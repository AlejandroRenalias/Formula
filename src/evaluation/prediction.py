"""Absolute-time samples conditional on the subject's actual dry stop plan."""
from dataclasses import dataclass

from src.calculators.projection import Stop, _quantile, _status, sample_scenarios, simulate_policy
from src.core.models import TireCompound, TrackStatus
from src.evaluation.snapshot import ExcludedSnapshot, at_time, crossings, number


@dataclass(frozen=True)
class ActualPlan:
    # Evaluation treatment, not a selectable causal policy. Unlike Policy,
    # this may have more than two stops (e.g. a late fastest-lap stop).
    dry_stops: tuple[Stop, ...]
    id: str = "actual_subject_plan"
    label: str = "Conditional actual subject plan"
    react_to_weather: bool = False

    @property
    def max_stops(self):
        return len(self.dry_stops)


def actual_plan(data, driver, cutoff, lap):
    """Outcome channel only: never called by the snapshot builder."""
    future = sorted((r for r in data["laps"] if r["Driver"] == driver
                     and number(r.get("PitInTime")) and r["PitInTime"] > cutoff),
                    key=lambda r: r["PitInTime"])
    stops = []
    for row in future:
        boundary = int(row["NumberOfLaps"]) - 1
        if boundary < lap:
            raise ExcludedSnapshot("pit_boundary_precedes_cutoff")
        exits = sorted((r["PitOutTime"] for r in data["laps"] if r["Driver"] == driver
                        and number(r.get("PitOutTime")) and r["PitOutTime"] > row["PitInTime"]))
        if not exits:
            raise ExcludedSnapshot("actual_stop_missing_exit")
        exit_time = exits[0]
        out_row = next(r for r in data["laps"] if r["Driver"] == driver
                       and r.get("PitOutTime") == exit_time)
        # Corrected tyre labels belong ONLY to the conditional outcome channel.
        # Provisional UNKNOWN announcements are not final actual-plan labels.
        labels = [r for r in data.get("actual_tyres", []) if r["DriverNumber"] == driver
                  and r["LapNumber"] == out_row["NumberOfLaps"]]
        known = {c.value for c in TireCompound}
        if labels:
            value = labels[-1]["Compound"]
        else:
            next_entry = next((r["PitInTime"] for r in future if r["PitInTime"] > exit_time), float("inf"))
            updates = [r for r in at_time(data["tyres"], next_entry, driver)
                       if r["Time"] >= row["PitInTime"] and r.get("Compound") in known]
            value = updates[0]["Compound"] if updates else None
        if value not in known:
            raise ExcludedSnapshot("actual_stop_missing_compound")
        compound = TireCompound(value)
        if compound in (TireCompound.INTERMEDIATE, TireCompound.WET):
            raise ExcludedSnapshot("actual_wet_plan_outside_slice")
        stops.append(Stop(lap=boundary, compound=compound))
    if len({s.lap for s in stops}) != len(stops):
        raise ExcludedSnapshot("multiple_stops_same_boundary")
    return ActualPlan(tuple(stops))


def predict(snapshot, plan):
    """No outcome observations here. Summaries of unchanged simulation draws."""
    state, config = snapshot.state, snapshot.config
    if any(s.lap < state.current_lap or s.lap >= state.total_laps for s in plan.dry_stops):
        raise ExcludedSnapshot("actual_plan_boundary_outside_projection")
    scenarios = sample_scenarios(state, config)
    traces = [simulate_policy(state, plan, s, config, fixed_schedule=True) for s in scenarios]
    weights = [s.weight for s in scenarios]
    # Summarise the exact same traces; never draw again or force a green rerun.
    first_neutral = [next((lap for lap in range(state.current_lap+1,state.total_laps+1)
                          if _status(state,lap,config,s) in (TrackStatus.SAFETY_CAR,TrackStatus.VSC)),
                         state.total_laps+1) for s in scenarios]
    result = {}
    for i in range(1,state.total_laps-state.current_lap+1):
        target=state.current_lap+i
        green=[j for j,first in enumerate(first_neutral) if first>target]
        values=[t.times[i] for t in traces]
        starts=[any(state.current_lap<start<=target for start,_,_ in s.neutralization_events)
                for s in scenarios]
        # Until the first new event, only the known ongoing schedule removes
        # eligible laps. Thus the marginal onset probability is exact; duration
        # draws after that first onset do not affect this event indicator.
        eligible=sum(_status(state,lap,config) not in (TrackStatus.SAFETY_CAR,TrackStatus.VSC)
                     for lap in range(state.current_lap+1,target+1))
        onset_probability=1-(1-config.future_sc_probability-config.future_vsc_probability)**eligible
        result[target]={
            "p10_s":_quantile(values,weights,.1),
            "median_s":_quantile(values,weights,.5),
            "p90_s":_quantile(values,weights,.9),
            "green_p10_s":_quantile([values[j] for j in green],[weights[j] for j in green],.1) if green else None,
            "green_median_s":_quantile([values[j] for j in green],[weights[j] for j in green],.5) if green else None,
            "green_p90_s":_quantile([values[j] for j in green],[weights[j] for j in green],.9) if green else None,
            "green_sample_count":len(green),
            "green_probability_mass":sum(weights[j] for j in green)/sum(weights),
            "neutralization_start_probability":onset_probability,
            "sampled_neutralization_start_probability":sum(w for w,start in zip(weights,starts) if start)/sum(weights)}
    return result



def score_targets(data, driver, snapshot, predictions):
    labels = crossings(data, driver)
    lap = snapshot.state.current_lap
    cutoff = snapshot.audit["cutoff_session_s"]
    finish = max(labels)
    rows, exclusions = [], []
    for horizon, target in (("1", lap + 1), ("5", lap + 5), ("10", lap + 10), ("finish", finish)):
        if target > finish or target not in labels or target not in predictions:
            exclusions.append({"driver": driver, "lap": lap, "horizon": horizon,
                               "reason": "target_beyond_finish_or_missing"})
            continue
        observed = labels[target] - cutoff
        if observed <= 0:
            exclusions.append({"driver": driver, "lap": lap, "horizon": horizon,
                               "reason": "invalid_actual_elapsed_time"})
            continue
        row = {"driver": snapshot.state.subject_driver.driver, "driver_number": driver,
               "lap": lap, "horizon": horizon, "target_lap": target,
               "horizon_laps": target - lap, "actual_s": observed, **predictions[target]}
        row["error_s"] = row["median_s"] - observed
        row["covered"] = row["p10_s"] <= observed <= row["p90_s"]
        row["width_s"] = row["p90_s"] - row["p10_s"]
        rows.append(row)
    return rows, exclusions
