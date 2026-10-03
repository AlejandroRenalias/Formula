"""Absolute-time samples conditional on the subject's actual dry stop plan."""
from dataclasses import dataclass

from src.calculators.projection import Stop, _quantile, sample_scenarios, simulate_policy
from src.core.models import TireCompound
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
    """No outcome observations here. Existing weather/pit/wear draws only."""
    state, config = snapshot.state, snapshot.config
    if any(s.lap < state.current_lap or s.lap >= state.total_laps for s in plan.dry_stops):
        raise ExcludedSnapshot("actual_plan_boundary_outside_projection")
    scenarios = sample_scenarios(state, config)
    traces = [simulate_policy(state, plan, s, config, fixed_schedule=True) for s in scenarios]
    weights = [s.weight for s in scenarios]
    return {state.current_lap + i: {
        "p10_s": _quantile([t.times[i] for t in traces], weights, .1),
        "median_s": _quantile([t.times[i] for t in traces], weights, .5),
        "p90_s": _quantile([t.times[i] for t in traces], weights, .9)}
        for i in range(1, state.total_laps - state.current_lap + 1)}


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
