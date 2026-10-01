"""End-to-end tactical scenario exams with factor breakdown verification."""
import pytest
from src.core.models import (
    TrackStatus,
    TireCompound,
    PitAction,
    StrategyIntent,
)
from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.orchestrator.pipeline import StrategyPipeline


def test_scenario_vsc_free_pit_stop():
    """
    Scenario: Stint is 24 laps old on Mediums. VSC is deployed.
    Expected: Chief Strategist must call BOX NOW to capture VSC delta savings.
    Score breakdown must include neutralised_pit_delta_saving.
    """
    state = SyntheticRaceAdapter.create_race_state(
        current_lap=25,
        stint_length_laps=24,
        current_compound=TireCompound.MEDIUM,
        track_status=TrackStatus.VSC,
    )
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)

    assert decision.pit_action == PitAction.BOX_NOW
    assert decision.selected_candidate.target_compound == TireCompound.HARD
    assert decision.intent == StrategyIntent.SAFETY_CAR_OPPORTUNITY
    assert "neutralised_pit_delta_saving" in decision.score_breakdown
    assert decision.score_breakdown["neutralised_pit_delta_saving"] > 0
    assert decision.score_margin > 0.0


def test_scenario_imminent_rain_crossover():
    """
    Scenario: Dry track, but rain is arriving in 1 lap with 85% probability.
    Expected: Chief Strategist must call BOX NOW for INTERMEDIATE tyres.
    Score breakdown must include preemptive_wet_pit_stop_gain.
    """
    state = SyntheticRaceAdapter.create_race_state(
        current_lap=30,
        stint_length_laps=15,
        current_compound=TireCompound.MEDIUM,
        track_status=TrackStatus.GREEN,
        is_raining=False,
        rain_probability=0.85,
        rain_arrival_laps=1,
        rain_intensity="MODERATE",
    )
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)

    assert decision.pit_action == PitAction.BOX_NOW
    assert decision.selected_candidate.target_compound == TireCompound.INTERMEDIATE
    assert decision.intent == StrategyIntent.WEATHER_CROSSOVER
    assert "preemptive_wet_pit_stop_gain" in decision.score_breakdown


def test_scenario_fresh_tyres_stay_out():
    """
    Scenario: Lap 6 of race, tyres are only 5 laps old, track is dry and green.
    Expected: Chief Strategist must call STAY OUT.
    """
    state = SyntheticRaceAdapter.create_race_state(
        current_lap=6,
        stint_length_laps=5,
        current_compound=TireCompound.MEDIUM,
        track_status=TrackStatus.GREEN,
        is_raining=False,
        rain_probability=0.0,
    )
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)

    assert decision.pit_action == PitAction.STAY_OUT
    assert "tyre_life_remaining" in decision.score_breakdown
