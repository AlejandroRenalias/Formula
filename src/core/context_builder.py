"""Role-specific context builders for specialist agents."""
from typing import List, Optional
from pydantic import BaseModel, Field
from src.core.models import (
    RaceState,
    StrategyCandidate,
    TireCompound,
    TrackStatus,
    StrategyObjective,
    RiskProfile,
)


class PaceTyreContext(BaseModel):
    """Focused telemetry, tire, and pace context for the Pace & Tyre Specialist."""
    current_lap: int
    total_laps: int
    driver_name: str
    current_compound: TireCompound
    stint_length_laps: int
    last_lap_time_s: float
    pace_trend_s_per_lap: float
    degradation_rate_s_per_lap: float
    clean_air_potential_s: float
    gap_ahead_s: Optional[float] = None
    gap_behind_s: Optional[float] = None
    rival_ahead_compound: Optional[TireCompound] = None
    rival_behind_compound: Optional[TireCompound] = None
    expected_rejoin_position: int
    expected_rejoin_gap_s: float
    candidates: List[StrategyCandidate]
    objective: StrategyObjective
    risk_profile: RiskProfile


class WeatherContext(BaseModel):
    """Focused meteorological context for the Weather Specialist."""
    current_lap: int
    track_temp_c: float
    air_temp_c: float
    is_raining_currently: bool
    rain_probability: float
    rain_arrival_laps: Optional[int]
    rain_intensity: str
    current_compound: TireCompound
    candidates: List[StrategyCandidate]


class RaceControlContext(BaseModel):
    """Focused track status and sporting regulations context for the Race Control Specialist."""
    current_lap: int
    track_status: TrackStatus
    green_pit_loss_s: float
    current_pit_loss_s: float
    pit_time_saving_s: float
    used_compounds: List[TireCompound]
    mandatory_two_compounds_fulfilled: bool
    candidates: List[StrategyCandidate]
    total_pit_stops: int


class ContextBuilder:
    """Builds role-specific context models from the global RaceState."""

    @staticmethod
    def build_pace_tyre_context(state: RaceState, candidates: List[StrategyCandidate]) -> PaceTyreContext:
        gap_ahead = None
        gap_behind = None
        rival_ahead_comp = None
        rival_behind_comp = None

        # Find closest rival ahead (smallest positive gap) and behind (largest negative gap)
        ahead = [c for c in state.competitors if c.gap_to_subject_s > 0]
        behind = [c for c in state.competitors if c.gap_to_subject_s < 0]

        if ahead:
            closest_ahead = min(ahead, key=lambda c: c.gap_to_subject_s)
            gap_ahead = closest_ahead.gap_to_subject_s
            rival_ahead_comp = closest_ahead.current_compound

        if behind:
            closest_behind = max(behind, key=lambda c: c.gap_to_subject_s)
            gap_behind = abs(closest_behind.gap_to_subject_s)
            rival_behind_comp = closest_behind.current_compound

        return PaceTyreContext(
            current_lap=state.current_lap,
            total_laps=state.total_laps,
            driver_name=state.subject_driver.driver,
            current_compound=state.subject_driver.current_compound,
            stint_length_laps=state.subject_driver.stint_length_laps,
            last_lap_time_s=state.subject_driver.last_lap_time_s,
            pace_trend_s_per_lap=state.derived_pace.recent_pace_trend_s_per_lap.value,
            degradation_rate_s_per_lap=state.derived_pace.degradation_rate_s_per_lap.value,
            clean_air_potential_s=state.derived_pace.clean_air_potential_lap_time_s.value,
            gap_ahead_s=gap_ahead,
            gap_behind_s=gap_behind,
            rival_ahead_compound=rival_ahead_comp,
            rival_behind_compound=rival_behind_comp,
            expected_rejoin_position=state.pit_loss.expected_rejoin_position,
            expected_rejoin_gap_s=state.pit_loss.expected_rejoin_gap_to_traffic_s,
            candidates=candidates,
            objective=state.objective,
            risk_profile=state.risk_profile,
        )

    @staticmethod
    def build_weather_context(state: RaceState, candidates: List[StrategyCandidate]) -> WeatherContext:
        return WeatherContext(
            current_lap=state.current_lap,
            track_temp_c=state.observed_weather.track_temp_c.value,
            air_temp_c=state.observed_weather.air_temp_c.value,
            is_raining_currently=state.observed_weather.rainfall.value,
            rain_probability=state.weather_forecast.rain_probability.value,
            rain_arrival_laps=state.weather_forecast.expected_arrival_laps.value,
            rain_intensity=state.weather_forecast.intensity.value,
            current_compound=state.subject_driver.current_compound,
            candidates=candidates,
        )

    @staticmethod
    def build_race_control_context(state: RaceState, candidates: List[StrategyCandidate]) -> RaceControlContext:
        # F1 Sporting regulation: must use at least 2 distinct dry compounds in a dry race
        used_unique_dry = {
            c for c in state.subject_driver.used_compounds
            if c in (TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD)
        }
        # If wet/inter used at any point, mandatory 2 dry compounds rule is lifted
        wet_used = any(
            c in (TireCompound.INTERMEDIATE, TireCompound.WET)
            for c in state.subject_driver.used_compounds
        )
        rule_fulfilled = len(used_unique_dry) >= 2 or wet_used

        pit_time_saving = state.pit_loss.green_pit_loss_s - state.pit_loss.current_pit_loss_s

        return RaceControlContext(
            current_lap=state.current_lap,
            track_status=state.track_status,
            green_pit_loss_s=state.pit_loss.green_pit_loss_s,
            current_pit_loss_s=state.pit_loss.current_pit_loss_s,
            pit_time_saving_s=pit_time_saving,
            used_compounds=state.subject_driver.used_compounds,
            mandatory_two_compounds_fulfilled=rule_fulfilled,
            candidates=candidates,
            total_pit_stops=state.subject_driver.total_pit_stops,
        )
