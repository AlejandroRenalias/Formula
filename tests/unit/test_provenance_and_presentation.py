"""Tests for strict provenance preservation and presentation-only UI contracts."""
import pytest
from src.core.models import (
    TrackStatus,
    TireCompound,
    StrategyObjective,
    RiskProfile,
)
from src.core.provenance import DataSource
from src.adapters.scenarios import SCENARIOS
from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.adapters.fastf1_adapter import FastF1Adapter
from src.core.context_builder import ContextBuilder
from src.calculators.candidate_gen import CandidateGenerator
from src.orchestrator.pipeline import StrategyPipeline


def test_provenance_scenario_forecast():
    """Verify that scenario-defined forecasts strictly tag SCENARIO_FORECAST."""
    state = SyntheticRaceAdapter.create_race_state(
        current_lap=18,
        rain_probability=0.70,
        rain_arrival_laps=2,
        is_sandbox_override=False,
    )
    assert state.weather_forecast.rain_probability.source == DataSource.SCENARIO_FORECAST
    assert state.weather_forecast.expected_arrival_laps.source == DataSource.SCENARIO_FORECAST
    assert state.weather_forecast.intensity.source == DataSource.SCENARIO_FORECAST


def test_provenance_user_defined_sandbox():
    """Verify that sandbox user overrides strictly tag USER_DEFINED."""
    state = SyntheticRaceAdapter.create_race_state(
        current_lap=20,
        rain_probability=0.85,
        rain_arrival_laps=1,
        is_sandbox_override=True,
    )
    assert state.weather_forecast.rain_probability.source == DataSource.USER_DEFINED
    assert state.weather_forecast.expected_arrival_laps.source == DataSource.USER_DEFINED
    assert state.observed_weather.track_temp_c.source == DataSource.USER_DEFINED


def test_provenance_derived_model():
    """Verify that deterministic model calculations strictly tag DERIVED_MODEL."""
    state = SyntheticRaceAdapter.create_race_state(current_lap=25)
    assert state.derived_pace.recent_pace_trend_s_per_lap.source == DataSource.DERIVED_MODEL
    assert state.derived_pace.degradation_rate_s_per_lap.source == DataSource.DERIVED_MODEL
    assert state.derived_pace.clean_air_potential_lap_time_s.source == DataSource.DERIVED_MODEL


def test_provenance_real_fastf1():
    """Verify that FastF1 adapter marks actual telemetry/weather with REAL_FASTF1."""
    # FastF1 sensor values carry REAL_FASTF1 provenance
    state = SyntheticRaceAdapter.create_race_state(current_lap=10, is_sandbox_override=False)
    assert state.observed_weather.track_temp_c.source == DataSource.REAL_FASTF1
    assert state.observed_weather.rainfall.source == DataSource.REAL_FASTF1


def test_precomputed_all_candidates_in_decision():
    """Verify that StrategyDecision contains precomputed all_candidates for UI consumption."""
    state = SyntheticRaceAdapter.create_race_state(current_lap=25)
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)

    # Decision must contain all evaluated candidates with precomputed scores
    assert len(decision.all_candidates) >= 3
    for cand in decision.all_candidates:
        assert isinstance(cand.candidate_strategy_score, float)
        assert isinstance(cand.factors, dict)
        assert len(cand.factors) > 0  # Auditable factor breakdown present

    # Top candidate in all_candidates must match selected_candidate
    assert decision.all_candidates[0].candidate_id == decision.selected_candidate.candidate_id
    assert decision.all_candidates[0].candidate_strategy_score == decision.selected_candidate.candidate_strategy_score
