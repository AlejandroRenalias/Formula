"""FastF1 Data Adapter with strict structural knowledge cutoff."""
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import fastf1
import pandas as pd
import numpy as np

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

# Configure FastF1 cache directory
CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

COMPOUND_MAP = {
    "SOFT": TireCompound.SOFT,
    "MEDIUM": TireCompound.MEDIUM,
    "HARD": TireCompound.HARD,
    "INTERMEDIATE": TireCompound.INTERMEDIATE,
    "WET": TireCompound.WET,
}


class FastF1Adapter:
    """Loads real F1 race sessions from FastF1 and builds strictly time-sliced RaceState snapshots."""

    @classmethod
    def load_session(cls, year: int, race_name: str, session_type: str = "R") -> fastf1.core.Session:
        """Loads and caches a FastF1 session."""
        session = fastf1.get_session(year, race_name, session_type)
        session.load(telemetry=False, weather=True, laps=True)
        return session

    @classmethod
    def create_race_state_at_lap(
        cls,
        session: fastf1.core.Session,
        current_lap: int,
        subject_driver: str = "NOR",
        forecast_rain_prob: float = 0.0,
        forecast_rain_arrival_laps: Optional[int] = None,
        forecast_rain_intensity: str = "DRY",
        objective: StrategyObjective = StrategyObjective.MAXIMIZE_EXPECTED_POSITION,
        risk_profile: RiskProfile = RiskProfile.BALANCED,
    ) -> RaceState:
        """Constructs a strict knowledge-cutoff snapshot at the end of `current_lap`."""
        laps_df = session.laps
        weather_df = session.weather_data

        # 1. Subject driver laps sliced <= current_lap
        driver_laps = laps_df[laps_df["Driver"] == subject_driver]
        if driver_laps.empty:
            raise ValueError(f"Driver '{subject_driver}' not found in session laps.")

        driver_laps_up_to_current = driver_laps[driver_laps["LapNumber"] <= current_lap].copy()
        if driver_laps_up_to_current.empty:
            raise ValueError(f"No laps found for driver '{subject_driver}' up to lap {current_lap}.")

        latest_lap_row = driver_laps_up_to_current.iloc[-1]
        cutoff_time = latest_lap_row["Time"]

        # 2. Structural slicing of all session data <= cutoff_time
        sliced_laps = laps_df[laps_df["Time"] <= cutoff_time].copy()
        sliced_weather = weather_df[weather_df["Time"] <= cutoff_time].copy() if not weather_df.empty else pd.DataFrame()

        # 3. Build SubjectDriverState
        curr_compound_str = str(latest_lap_row.get("Compound", "MEDIUM")).upper()
        current_compound = COMPOUND_MAP.get(curr_compound_str, TireCompound.MEDIUM)
        stint_len = int(latest_lap_row.get("TyreLife", 1)) if pd.notna(latest_lap_row.get("TyreLife")) else 1
        pos = int(latest_lap_row.get("Position", 1)) if pd.notna(latest_lap_row.get("Position")) else 1
        last_lap_s = latest_lap_row["LapTime"].total_seconds() if pd.notna(latest_lap_row["LapTime"]) else 90.0

        # Used compounds up to cutoff
        used_comp_strings = driver_laps_up_to_current["Compound"].dropna().unique()
        used_compounds = [COMPOUND_MAP.get(str(c).upper(), TireCompound.MEDIUM) for c in used_comp_strings]
        pit_stops = int(driver_laps_up_to_current["PitInTime"].notna().sum())

        subject_state = SubjectDriverState(
            driver=subject_driver,
            team=str(latest_lap_row.get("Team", "McLaren")),
            position=pos,
            current_compound=current_compound,
            stint_length_laps=stint_len,
            total_pit_stops=pit_stops,
            used_compounds=used_compounds,
            last_lap_time_s=last_lap_s,
        )

        # 4. Build LapObservation history with data quality markers
        lap_history: List[LapObservation] = []
        for _, row in driver_laps_up_to_current.iterrows():
            lap_num = int(row["LapNumber"])
            lap_t_s = row["LapTime"].total_seconds() if pd.notna(row["LapTime"]) else 0.0
            comp = COMPOUND_MAP.get(str(row.get("Compound", "MEDIUM")).upper(), TireCompound.MEDIUM)
            age = int(row.get("TyreLife", lap_num)) if pd.notna(row.get("TyreLife")) else lap_num
            track_st_raw = str(row.get("TrackStatus", "1"))
            
            is_pit_in = pd.notna(row.get("PitInTime"))
            is_pit_out = pd.notna(row.get("PitOutTime"))
            is_accurate = bool(row.get("IsAccurate", True))

            # Map FastF1 track status code: '1' is Track Clear (Green), '2' Yellow, '4' SC, '6'/'7' VSC
            status = TrackStatus.GREEN
            if "4" in track_st_raw:
                status = TrackStatus.SAFETY_CAR
            elif "6" in track_st_raw or "7" in track_st_raw:
                status = TrackStatus.VSC
            elif "2" in track_st_raw:
                status = TrackStatus.YELLOW

            usable = is_accurate and status == TrackStatus.GREEN and not is_pit_in and not is_pit_out

            lap_history.append(
                LapObservation(
                    lap_number=lap_num,
                    lap_time_s=round(lap_t_s, 3),
                    compound=comp,
                    tyre_age_laps=age,
                    track_status=status,
                    is_pit_in_lap=is_pit_in,
                    is_pit_out_lap=is_pit_out,
                    usable_for_pace_model=usable,
                )
            )

        # 5. Extract Competitors State at cutoff
        competitors: List[CompetitorState] = []
        unique_drivers = sliced_laps["Driver"].unique()
        for d in unique_drivers:
            if d == subject_driver:
                continue
            d_laps = sliced_laps[sliced_laps["Driver"] == d]
            if d_laps.empty:
                continue
            last_d_lap = d_laps.iloc[-1]
            d_pos = int(last_d_lap.get("Position", 10)) if pd.notna(last_d_lap.get("Position")) else 10
            d_comp = COMPOUND_MAP.get(str(last_d_lap.get("Compound", "HARD")).upper(), TireCompound.HARD)
            d_age = int(last_d_lap.get("TyreLife", 10)) if pd.notna(last_d_lap.get("TyreLife")) else 10
            
            # Gap estimation relative to subject
            # If d is ahead (d_pos < pos), gap is positive; if behind, gap is negative
            # Approximate from lap time differences if official gap delta is missing
            pos_diff = pos - d_pos
            approx_gap = float(pos_diff * 2.5)  # approximate 2.5s per position

            competitors.append(
                CompetitorState(
                    driver=d,
                    team=str(last_d_lap.get("Team", "F1 Team")),
                    position=d_pos,
                    current_compound=d_comp,
                    tyre_age_laps=d_age,
                    gap_to_subject_s=approx_gap,
                    last_lap_time_s=last_d_lap["LapTime"].total_seconds() if pd.notna(last_d_lap["LapTime"]) else None,
                    is_in_pit=pd.notna(last_d_lap.get("PitInTime")),
                    pit_stop_count=int(d_laps["PitInTime"].notna().sum()),
                )
            )

        # 6. Observed Weather at Cutoff
        current_track_temp = 28.0
        current_air_temp = 20.0
        current_rainfall = False
        current_humidity = 60.0
        if not sliced_weather.empty:
            w_row = sliced_weather.iloc[-1]
            current_track_temp = float(w_row.get("TrackTemp", 28.0))
            current_air_temp = float(w_row.get("AirTemp", 20.0))
            current_rainfall = bool(w_row.get("Rainfall", False))
            current_humidity = float(w_row.get("Humidity", 60.0))

        # 7. Current Track Status
        current_track_status = lap_history[-1].track_status if lap_history else TrackStatus.GREEN

        # 8. Deterministic Calculations
        derived_pace = PaceModel.calculate_pace_metrics(lap_history)

        base_loss = (
            PitLossModel.DEFAULT_SC_LOSS_S if current_track_status == TrackStatus.SAFETY_CAR
            else PitLossModel.DEFAULT_VSC_LOSS_S if current_track_status == TrackStatus.VSC
            else PitLossModel.DEFAULT_GREEN_LOSS_S
        )
        rejoin_pos, rejoin_gap = TrafficModel.predict_rejoin(subject_state, competitors, base_loss)
        pit_loss = PitLossModel.calculate_pit_loss(
            track_status=current_track_status,
            expected_rejoin_pos=rejoin_pos,
            expected_rejoin_gap=rejoin_gap,
        )

        total_laps_in_race = int(session.total_laps) if hasattr(session, "total_laps") and session.total_laps else 52

        now_dt = datetime.now(timezone.utc)
        return RaceState(
            current_lap=current_lap,
            total_laps=total_laps_in_race,
            timestamp=now_dt,
            knowledge_cutoff=now_dt,
            subject_driver=subject_state,
            competitors=competitors,
            track_status=current_track_status,
            observed_weather=ObservedWeather(
                track_temp_c=ProvenanceMetric(value=current_track_temp, source=DataSource.REAL_FASTF1),
                air_temp_c=ProvenanceMetric(value=current_air_temp, source=DataSource.REAL_FASTF1),
                rainfall=ProvenanceMetric(value=current_rainfall, source=DataSource.REAL_FASTF1),
                humidity_pct=ProvenanceMetric(value=current_humidity, source=DataSource.REAL_FASTF1),
            ),
            weather_forecast=WeatherForecast(
                rain_probability=ProvenanceMetric(value=forecast_rain_prob, source=DataSource.SCENARIO_FORECAST),
                expected_arrival_laps=ProvenanceMetric(value=forecast_rain_arrival_laps, source=DataSource.SCENARIO_FORECAST),
                intensity=ProvenanceMetric(value=forecast_rain_intensity, source=DataSource.SCENARIO_FORECAST),
                confidence=DataQuality.HIGH if forecast_rain_prob > 0.5 else DataQuality.LOW,
            ),
            lap_history=lap_history,
            derived_pace=derived_pace,
            pit_loss=pit_loss,
            objective=objective,
            risk_profile=risk_profile,
        )
