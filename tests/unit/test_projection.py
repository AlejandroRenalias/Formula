"""Physical, policy, uncertainty, and information-boundary sanity cases."""
import json
from datetime import timedelta

import pytest

from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.calculators.projection import Policy, Stop, Scenario, ProjectionConfig, project, simulate_policy, _snapshot
from src.calculators.tyre_model import TyreModel
from src.core.models import TireCompound
from src.orchestrator.projection_pipeline import run_projection_cycle


def state(probability=0, eta=4):
    return SyntheticRaceAdapter.create_race_state(current_lap=18, total_laps=52,
        stint_length_laps=17, rain_probability=probability, rain_arrival_laps=eta,
        rain_intensity="LIGHT", competitors=[])


def cfg(**updates):
    return ProjectionConfig(samples_per_weather_branch=4, pit_loss_spread_s=0,
        rain_eta_spread_laps=0, **updates)


def plans(stop_lap=26):
    return (Policy(id="box", label="Box HARD now", dry_stops=(Stop(lap=18, compound=TireCompound.HARD),)),
            Policy(id="wait", label="Wait, then HARD if dry", dry_stops=(Stop(lap=stop_lap, compound=TireCompound.HARD),)))


def by_id(result, pid):
    return next(p for p in result["plans"] if p["id"] == pid)


def test_stop_lap_charges_pit_loss():
    s = state()
    config = cfg(degradation_scale=0, cliff_rate_s=0, fuel_effect_s_per_lap=0)
    snapshot = _snapshot(s, config)
    same_compound = Policy(id="stop", label="Same compound", react_to_weather=False,
                          dry_stops=(Stop(lap=18, compound=TireCompound.MEDIUM),))
    stay = Policy(id="stay", label="Stay", react_to_weather=False)
    a = simulate_policy(snapshot, same_compound, Scenario(None, 0, 1), config)
    b = simulate_policy(snapshot, stay, Scenario(None, 0, 1), config)
    assert a.times[1] - b.times[1] == pytest.approx(21.5)
    assert a.stops[0]["lap"] == 18 and a.stops[0]["charged_on_lap"] == 19


def test_older_tyres_are_slower():
    assert TyreModel.lap_delta_s(TireCompound.MEDIUM, 20) > TyreModel.lap_delta_s(TireCompound.MEDIUM, 5)


def test_zero_rain_probability_ignores_eta_and_weather_costs():
    baseline = project(state(), plans(), cfg(), include_flips=False)
    changed = project(state(eta=1), plans(), cfg(slick_wet_penalty_s=500, inter_dry_penalty_s=100), include_flips=False)
    assert changed["ranking"] == baseline["ranking"]
    assert [p["mean_time_to_finish_s"] for p in changed["plans"]] == [p["mean_time_to_finish_s"] for p in baseline["plans"]]


def test_certain_rain_in_two_laps_prefers_waiting_over_slick_stop():
    result = project(state(1, 2), plans(), cfg(), include_flips=False)
    assert result["recommended"] == "wait"
    assert len(by_id(result, "box")["stops"]) == 2
    assert len(by_id(result, "wait")["stops"]) == 1
    assert by_id(result, "wait")["stops"][0]["compound"] == "INTERMEDIATE"


def test_preemptive_inters_pay_dry_running_cost():
    assert TyreModel.get_compound_specs(TireCompound.INTERMEDIATE).base_pace_delta_s > 0
    from src.calculators.weather_model import WeatherModel
    assert WeatherModel.projection_penalty_s(TireCompound.INTERMEDIATE, 0, "LIGHT") == 8
    assert WeatherModel.projection_penalty_s(TireCompound.INTERMEDIATE, 1, "LIGHT") == 0


def test_higher_pit_loss_never_improves_extra_stop_relative_time():
    policies = (plans()[0], Policy(id="two", label="Two stops", react_to_weather=False,
                dry_stops=(Stop(lap=18, compound=TireCompound.HARD), Stop(lap=36, compound=TireCompound.MEDIUM))))
    margins = []
    for loss in (5, 10, 21.5, 40):
        s = state()
        s.pit_loss = s.pit_loss.model_copy(update={"green_pit_loss_s": loss})
        result = project(s, policies, cfg(), include_flips=False)
        margins.append(by_id(result, "two")["mean_time_to_finish_s"] - by_id(result, "box")["mean_time_to_finish_s"])
    assert margins == sorted(margins)
    assert margins[-1] - margins[0] == pytest.approx(35)


def test_normal_dry_degradation_prefers_sensible_one_stop_to_two():
    policies = (Policy(id="one", label="One stop", dry_stops=(Stop(lap=22, compound=TireCompound.HARD),)),
                Policy(id="two", label="Two stops", dry_stops=(Stop(lap=22, compound=TireCompound.HARD),
                                                            Stop(lap=38, compound=TireCompound.MEDIUM))))
    result = project(state(), policies, cfg(degradation_scale=1), include_flips=False)
    assert result["recommended"] == "one"


def test_future_laps_and_derived_metrics_do_not_leak():
    s = state(.7)
    expected = project(s, config=cfg(), include_flips=False)
    future = s.lap_history[-1].model_copy(update={"lap_number": 19, "lap_time_s": 1,
                                                "timestamp": s.knowledge_cutoff + timedelta(seconds=1)})
    contaminated = s.model_copy(deep=True)
    contaminated.lap_history += [future, future.model_copy(update={"lap_number": 18})]
    contaminated.derived_pace.degradation_rate_s_per_lap.value = 99
    assert project(contaminated, config=cfg(), include_flips=False) == expected
    assert s.lap_history == state(.7).lap_history


def test_same_seed_and_policy_order_use_shared_scenarios():
    config = ProjectionConfig(samples_per_weather_branch=8)
    a = project(state(.7), plans(), config, include_flips=False)
    assert a == project(state(.7), plans(), config, include_flips=False)
    b = project(state(.7), tuple(reversed(plans())), config, include_flips=False)
    for pid in ("box", "wait"):
        assert by_id(a, pid)["scenario_stops"] == by_id(b, pid)["scenario_stops"]
        assert by_id(a, pid)["mean_time_to_finish_s"] == by_id(b, pid)["mean_time_to_finish_s"]
    assert a["recommended"] == b["recommended"]
    for p in a["plans"]:
        assert all(low <= middle <= high for low, middle, high in zip(p["p10"], p["median"], p["p90"]))
        assert len(p["laps"]) == len(p["median"]) == 35
        assert p["laps"][0] == 18 and p["laps"][-1] == 52
    json.dumps(a, allow_nan=False)


def test_finish_compound_constraint_and_wet_exemption():
    policies = (Policy(id="illegal", label="Keep medium", react_to_weather=False), plans()[0])
    result = project(state(), policies, cfg(), include_flips=False)
    assert by_id(result, "illegal")["invalid_probability"] == 1
    assert result["ranking"] == ["box"]
    assert result["plan_margin_s"] is None
    assert result["call_margin_s"] is None
    assert result["call_win_rate"] is None
    with pytest.raises(ValueError, match="compound-compliant"):
        project(state(), policies[:1], cfg(), include_flips=False)
    wet = state(1, 2)
    assert project(wet, (Policy(id="wet", label="Wait for inters"),), cfg(), include_flips=False)["ranking"] == ["wet"]


def test_projection_owns_recommendation_and_exposes_scorer_disagreement():
    s = state(1, 2)
    result = run_projection_cycle(s, cfg(), plans())
    assert result["recommended"] == "wait"
    assert result["disagreement"]["disagrees"]
    assert result["disagreement"]["scorer_action"] == "BOX_NOW"
    assert "score_margin" in result["scorer"]


def test_pit_loss_flip_on_toy_has_known_boundary():
    s = state()
    policies = (Policy(id="one", label="One stop", react_to_weather=False,
                       dry_stops=(Stop(lap=18, compound=TireCompound.HARD),)),
                Policy(id="two", label="Extra fresh set", react_to_weather=False,
                       dry_stops=(Stop(lap=18, compound=TireCompound.HARD), Stop(lap=36, compound=TireCompound.HARD))))
    config = cfg(degradation_scale=1, cliff_rate_s=0, fuel_effect_s_per_lap=0,
                 rain_sweep_offsets=(), safety_car_sweep_offsets=(), pit_loss_sweep_s=(10, 11, 12, 13, 14))
    # Resetting HARD age after 18 laps saves 18 * 0.04 * 16 = 11.52s.
    result = project(s, policies, config)
    flip = next(f for f in result["policy_flip_thresholds"] if f["assumption"] == "pit_loss_s")
    assert {v["value"]: v["recommended"] for v in flip["sweep"]}[11] == "two"
    assert {v["value"]: v["recommended"] for v in flip["sweep"]}[12] == "one"
    assert flip["transitions"][0]["from_value"] == 11
    assert flip["transitions"][0]["to_value"] == 12
    call_flip = next(f for f in result["flip_thresholds"] if f["assumption"] == "pit_loss_s")
    assert call_flip["status"] == "no flip in range"
    assert call_flip["transitions"] == []  # Both policies BOX now.


def test_bad_policies_and_invalid_cutoff_rejected():
    with pytest.raises(ValueError):
        Policy(id="bad", label="bad", dry_stops=(Stop(lap=22, compound=TireCompound.HARD),
                                                  Stop(lap=20, compound=TireCompound.MEDIUM)))
    s = state()
    s.timestamp += timedelta(seconds=1)
    with pytest.raises(ValueError, match="timestamp"):
        project(s, config=cfg())


def test_no_flip_in_range_and_finish_at_cutoff_origin():
    config = cfg(degradation_scale=0, cliff_rate_s=0, rain_sweep_offsets=(1, 2, 4),
                 pit_loss_sweep_s=(10, 20, 30), safety_car_sweep_offsets=())
    result = project(state(), plans(), config)
    flip = next(f for f in result["flip_thresholds"] if f["assumption"] == "rain_arrival_lap")
    assert flip["status"] == "no flip in range"
    assert flip["flips_at"] is None and flip["flips_to"] is None
    assert all(p["median"][0] == p["p10"][0] == p["p90"][0] == 0 for p in result["plans"])


def test_probability_weighting_is_exact_and_policy_stops_are_bounded():
    result = project(state(.7), config=ProjectionConfig(samples_per_weather_branch=8), include_flips=False)
    for plan in result["plans"]:
        branches = plan["scenario_stops"]
        assert sum(s["weight"] for s in branches if s["rain_lap"] is not None) == pytest.approx(.7)
        assert sum(s["weight"] for s in branches if s["rain_lap"] is None) == pytest.approx(.3)
        assert all(len(s["stops"]) <= 2 for s in branches)


def test_pit_loss_moves_projected_position_without_a_score_bonus():
    s = SyntheticRaceAdapter.create_race_state(current_lap=18, total_laps=52, stint_length_laps=17)
    result = project(s, plans(), cfg(), include_flips=False)
    assert by_id(result, "box")["median_position"][1] == 3
    assert by_id(result, "wait")["median_position"][1] == 1


def test_same_compound_stops_do_not_satisfy_finish_constraint():
    policy = Policy(id="medium", label="Another medium", react_to_weather=False,
                    dry_stops=(Stop(lap=18, compound=TireCompound.MEDIUM),))
    with pytest.raises(ValueError, match="compound-compliant"):
        project(state(), (policy,), cfg(), include_flips=False)


def test_compound_disagreement_is_exposed_even_when_both_box():
    policy = Policy(id="soft", label="BOX SOFT", react_to_weather=False,
                    dry_stops=(Stop(lap=18, compound=TireCompound.SOFT),))
    result = run_projection_cycle(state(), cfg(rain_sweep_offsets=(),
                                              pit_loss_sweep_s=(), safety_car_sweep_offsets=()), (policy,))
    disagreement = result["disagreement"]
    assert disagreement["scorer_action"] == disagreement["projection_action"] == "BOX_NOW"
    assert disagreement["projection_compound"] == "SOFT"
    assert disagreement["disagrees"] and disagreement["disagreement_probability"] == 1


def test_committed_fixture_reproduces_from_its_source_inputs():
    from pathlib import Path
    from src.core.models import RaceState
    saved = json.loads((Path(__file__).resolve().parents[1] / "fixtures" / "projection_lap18.json").read_text(encoding="utf-8"))
    source = saved.pop("fixture")
    result = run_projection_cycle(RaceState.model_validate(source["state"]),
                                  ProjectionConfig.model_validate(source["config"]))
    from src.ui.projection_fixture import build_projection_view
    from src.adapters.scenarios import TrackScenarioConfig
    from src.calculators.circuit_map import build_cutoff_track
    result['track'] = build_cutoff_track(RaceState.model_validate(source['state']),
                                       TrackScenarioConfig.model_validate(source['track_config']))
    result['ui'] = build_projection_view(result, RaceState.model_validate(source['state']))
    # The previous uncertainty slice added disabled-by-default config fields.
    # Check their values explicitly, then compare the original fixture contract
    # without modifying its UI artifact or accepting numeric projection drift.
    added = {"base_pace_sigma_s", "lap_noise_sigma_s"}
    assert {r["name"]: r["value"] for r in result["assumptions"] if r["name"] in added} == {
        name: 0.0 for name in added}
    result["assumptions"] = [r for r in result["assumptions"] if r["name"] not in added]
    result["ui"]["display"]["assumptions"] = [
        r for r in result["ui"]["display"]["assumptions"]
        if r["name"] not in {name.replace("_", " ") for name in added}]
    assert result == saved


def test_call_compares_action_groups_instead_of_runner_up_policy():
    result = project(state(.7), config=cfg(), include_flips=False)
    best = result["best_policies_by_call"]
    assert result["call"] == "STAY_OUT"
    assert best["STAY_OUT"] == result["recommended"]
    assert by_id(result, best["BOX_NOW"])["policy"]["dry_stops"][0]["lap"] == 18
    difference = by_id(result, best["BOX_NOW"])["mean_time_to_finish_s"] - by_id(result, best["STAY_OUT"])["mean_time_to_finish_s"]
    assert result["call_margin_s"] == pytest.approx(difference, abs=.0001)
    assert result["call_margin_s"] > result["plan_margin_s"]
    assert "margin_s" not in result


def test_win_rate_uses_paired_probability_mass_not_winning_call_frequency():
    config = cfg(call_tolerance_s=0, degradation_spread_fraction=0)
    result = project(state(.7, 12), plans(), config, include_flips=False)
    assert result["call"] == "BOX_NOW"
    assert result["call_win_rate"] == pytest.approx(.3)  # STAY wins dry; BOX wins rain.
    bands = result["call_comparison"]
    assert bands["stay_policy_id"] == "wait" and bands["box_policy_id"] == "box"
    assert bands["p10"][-1] < 0 < bands["p90"][-1]
    assert bands["median"] == by_id(result, "wait")["median"]
    assert bands["p10"] == by_id(result, "wait")["p10"]
    assert bands["p90"] == by_id(result, "wait")["p90"]
    reordered = project(state(.7, 12), tuple(reversed(plans())), config, include_flips=False)
    assert reordered["call_comparison"] == bands
    assert reordered["call_win_rate"] == result["call_win_rate"]


def test_probability_sweep_finds_call_flip_and_arrival_includes_no_rain():
    result = project(state(.7, 12), plans(), cfg())
    probability = next(f for f in result["flip_thresholds"] if f["assumption"] == "rain_probability")
    assert probability["range"] == [0, 1] and probability["resolution"] == .1
    assert probability["transitions"] == [{"from_value": 0, "to_value": .1,
                                           "from_call": "STAY_OUT", "to_call": "BOX_NOW"}]
    arrival = next(f for f in result["flip_thresholds"] if f["assumption"] == "rain_arrival_lap")
    assert arrival["range"] == [19, 52] and arrival["resolution"] == 1
    assert arrival["includes_no_rain"]
    assert arrival["sweep"][-1]["value"] == "no rain"
    assert arrival["sweep"][-1]["call"] == "STAY_OUT"


def test_representative_scenarios_preserve_specific_stop_laps_and_times():
    s, config = state(.7), cfg()
    result = project(s, plans(), config, include_flips=False)
    representatives = {item["id"]: item for item in result["scenarios"]}
    wet, dry = representatives["rain_at_eta"], representatives["stays_dry"]
    assert wet["probability"] == .7 and dry["probability"] == pytest.approx(.3)
    assert wet["rain_lap"] == 22 and dry["rain_lap"] is None
    for scenario in representatives.values():
        assert {p["policy_id"] for p in scenario["plans"]} == {"box", "wait"}
        for plan in scenario["plans"]:
            assert plan["laps"] == list(range(18, 53))
            assert plan["cumulative_time"][0] == 0
            assert len(plan["cumulative_time"]) == len(plan["laps"])
            assert plan["finish_legal"]
            policy = next(p for p in plans() if p.id == plan["policy_id"])
            trace = simulate_policy(_snapshot(s, config), policy, Scenario(scenario["rain_lap"], 0, 1), config)
            assert plan["cumulative_time"] == trace.times
    assert [s["lap"] for s in next(p for p in wet["plans"] if p["policy_id"] == "wait")["stops"]] == [22]
    assert [s["lap"] for s in next(p for p in dry["plans"] if p["policy_id"] == "wait")["stops"]] == [26]


def test_sampled_future_rain_cannot_change_the_committed_cutoff_action():
    result = project(state(1, 1), plans(), cfg(), include_flips=False)
    assert result["best_policies_by_call"] == {"STAY_OUT": "wait", "BOX_NOW": "box"}
    for branch in by_id(result, "wait")["scenario_stops"]:
        assert all(s["lap"] > 18 for s in branch["stops"])
    assert all(branch["stops"][0]["lap"] == 18 for branch in by_id(result, "box")["scenario_stops"])


def test_missing_eta_does_not_invent_a_probability_sweep_or_rain_chart():
    s = state()
    s.weather_forecast.expected_arrival_laps.value = None
    result = project(s, plans(), cfg())
    flip = next(f for f in result["flip_thresholds"] if f["assumption"] == "rain_probability")
    assert flip["status"] == "unavailable: rain ETA missing"
    assert flip["sweep"] == []
    assert [s["id"] for s in result["scenarios"]] == ["stays_dry"]
    with pytest.raises(ValueError, match="probability sweep"):
        cfg(rain_probability_sweep=(1.1,))


def test_safety_car_opportunity_advances_stop_without_double_stopping():
    result = project(state(), plans(), cfg(safety_car_lap=19,
                         degradation_spread_fraction=0), include_flips=False)
    assert result["call"] == "STAY_OUT"
    box, wait = by_id(result, "box"), by_id(result, "wait")
    assert box["stops"][0]["pit_loss_s"] == 21.5  # Before SC is observed.
    assert len(wait["stops"]) == 1
    assert wait["stops"][0]["lap"] == 19
    assert wait["stops"][0]["pit_loss_s"] == 9.5
    assert wait["stops"][0]["reason"] == "safety_car_opportunity"
    expensive_sc = state()
    expensive_sc.pit_loss.sc_pit_loss_s = 30
    no_benefit = project(expensive_sc, plans(), cfg(safety_car_lap=19,
                               degradation_spread_fraction=0), include_flips=False)
    assert by_id(no_benefit, "wait")["stops"][0]["lap"] == 26


def test_box_policy_can_take_opportunistic_inters_under_sc():
    result = project(state(1), plans(), cfg(safety_car_lap=20,
                         degradation_spread_fraction=0), include_flips=False)
    stops = by_id(result, "box")["stops"]
    assert stops[0]["pit_loss_s"] == 21.5
    assert stops[1]["compound"] == "INTERMEDIATE"
    assert stops[1]["reason"] == "safety_car_opportunity"
    assert stops[1]["pit_loss_s"] == 9.5


def test_sc_opportunity_respects_compound_legality_with_one_stop_left():
    s = state()
    s.total_laps = 26
    policy = Policy(id="wait", label="One remaining stop", max_stops=1,
                    react_to_weather=False, dry_stops=(Stop(lap=24, compound=TireCompound.HARD),))
    result = project(s, (policy,), cfg(safety_car_lap=19,
                         degradation_spread_fraction=0), include_flips=False)
    assert by_id(result, "wait")["invalid_probability"] == 0
    assert by_id(result, "wait")["stops"][0]["compound"] == "HARD"


def test_default_box_and_stay_have_matched_second_stop_options_and_budget():
    from src.calculators.projection import default_policies
    policies = default_policies(state(), cfg())
    assert len(policies) == 9
    assert all(p.max_stops == 2 for p in policies)
    box = {p.dry_stops[1] for p in policies if len(p.dry_stops) == 2 and p.dry_stops[0].lap == 18}
    stay = {p.dry_stops[1] for p in policies if len(p.dry_stops) == 2 and p.dry_stops[0].lap > 18}
    assert box == stay and {s.lap for s in box} == {34, 38}


def test_safety_car_compresses_the_field_in_position_order():
    s = SyntheticRaceAdapter.create_race_state(current_lap=18, total_laps=52, stint_length_laps=17)
    s.subject_driver.position = 3
    s.subject_driver.last_lap_time_s = 100
    s.competitors = [r.model_copy(update={"gap_to_subject_s": gap, "current_compound": TireCompound.MEDIUM,
                                        "tyre_age_laps": 17, "last_lap_time_s": 100})
                     for r, gap in zip(s.competitors, (10, 20))]
    stay = Policy(id="stay", label="No stops", max_stops=0)
    config = cfg(degradation_scale=0, cliff_rate_s=0, fuel_effect_s_per_lap=0,
                 safety_car_lap=19, safety_car_pace_delay_s=0)
    snapshot = _snapshot(s, config)
    packed = simulate_policy(snapshot, stay, Scenario(None, 0, 1), config)
    plain = simulate_policy(snapshot, stay, Scenario(None, 0, 1),
                            config.model_copy(update={"safety_car_lap": None}))
    assert plain.times[1] - packed.times[1] == pytest.approx(19)
    assert packed.positions[1] == 3


def test_confidence_tolerance_counts_boundary_as_too_close():
    from src.calculators.projection import Trace, _confidence
    scenarios = [Scenario(None, 0, .25), Scenario(None, 0, .25),
                 Scenario(22, 0, .25), Scenario(22, 0, .25)]
    traces = {"stay": [Trace([0, 100], [], [], True) for _ in scenarios],
              "box": [Trace([0, t], [], [], True) for t in (101, 102, 98, 99)]}
    confidence, groups = _confidence(traces, scenarios, "stay", "box", 1)
    assert confidence["stay_clearly_better"] == .25
    assert confidence["box_clearly_better"] == .25
    assert confidence["too_close_to_call"] == .5
    assert {g["id"]: g["expected_stay_advantage_s"] for g in groups} == {"rain": -1.5, "no_rain": 1.5}


def test_dry_wear_uncertainty_prevents_a_sure_win_from_tiny_margin():
    uncertain = project(state(), plans(), cfg(), include_flips=False)
    assert uncertain["call_comparison"]["p10"][-1] < uncertain["call_comparison"]["p90"][-1]
    assert uncertain["call_confidence"]["too_close_to_call"] > .5
    fixed = project(state(), plans(), cfg(degradation_spread_fraction=0), include_flips=False)
    assert fixed["call_comparison"]["p10"][-1] == fixed["call_comparison"]["p90"][-1]
    assert sum(uncertain["call_confidence"][name] for name in
               ("stay_clearly_better", "box_clearly_better", "too_close_to_call")) == pytest.approx(1)


def test_raw_precision_and_display_seconds_are_separate_at_every_sweep_point():
    result = project(state(.7), plans(), cfg(safety_car_sweep_offsets=(),
                         rain_sweep_offsets=(4,), rain_probability_sweep=(), pit_loss_sweep_s=(5, 6, 7, 8)))
    assert result["display"]["call_margin_s"] == round(result["call_margin_s"], 1)
    assert result["call_margin_s"] != result["display"]["call_margin_s"]
    for sweep in result["flip_thresholds"]:
        for point in sweep["sweep"]:
            assert point["call"] in {"STAY_OUT", "BOX_NOW"}
            assert point["display"]["call_margin_s"] == round(point["call_margin_s"], 1)
            assert point["scenario_group_margins"]
    for scenario in result["scenarios"]:
        for plan in scenario["plans"]:
            assert plan["display"]["cumulative_time"] == [round(v, 1) for v in plan["cumulative_time"]]


def test_persistent_pace_offset_and_lap_noise_have_distinct_accumulation():
    s = state().model_copy(update={"competitors": []})
    config = cfg(degradation_scale=0, cliff_rate_s=0, fuel_effect_s_per_lap=0,
                 traffic_penalty_s=0)
    stay = Policy(id="stay", label="Stay", react_to_weather=False)
    baseline = simulate_policy(s, stay, Scenario(None, 0, 1), config)
    persistent = simulate_policy(s, stay, Scenario(None, 0, 1, base_pace_offset_s=2), config)
    noise = (3., -3.) + (0.,)*(s.total_laps-s.current_lap-2)
    noisy = simulate_policy(s, stay, Scenario(None, 0, 1, lap_noise_s=noise), config)
    assert [a-b for a,b in zip(persistent.times[1:6], baseline.times[1:6])] == pytest.approx([2,4,6,8,10])
    assert [a-b for a,b in zip(noisy.times[1:6], baseline.times[1:6])] == pytest.approx([3,0,0,0,0])
    with pytest.raises(ValueError, match="remaining race"):
        simulate_policy(s, stay, Scenario(None, 0, 1, lap_noise_s=(1.,)), config)


def test_added_uncertainty_preserves_existing_draws_and_shared_realizations():
    from src.calculators.projection import sample_scenarios
    s = state(.5)
    original = cfg()
    added = original.model_copy(update={"base_pace_sigma_s": .5, "lap_noise_sigma_s": 1.})
    before, after = sample_scenarios(s, original), sample_scenarios(s, added)
    fields = lambda rows: [(r.rain_lap, r.pit_offset_s, r.weight, r.degradation_multiplier) for r in rows]
    assert fields(before) == fields(after)
    assert after == sample_scenarios(s, added)
    assert all(r.base_pace_offset_s == 0 and r.lap_noise_s == () for r in before)
    assert sum(r.base_pace_offset_s for r in after) == pytest.approx(0)
    for lap in range(s.total_laps-s.current_lap):
        assert sum(r.lap_noise_s[lap] for r in after) == pytest.approx(0)
    assert [(r.base_pace_offset_s, r.lap_noise_s) for r in after[:4]] == [
        (r.base_pace_offset_s, r.lap_noise_s) for r in after[4:]]
