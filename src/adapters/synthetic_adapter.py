"""Synthetic race adapter with strict provenance preservation and structural cutoff."""
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from src.core.models import (
    RaceState,
    SubjectDriverState,
    CompetitorState,
    TrackStatus,
    ObservedWeather,
    WeatherForecast,
    LapObservation,
    DerivedPaceMetrics,
    PitLossMetrics,
    TireCompound,
    StrategyObjective,
    RiskProfile,
)
from src.core.provenance import DataSource, DataQuality, ProvenanceMetric
from src.calculators.pace_model import PaceModel
from src.calculators.pit_loss_model import PitLossModel
from src.calculators.traffic_model import TrafficModel


class SyntheticRaceAdapter:
    """Generates strictly validated RaceState fixtures with end-to-end provenance preservation."""

    @classmethod
    def create_race_state(
        cls,
        current_lap: int = 25,
        total_laps: int = 57,
        subject_driver: str = "NOR",
        team: str = "McLaren",
        position: int = 1,
        current_compound: TireCompound = TireCompound.MEDIUM,
        stint_length_laps: int = 24,
        total_pit_stops: int = 0,
        used_compounds: Optional[List[TireCompound]] = None,
        last_lap_time_s: float = 91.5,
        track_status: TrackStatus = TrackStatus.GREEN,
        is_raining: bool = False,
        rain_probability: float = 0.0,
        rain_arrival_laps: Optional[int] = None,
        rain_intensity: str = "DRY",
        track_temp_c: float = 32.0,
        competitors: Optional[List[CompetitorState]] = None,
        objective: StrategyObjective = StrategyObjective.MAXIMIZE_EXPECTED_POSITION,
        risk_profile: RiskProfile = RiskProfile.BALANCED,
        is_sandbox_override: bool = False,
    ) -> RaceState:
        now = datetime(2024, 7, 7, 14, 0, 0, tzinfo=timezone.utc) + timedelta(minutes=int(current_lap * 1.5))
        knowledge_cutoff = now

        if used_compounds is None:
            used_compounds = [current_compound]

        # 1. Structural Cutoff: Generate raw session and slice strictly <= current_lap & <= cutoff
        full_session_laps: List[LapObservation] = []
        base_lap_time = 90.0
        for lap_idx in range(1, total_laps + 1):
            lap_t = base_lap_time + (lap_idx * 0.07)
            lap_time_stamp = datetime(2024, 7, 7, 14, 0, 0, tzinfo=timezone.utc) + timedelta(minutes=int(lap_idx * 1.5))
            full_session_laps.append(
                LapObservation(
                    lap_number=lap_idx,
                    lap_time_s=round(lap_t, 3),
                    compound=current_compound,
                    tyre_age_laps=lap_idx,
                    track_status=track_status if lap_idx == current_lap else TrackStatus.GREEN,
                    is_pit_in_lap=False,
                    is_pit_out_lap=(lap_idx == 1),
                    usable_for_pace_model=True,
                    timestamp=lap_time_stamp,
                )
            )

        # Physical slicing before passing to calculators
        available_lap_history = [
            l for l in full_session_laps
            if l.lap_number <= current_lap and (l.timestamp is None or l.timestamp <= knowledge_cutoff)
        ]

        # Default competitors if not provided
        if competitors is None:
            competitors = [
                CompetitorState(
                    driver="VER",
                    team="Red Bull",
                    position=2,
                    current_compound=TireCompound.HARD,
                    tyre_age_laps=5,
                    gap_to_subject_s=-3.5,
                    last_lap_time_s=90.8,
                    is_in_pit=False,
                    pit_stop_count=1,
                ),
                CompetitorState(
                    driver="HAM",
                    team="Mercedes",
                    position=3,
                    current_compound=TireCompound.MEDIUM,
                    tyre_age_laps=24,
                    gap_to_subject_s=-18.0,
                    last_lap_time_s=91.8,
                    is_in_pit=False,
                    pit_stop_count=0,
                ),
            ]

        subject_state = SubjectDriverState(
            driver=subject_driver,
            team=team,
            position=position,
            current_compound=current_compound,
            stint_length_laps=stint_length_laps,
            total_pit_stops=total_pit_stops,
            used_compounds=used_compounds,
            last_lap_time_s=last_lap_time_s,
        )

        # Calculators only receive available_lap_history -> produces DERIVED_MODEL provenance
        derived_pace = PaceModel.calculate_pace_metrics(available_lap_history)

        base_loss = (
            PitLossModel.DEFAULT_SC_LOSS_S if track_status == TrackStatus.SAFETY_CAR
            else PitLossModel.DEFAULT_VSC_LOSS_S if track_status == TrackStatus.VSC
            else PitLossModel.DEFAULT_GREEN_LOSS_S
        )
        rejoin_pos, rejoin_gap = TrafficModel.predict_rejoin(subject_state, competitors, base_loss)
        pit_loss = PitLossModel.calculate_pit_loss(
            track_status=track_status,
            expected_rejoin_pos=rejoin_pos,
            expected_rejoin_gap=rejoin_gap,
        )

        # Explicit Provenance Tagging
        weather_source = DataSource.USER_DEFINED if is_sandbox_override else DataSource.SCENARIO_FORECAST
        observed_source = DataSource.USER_DEFINED if is_sandbox_override else DataSource.REAL_FASTF1

        return RaceState(
            current_lap=current_lap,
            total_laps=total_laps,
            timestamp=now,
            knowledge_cutoff=knowledge_cutoff,
            subject_driver=subject_state,
            competitors=competitors,
            track_status=track_status,
            observed_weather=ObservedWeather(
                track_temp_c=ProvenanceMetric(value=track_temp_c, source=observed_source),
                air_temp_c=ProvenanceMetric(value=22.0, source=observed_source),
                rainfall=ProvenanceMetric(value=is_raining, source=observed_source),
                humidity_pct=ProvenanceMetric(value=65.0, source=observed_source),
            ),
            weather_forecast=WeatherForecast(
                rain_probability=ProvenanceMetric(value=rain_probability, source=weather_source),
                expected_arrival_laps=ProvenanceMetric(value=rain_arrival_laps, source=weather_source),
                intensity=ProvenanceMetric(value=rain_intensity, source=weather_source),
                confidence=DataQuality.HIGH if rain_probability > 0.5 else DataQuality.LOW,
            ),
            lap_history=available_lap_history,
            derived_pace=derived_pace,
            pit_loss=pit_loss,
            objective=objective,
            risk_profile=risk_profile,
        )
