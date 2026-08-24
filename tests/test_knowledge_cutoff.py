"""Tests ensuring zero future-data leakage and strict knowledge cutoff enforcement."""
import pytest
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from src.core.models import (
    RaceState,
    SubjectDriverState,
    TrackStatus,
    ObservedWeather,
    WeatherForecast,
    DerivedPaceMetrics,
    PitLossMetrics,
    TireCompound,
)
from src.core.provenance import DataSource, ProvenanceMetric
from src.adapters.synthetic_adapter import SyntheticRaceAdapter


def test_replay_never_uses_future_data():
    """Verify that all observations in RaceState strictly precede current timestamp."""
    state = SyntheticRaceAdapter.create_race_state(current_lap=31)

    for lap in state.lap_history:
        assert lap.lap_number <= state.current_lap, f"Lap {lap.lap_number} exceeds current lap {state.current_lap}"
        if lap.timestamp:
            assert lap.timestamp <= state.knowledge_cutoff, (
                f"Lap timestamp {lap.timestamp} exceeds cutoff {state.knowledge_cutoff}"
            )


def test_knowledge_cutoff_cannot_exceed_timestamp():
    """Verify Pydantic validation rejects future knowledge cutoff."""
    now = datetime(2024, 7, 7, 14, 30, 0, tzinfo=timezone.utc)
    future_cutoff = now + timedelta(minutes=10)

    with pytest.raises(ValidationError) as exc_info:
        RaceState(
            current_lap=20,
            total_laps=57,
            timestamp=now,
            knowledge_cutoff=future_cutoff,  # Illegal: in the future!
            subject_driver=SubjectDriverState(
                driver="NOR",
                team="McLaren",
                position=1,
                current_compound=TireCompound.MEDIUM,
                stint_length_laps=19,
                total_pit_stops=0,
                used_compounds=[TireCompound.MEDIUM],
                last_lap_time_s=91.0,
            ),
            competitors=[],
            track_status=TrackStatus.GREEN,
            observed_weather=ObservedWeather(
                track_temp_c=ProvenanceMetric(value=30.0, source=DataSource.REAL_FASTF1),
                air_temp_c=ProvenanceMetric(value=22.0, source=DataSource.REAL_FASTF1),
                rainfall=ProvenanceMetric(value=False, source=DataSource.REAL_FASTF1),
                humidity_pct=ProvenanceMetric(value=60.0, source=DataSource.REAL_FASTF1),
            ),
            weather_forecast=WeatherForecast(
                rain_probability=ProvenanceMetric(value=0.0, source=DataSource.SCENARIO_FORECAST),
                expected_arrival_laps=ProvenanceMetric(value=None, source=DataSource.SCENARIO_FORECAST),
                intensity=ProvenanceMetric(value="DRY", source=DataSource.SCENARIO_FORECAST),
            ),
            lap_history=[],
            derived_pace=DerivedPaceMetrics(
                recent_pace_trend_s_per_lap=ProvenanceMetric(value=0.05, source=DataSource.DERIVED_MODEL),
                degradation_rate_s_per_lap=ProvenanceMetric(value=0.08, source=DataSource.DERIVED_MODEL),
                clean_air_potential_lap_time_s=ProvenanceMetric(value=90.0, source=DataSource.DERIVED_MODEL),
            ),
            pit_loss=PitLossMetrics(
                current_pit_loss_s=21.5,
                expected_rejoin_position=2,
                expected_rejoin_gap_to_traffic_s=4.0,
            ),
        )

    assert "Knowledge cutoff" in str(exc_info.value)
