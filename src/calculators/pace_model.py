"""Deterministic pace regression and degradation estimation."""
from typing import List, Tuple
import numpy as np
from src.core.models import LapObservation, TrackStatus, DerivedPaceMetrics
from src.core.provenance import DataSource, DataQuality, ProvenanceMetric


class PaceModel:
    """Calculates driver pace trends and empirical degradation from clean laps."""

    @staticmethod
    def filter_clean_laps(laps: List[LapObservation]) -> List[LapObservation]:
        """Preserves raw lap history but filters out unusable laps for pace regression."""
        return [
            lap for lap in laps
            if lap.usable_for_pace_model
            and not lap.is_pit_in_lap
            and not lap.is_pit_out_lap
            and lap.track_status == TrackStatus.GREEN
            and lap.lap_time_s > 0
        ]

    @classmethod
    def calculate_pace_metrics(
        cls,
        lap_history: List[LapObservation],
        window_laps: int = 6,
        fuel_correction_s_per_lap: float = 0.05,  # Lap time gain from fuel burn
    ) -> DerivedPaceMetrics:
        """
        Calculates pace trend and tyre degradation rate using linear regression on clean laps.
        Corrects for natural fuel burn (cars get faster as fuel burns off).
        """
        clean_laps = cls.filter_clean_laps(lap_history)

        if not clean_laps:
            return DerivedPaceMetrics(
                recent_pace_trend_s_per_lap=ProvenanceMetric(
                    value=0.0, source=DataSource.DERIVED_MODEL, quality=DataQuality.LOW, notes="No clean laps"
                ),
                degradation_rate_s_per_lap=ProvenanceMetric(
                    value=0.07, source=DataSource.DERIVED_MODEL, quality=DataQuality.LOW, notes="Default baseline"
                ),
                clean_air_potential_lap_time_s=ProvenanceMetric(
                    value=80.0, source=DataSource.DERIVED_MODEL, quality=DataQuality.LOW
                ),
                pace_confidence=DataQuality.LOW,
            )

        recent_laps = clean_laps[-window_laps:]
        lap_numbers = np.array([lap.lap_number for lap in recent_laps])
        lap_times = np.array([lap.lap_time_s for lap in recent_laps])

        if len(recent_laps) >= 3:
            # Linear regression: lap_time = slope * lap_number + intercept
            slope, _ = np.polyfit(lap_numbers, lap_times, 1)
            raw_trend = float(slope)
            # Degradation = raw slope + fuel burn compensation (fuel burn speeds car up by ~0.05s/lap)
            deg_rate = max(0.0, float(raw_trend + fuel_correction_s_per_lap))
            quality = DataQuality.HIGH if len(recent_laps) >= 5 else DataQuality.MEDIUM
        else:
            raw_trend = 0.0
            deg_rate = 0.07
            quality = DataQuality.LOW

        best_clean_pace = float(np.min(lap_times))

        return DerivedPaceMetrics(
            recent_pace_trend_s_per_lap=ProvenanceMetric(
                value=round(raw_trend, 4),
                source=DataSource.DERIVED_MODEL,
                quality=quality,
                notes=f"Calculated over {len(recent_laps)} clean laps",
            ),
            degradation_rate_s_per_lap=ProvenanceMetric(
                value=round(deg_rate, 4),
                source=DataSource.DERIVED_MODEL,
                quality=quality,
                notes="Compensated for fuel burn rate",
            ),
            clean_air_potential_lap_time_s=ProvenanceMetric(
                value=round(best_clean_pace, 3),
                source=DataSource.DERIVED_MODEL,
                quality=quality,
            ),
            pace_confidence=quality,
        )
