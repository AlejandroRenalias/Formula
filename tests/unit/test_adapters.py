"""Unit tests for adapter layers and scenarios."""
import pytest
from src.adapters.scenarios import SCENARIOS
from src.core.models import TrackStatus, TireCompound, StrategyObjective, RiskProfile
from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.orchestrator.pipeline import StrategyPipeline


def test_scenarios_catalog():
    """Verify scenario catalog configuration."""
    assert "silverstone_2024" in SCENARIOS
    assert "synthetic_sandbox" in SCENARIOS

    silverstone = SCENARIOS["silverstone_2024"]
    assert silverstone.total_laps == 52
    assert "NOR" in silverstone.available_drivers
    assert 18 in silverstone.forecast_timeline
    assert silverstone.forecast_timeline[18]["rain_prob"] == 0.70


def test_scenario_execution_across_laps():
    """Verify strategy pipeline runs properly across different race laps."""
    pipeline = StrategyPipeline()

    # Lap 15 (Dry, rain far away) -> Stay out
    state_l15 = SyntheticRaceAdapter.create_race_state(
        current_lap=15,
        stint_length_laps=14,
        rain_probability=0.20,
        rain_arrival_laps=5,
    )
    decision_l15 = pipeline.run_strategy_cycle(state_l15)
    assert decision_l15.selected_candidate is not None

    # Lap 19 (Rain imminent in 1 lap) -> Box for Inters
    state_l19 = SyntheticRaceAdapter.create_race_state(
        current_lap=19,
        stint_length_laps=18,
        rain_probability=0.90,
        rain_arrival_laps=1,
    )
    decision_l19 = pipeline.run_strategy_cycle(state_l19)
    assert decision_l19.selected_candidate.target_compound == TireCompound.INTERMEDIATE
