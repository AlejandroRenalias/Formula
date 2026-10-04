"""Information-boundary and absolute conditional replay regression tests."""
from copy import deepcopy
import json
from pathlib import Path
import socket

import pytest

from src.calculators.projection import Scenario, Stop, simulate_policy
from src.core.models import TireCompound, TrackStatus
from src.evaluation.offline import network_blocked
from src.evaluation.prediction import ActualPlan, actual_plan, predict, score_targets
from src.evaluation.snapshot import (ExcludedSnapshot, build_snapshot, crossings,
                                      load_dataset, median_pace_anchor, clock)
from tools.evaluate_bahrain import metrics


def dataset():
    data = {"schema_version": 1, "year": 2021, "race": "Bahrain", "scheduled_laps": 56,
            "drivers": [{"DriverNumber": d, "Abbreviation": a, "TeamName": "Team"}
                        for d, a in (("1", "AAA"), ("2", "BBB"))],
            "results": [], "laps": [], "events": [], "tyres": [],
            "weather": [{"Time": 0., "TrackTemp": 30., "AirTemp": 20., "Humidity": 50.,
                         "Rainfall": False, "WindSpeed": 2.}],
            "track_status": [{"Time": 0., "Status": "1"}]}
    for d, offset in (("1", 0), ("2", 3)):
        data["tyres"].append({"Time": 0., "Driver": d, "Stint": 0,
                              "Compound": "MEDIUM", "StartLaps": 3.})
        data["events"].append({"Time": 0., "Driver": d, "Position": d, "InPit": False})
        for n in range(1, 57):
            time = n * 100. + offset
            data["laps"].append({"Time": time, "Driver": d, "NumberOfLaps": n,
                                 "LapTime": 100., "PitInTime": None, "PitOutTime": None})
            data["events"].append({"Time": time, "Driver": d, "NumberOfLaps": n,
                                   "LastLapTime": {"Value": "1:40.000"}})
    return data


def test_future_observations_and_proxy_row_fields_do_not_leak():
    data = dataset()
    expected = build_snapshot(data, "1", 8)
    changed = deepcopy(data)
    for key in ("events", "tyres", "weather", "track_status"):
        for row in changed[key]:
            if row["Time"] > 800:
                row.update(Position="1", Compound="WET", StartLaps=99,
                           LastLapTime={"Value": "0:01.000"}, Rainfall=True, Status="4")
    for row in changed["laps"]:
        if row["Time"] > 800:
            # The approved proxy is only Time. Poison every other value.
            row.update(LapTime=1., Compound="WET", TyreLife=999,
                       PitInTime=850., PitOutTime=860., Position=1)
    changed["results"] = [{"DriverNumber": "2", "Position": 1}]
    changed["actual_tyres"] = [{"DriverNumber": "1", "LapNumber": 8, "Compound": "WET"}]
    actual = build_snapshot(changed, "1", 8)
    assert actual == expected
    assert predict(actual, ActualPlan(())) == predict(expected, ActualPlan(()))
    proxy = next(r for r in actual.audit["gaps"] if r["driver"] == "2")
    assert proxy["after_cutoff_exception"] is True
    assert proxy["gap_s"] == -3


def test_truncated_raw_packets_match_full_replay_with_isolated_proxy():
    data = dataset()
    expected = build_snapshot(data, "1", 8)
    prefix = deepcopy(data)
    for key in ("events", "tyres", "weather", "track_status", "laps"):
        prefix[key] = [r for r in prefix[key] if r["Time"] <= 800]
    proxy = {"2": crossings(data, "2")[8]}
    # No future timing packet remains, yet permitted crossing proxy is retained.
    actual = build_snapshot(prefix, "1", 8, cutoff_s=800., gap_proxy=proxy)
    assert actual == expected


def test_only_same_lap_proxy_can_change_gap():
    data = dataset()
    expected = build_snapshot(data, "1", 8)
    for row in data["laps"]:
        if row["Driver"] == "2" and row["NumberOfLaps"] == 9:
            row["Time"] += 400
    assert build_snapshot(data, "1", 8) == expected
    next(r for r in data["laps"] if r["Driver"] == "2" and r["NumberOfLaps"] == 8)["Time"] += 2
    changed = build_snapshot(data, "1", 8)
    assert changed.state.competitors[0].gap_to_subject_s == -5
    assert changed.state.competitors[0].last_lap_time_s == expected.state.competitors[0].last_lap_time_s


def test_pit_stop_straddling_cutoff_is_excluded_without_future_tyres():
    data = dataset()
    data["events"] += [{"Time": 790., "Driver": "1", "InPit": True},
                       {"Time": 810., "Driver": "1", "InPit": False}]
    data["tyres"].append({"Time": 805., "Driver": "1", "Stint": 1,
                           "Compound": "HARD", "StartLaps": 0.})
    with pytest.raises(ExcludedSnapshot, match="subject_stop_straddles_cutoff"):
        build_snapshot(data, "1", 8)


def test_rival_in_pit_is_known_but_future_exit_and_compound_are_not():
    data = dataset()
    data["events"] += [{"Time": 790., "Driver": "2", "InPit": True},
                       {"Time": 810., "Driver": "2", "InPit": False}]
    data["tyres"].append({"Time": 805., "Driver": "2", "Stint": 1,
                           "Compound": "HARD", "StartLaps": 0.})
    rival = build_snapshot(data, "1", 8).state.competitors[0]
    assert rival.is_in_pit
    assert rival.pit_stop_count == 1
    assert rival.current_compound == TireCompound.MEDIUM


def test_pre_race_pit_visits_do_not_count_and_old_stint_updates_are_not_used_compounds():
    data = dataset()
    data["session_start_s"] = 50.
    data["events"] += [{"Time": 10., "Driver": "1", "InPit": True},
                       {"Time": 20., "Driver": "1", "InPit": False}]
    data["tyres"] += [{"Time": 1., "Driver": "1", "Stint": -1,
                       "Compound": "HARD", "StartLaps": 0.}]
    snap = build_snapshot(data, "1", 8)
    assert snap.state.subject_driver.total_pit_stops == 0
    assert snap.state.subject_driver.used_compounds == [TireCompound.MEDIUM]


def test_frozen_parameters_and_source_timestamps(monkeypatch):
    from src.calculators.pace_model import PaceModel
    def forbidden(*args, **kwargs):
        raise AssertionError("Parameter fitting is forbidden")
    monkeypatch.setattr(PaceModel, "calculate_pace_metrics", forbidden)
    snap = build_snapshot(dataset(), "1", 8)
    assert snap.config.degradation_scale == 1
    assert snap.state.pit_loss.green_pit_loss_s == snap.audit["pit_loss_estimate"]["green_total_loss_s"]
    assert snap.config.pit_in_lap_fraction == snap.audit["pit_loss_estimate"]["in_lap_fraction"]
    assert all(t <= 800 for t in snap.audit["parameter_source_session_s"].values())
    assert snap.state.subject_driver.stint_length_laps == 11  # used tyres: 3 + 8
    assert snap.audit["subject_completed_stint_laps"] == 8
    predict(snap, ActualPlan(()))


def test_median_anchor_resists_single_fast_outlier_and_preserves_corrections():
    from src.core.models import LapObservation
    from src.calculators.tyre_model import TyreModel
    clean = [LapObservation(lap_number=n, lap_time_s=t, compound=TireCompound.MEDIUM,
             tyre_age_laps=n, timestamp=clock(n*100))
             for n,t in enumerate((90.,100.,101.,102.,103.,104.), 1)]
    base, observed, middle = median_pace_anchor(clean, 8)
    assert observed == 101.5
    assert [r.lap_number for r in middle] == [3,4]
    expected = sum(r.lap_time_s - TyreModel.lap_delta_s(r.compound,r.tyre_age_laps)
                   - .05*(8-r.lap_number) for r in middle)/2
    assert base == pytest.approx(expected)
    assert median_pace_anchor(clean[:1], 8)[0] == pytest.approx(
        90 - TyreModel.lap_delta_s(TireCompound.MEDIUM,1) - .05*7)


def test_future_weather_and_track_events_ignored():
    data = dataset()
    before = build_snapshot(data, "1", 8)
    data["weather"].append({"Time": 801., "Rainfall": True})
    data["track_status"].append({"Time": 801., "Status": "4"})
    assert build_snapshot(data, "1", 8) == before


def test_absolute_prediction_matches_direct_engine_samples():
    snap = build_snapshot(dataset(), "1", 8)
    plan = ActualPlan(())
    result = predict(snap, plan)
    trace = simulate_policy(snap.state, plan, Scenario(None, 0, 1), snap.config,
                            fixed_schedule=True)
    assert result[9]["median_s"] > 90  # absolute elapsed, not relative plan delta
    assert result[9]["p10_s"] <= trace.times[1] <= result[9]["p90_s"]
    assert result[9]["p10_s"] <= result[9]["median_s"] <= result[9]["p90_s"]


def test_fixed_treatment_suppresses_autonomous_sc_subject_stop():
    snap = build_snapshot(dataset(), "1", 8)
    state = snap.state.model_copy(update={"track_status": TrackStatus.SAFETY_CAR})
    plan = ActualPlan((Stop(lap=30, compound=TireCompound.HARD),))
    trace = simulate_policy(state, plan, Scenario(None, 0, 1), snap.config,
                            fixed_schedule=True)
    assert [s["lap"] for s in trace.stops] == [30]


def test_three_stops_and_same_compound_treatment_are_supported():
    snap = build_snapshot(dataset(), "1", 8)
    plan = ActualPlan(tuple(Stop(lap=n, compound=TireCompound.MEDIUM) for n in (10, 20, 30)))
    trace = simulate_policy(snap.state, plan, Scenario(None, 0, 1), snap.config,
                            fixed_schedule=True)
    assert [s["lap"] for s in trace.stops] == [10, 20, 30]
    assert predict(snap, plan)[18]["median_s"] != predict(snap, ActualPlan(()))[18]["median_s"]


def test_actual_plan_is_separate_and_charged_on_pit_in_lap():
    data = dataset()
    before = build_snapshot(data, "1", 8)
    entry = next(r for r in data["laps"] if r["Driver"] == "1" and r["NumberOfLaps"] == 10)
    entry["PitInTime"] = 990.
    out = next(r for r in data["laps"] if r["Driver"] == "1" and r["NumberOfLaps"] == 11)
    out["PitOutTime"] = 1010.
    data["tyres"].append({"Time": 1005., "Driver": "1", "Stint": 1,
                           "Compound": "HARD", "StartLaps": 0.})
    plan = actual_plan(data, "1", 800., 8)
    assert plan.dry_stops == (Stop(lap=9, compound=TireCompound.HARD),)
    assert build_snapshot(data, "1", 8) == before
    assert predict(before, plan)[10]["median_s"] != predict(before, ActualPlan(()))[10]["median_s"]


def test_actual_plan_uses_outcome_labels_not_provisional_unknown_announcements():
    data = dataset()
    next(r for r in data["laps"] if r["Driver"] == "1" and r["NumberOfLaps"] == 10)["PitInTime"] = 990.
    next(r for r in data["laps"] if r["Driver"] == "1" and r["NumberOfLaps"] == 11)["PitOutTime"] = 1010.
    data["tyres"].append({"Time": 1005., "Driver": "1", "Stint": 1,
                           "Compound": "UNKNOWN", "StartLaps": 0.})
    data["actual_tyres"] = [{"DriverNumber": "1", "LapNumber": 11, "Compound": "HARD"}]
    before = build_snapshot(data, "1", 8)
    assert actual_plan(data, "1", 800., 8).dry_stops[0].compound == TireCompound.HARD
    data["actual_tyres"][0]["Compound"] = "SOFT"
    assert build_snapshot(data, "1", 8) == before
    assert actual_plan(data, "1", 800., 8).dry_stops[0].compound == TireCompound.SOFT


def test_horizon_beyond_finish_counted_and_actual_includes_pit_elapsed():
    data = dataset()
    snap = build_snapshot(data, "1", 51)
    rows, exclusions = score_targets(data, "1", snap, predict(snap, ActualPlan(())))
    assert {r["horizon"] for r in rows} == {"1", "5", "finish"}
    assert exclusions[0]["horizon"] == "10"
    assert next(r for r in rows if r["horizon"] == "finish")["actual_s"] == 500


def test_metrics_sign_inclusive_coverage_and_width():
    rows = [{"horizon": "1", "horizon_laps": 1, "contains_subject_pit_stop": False,
             "error_s": -2., "actual_s": 10., "p10_s": 8., "p90_s": 10.,
             "covered": True, "width_s": 2.},
            {"horizon": "1", "horizon_laps": 1, "contains_subject_pit_stop": True,
             "error_s": 4., "actual_s": 2., "p10_s": 5., "p90_s": 7.,
             "covered": False, "width_s": 2.}]
    m = metrics(rows)["1"]
    assert m["mae_s"] == 3
    assert m["bias_s"] == 1
    assert m["coverage"] == .5
    assert m["mean_width_s"] == 2
    assert m["lower_misses"] == 1
    assert m["median_error_s"] == 1
    assert m["by_subject_pit_stop"]["without_stop"]["bias_s"] == -2
    assert m["by_subject_pit_stop"]["with_stop"]["bias_s"] == 4


def test_error_per_lap_aggregates_per_prediction_not_ratio_of_means():
    rows = [{"horizon": "finish", "horizon_laps": laps, "contains_subject_pit_stop": False,
             "error_s": error, "actual_s": 10., "p10_s": 8., "p90_s": 10.,
             "covered": True, "width_s": 2.} for laps, error in ((2, -4.), (10, -10.))]
    m = metrics(rows)["finish"]
    assert m["mean_error_per_lap_s"] == -1.5
    assert m["median_error_per_lap_s"] == -1.5
    assert m["by_subject_pit_stop"]["with_stop"] == {"n": 0}


def test_pit_stop_diagnostics_use_actual_entry_inside_horizon_only():
    from src.evaluation.diagnostics import enrich_rows
    data = dataset()
    next(r for r in data["laps"] if r["Driver"] == "1" and r["NumberOfLaps"] == 10)["PitInTime"] = 990.
    rows = [{"driver_number": "1", "lap": 8, "target_lap": target,
             "horizon_laps": target-8, "error_s": -2.} for target in (9, 10)]
    enriched = enrich_rows(data, rows)
    assert [r["contains_subject_pit_stop"] for r in enriched] == [False, True]
    assert enriched[1]["error_per_lap_s"] == -1


def test_network_blocked_prediction_and_no_fallback_download():
    with network_blocked():
        with pytest.raises(RuntimeError, match="offline"):
            socket.create_connection(("example.com", 443))
        predict(build_snapshot(dataset(), "1", 8), ActualPlan(()))
        with pytest.raises(FileNotFoundError):
            load_dataset(Path("missing-evaluation-dataset.json"))


def test_cache_integrity_and_bahrain_guard(tmp_path):
    import hashlib
    path = tmp_path / "session.json"
    path.write_text(json.dumps({"schema_version": 1, "year": 2024, "race": "Bahrain"}))
    path.with_suffix(".sha256").write_text(hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError, match="Approved development races only"):
        load_dataset(path)
    path.write_text("{}")
    with pytest.raises(ValueError, match="hash mismatch"):
        load_dataset(path)


@pytest.mark.skipif(not Path("data/cache/evaluation/bahrain_2021/session.json").exists(),
                    reason="Real Bahrain cache is optional; CI never downloads")
def test_real_cache_prefix_replay_and_future_packet_mutation():
    with network_blocked():
        data, _ = load_dataset("data/cache/evaluation/bahrain_2021/session.json")
        for driver, lap in (("44", 18), ("11", 25), ("22", 40)):
            before = build_snapshot(data, driver, lap)
            cutoff = before.audit["cutoff_session_s"]
            prefix = deepcopy(data)
            for key in ("events", "tyres", "weather", "track_status", "laps"):
                prefix[key] = [r for r in prefix[key] if r["Time"] <= cutoff]
            proxy = {d["DriverNumber"]: crossings(data, d["DriverNumber"]).get(lap)
                     for d in data["drivers"] if d["DriverNumber"] != driver}
            assert build_snapshot(prefix, driver, lap, cutoff_s=cutoff, gap_proxy=proxy) == before
            changed = deepcopy(data)
            for key in ("events", "tyres", "weather", "track_status"):
                changed[key] = [r for r in changed[key] if r["Time"] <= cutoff]
            assert build_snapshot(changed, driver, lap) == before
            predict(before, actual_plan(data, driver, cutoff, lap))


def test_pace_uncertainty_uses_driver_local_normalized_pre_cutoff_scatter():
    import statistics
    from src.evaluation.snapshot import pace_uncertainty, EPOCH
    from src.calculators.tyre_model import TyreModel
    from src.calculators.pace_model import PaceModel
    snapshot = build_snapshot(dataset(), "1", 8)
    clean = PaceModel.filter_clean_laps(snapshot.state.lap_history)[-6:]
    expected = [r.lap_time_s-TyreModel.lap_delta_s(r.compound,r.tyre_age_laps)
                -.05*(8-r.lap_number) for r in clean]
    u = snapshot.audit["pace_uncertainty"]
    scatter = statistics.stdev(expected)
    assert u["normalized_pace_samples_s"] == pytest.approx(expected)
    assert snapshot.config.lap_noise_sigma_s == pytest.approx(scatter)
    assert snapshot.config.base_pace_sigma_s == pytest.approx(scatter/len(clean)**.5)
    assert u["source_session_s"] <= snapshot.audit["cutoff_session_s"]
    assert pace_uncertainty(clean[:1],8)["lap_noise_sigma_s"] == 0


def test_other_driver_pace_cannot_size_subject_uncertainty():
    data = dataset()
    expected = build_snapshot(data,"1",8)
    for row in data["events"]:
        if row["Driver"] == "2" and row["Time"] <= 800 and "LastLapTime" in row:
            row["LastLapTime"] = {"Value": "1:20.000"}
    actual = build_snapshot(data,"1",8)
    assert actual.audit["pace_uncertainty"] == expected.audit["pace_uncertainty"]
    assert actual.config == expected.config


@pytest.mark.parametrize("year,race",[(2023,"Spain"),(2024,"Bahrain"),(2021,"Russia"),(2023,"Netherlands"),(2024,"Canada")])
def test_held_out_and_wet_races_are_denied_before_evaluation(year,race,tmp_path):
    import hashlib
    data=dataset();data.update(year=year,race=race)
    p=tmp_path/"session.json";p.write_text(json.dumps(data))
    p.with_suffix(".sha256").write_text(hashlib.sha256(p.read_bytes()).hexdigest())
    with pytest.raises(ValueError,match="Approved development races only"):
        load_dataset(p)


def test_no_stop_tyre_groups_keep_row_normalized_errors_and_drop_pit_rows():
    from src.evaluation.breakdown import no_stop_breakdowns,age_bucket
    assert [age_bucket(n) for n in (0,9,10,19,20,29,30)] == ["0-9","0-9","10-19","10-19","20-29","20-29","30+"]
    rows=[{"horizon":"finish","horizon_laps":h,"error_s":e,"contains_subject_pit_stop":pit,
           "actual_s":100.,"p10_s":90.,"p90_s":110.,"width_s":20.,"covered":True,
           "cutoff_tyre_age_laps":12,"cutoff_compound":"HARD","cutoff_track_status":"GREEN"}
          for h,e,pit in ((2,-4.,False),(10,-10.,False),(1,999.,True))]
    groups=no_stop_breakdowns(rows)
    assert len(groups)==4
    assert all(r["n"]==2 and r["mean_error_per_lap_s"]==-1.5 for r in groups)


@pytest.mark.parametrize("race,driver,lap",[("spain_2022","1",22),("spain_2022","44",40),("france_2022","1",25),("france_2022","63",19),("france_2022","55",40)])
def test_development_race_prefix_and_future_poisoning(race,driver,lap):
    path=Path("data/cache/evaluation")/race/"session.json"
    if not path.exists(): pytest.skip("Local real cache optional; tests never download")
    with network_blocked():
        data,_=load_dataset(path);before=build_snapshot(data,driver,lap);cutoff=before.audit["cutoff_session_s"]
        prefix=deepcopy(data)
        for key in ("events","tyres","weather","track_status","laps"):
            prefix[key]=[r for r in prefix[key] if r["Time"]<=cutoff]
        proxy={d["DriverNumber"]:crossings(data,d["DriverNumber"]).get(lap)
               for d in data["drivers"] if d["DriverNumber"]!=driver}
        assert build_snapshot(prefix,driver,lap,cutoff_s=cutoff,gap_proxy=proxy)==before
        changed=deepcopy(data)
        for key in ("events","tyres","weather","track_status"):
            for r in changed[key]:
                if r["Time"]>cutoff:r.update(Position="1",Compound="WET",StartLaps=999,LastLapTime={"Value":"0:01.000"},Rainfall=True,Status="4")
        for r in changed["laps"]:
            if r["Time"]>cutoff:r.update(LapTime=1.,PitInTime=cutoff+1.,PitOutTime=cutoff+2.)
        assert build_snapshot(changed,driver,lap)==before
        assert all(t<=cutoff for t in before.audit["parameter_source_session_s"].values())
