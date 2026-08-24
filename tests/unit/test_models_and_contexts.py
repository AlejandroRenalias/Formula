"""Unit tests for models, provenance, triggers, and context builders."""
import pytest
from src.core.models import (
    TireCompound,
    TrackStatus,
    PitAction,
    StrategyObjective,
    RiskProfile,
)
from src.core.provenance import DataSource, DataQuality, ProvenanceMetric
from src.core.context_builder import ContextBuilder
from src.core.triggers import TriggerEvaluator, DecisionTriggerType
from src.calculators.candidate_gen import CandidateGenerator
from src.adapters.synthetic_adapter import SyntheticRaceAdapter


def test_provenance_metric():
    """Verify ProvenanceMetric data integrity and tagging."""
    m = ProvenanceMetric(value=24.5, source=DataSource.REAL_FASTF1, quality=DataQuality.HIGH)
    assert m.value == 24.5
    assert m.source == DataSource.REAL_FASTF1
    assert m.quality == DataQuality.HIGH


def test_context_builders():
    """Verify that role-specific contexts contain only relevant, correctly mapped fields."""
    state = SyntheticRaceAdapter.create_race_state(
        current_lap=20,
        stint_length_laps=19,
        track_status=TrackStatus.VSC,
        rain_probability=0.75,
        rain_arrival_laps=2,
    )
    candidates = CandidateGenerator.generate_candidates(state)

    pace_ctx = ContextBuilder.build_pace_tyre_context(state, candidates)
    weather_ctx = ContextBuilder.build_weather_context(state, candidates)
    race_ctrl_ctx = ContextBuilder.build_race_control_context(state, candidates)

    # Pace context assertions
    assert pace_ctx.current_lap == 20
    assert pace_ctx.current_compound == TireCompound.MEDIUM
    assert pace_ctx.stint_length_laps == 19
    assert len(pace_ctx.candidates) == len(candidates)

    # Weather context assertions
    assert weather_ctx.rain_probability == 0.75
    assert weather_ctx.rain_arrival_laps == 2

    # Race Control context assertions
    assert race_ctrl_ctx.track_status == TrackStatus.VSC
    assert race_ctrl_ctx.pit_time_saving_s > 5.0
    assert not race_ctrl_ctx.mandatory_two_compounds_fulfilled


def test_trigger_evaluator():
    """Verify that race events trigger decision reviews."""
    prev_state = SyntheticRaceAdapter.create_race_state(current_lap=19, track_status=TrackStatus.GREEN)
    curr_state = SyntheticRaceAdapter.create_race_state(current_lap=20, track_status=TrackStatus.SAFETY_CAR)

    triggers = TriggerEvaluator.evaluate_triggers(curr_state, prev_state)
    trigger_types = [t.trigger_type for t in triggers]

    assert DecisionTriggerType.SC_DEPLOYED in trigger_types
    assert DecisionTriggerType.HEARTBEAT in trigger_types  # Lap 20 is divisible by 5
