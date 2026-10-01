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
    assert result["margin_s"] is None
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
    flip = next(f for f in result["flip_thresholds"] if f["assumption"] == "pit_loss_s")
    assert {v["value"]: v["recommended"] for v in flip["sweep"]}[11] == "two"
    assert {v["value"]: v["recommended"] for v in flip["sweep"]}[12] == "one"
    assert flip["transitions"][0]["from_value"] == 11
    assert flip["transitions"][0]["to_value"] == 12


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
    assert result == saved
