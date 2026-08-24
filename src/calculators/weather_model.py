"""Deterministic weather crossover and track condition model."""
from typing import Optional, Tuple
from src.core.models import ObservedWeather, WeatherForecast, TireCompound


class WeatherModel:
    """Calculates track crossover conditions between slick, intermediate, and wet tyres."""

    @staticmethod
    def evaluate_crossover(
        observed: ObservedWeather,
        forecast: WeatherForecast,
        current_lap: int,
    ) -> Tuple[TireCompound, float, str]:
        """
        Determines the optimal compound based on observed and forecasted weather.
        Returns: (optimal_compound, crossover_urgency_score, rationale)
        """
        is_raining = observed.rainfall.value
        rain_prob = forecast.rain_probability.value
        arrival = forecast.expected_arrival_laps.value
        intensity = forecast.intensity.value

        # 1. Currently raining
        if is_raining:
            if intensity == "HEAVY":
                return TireCompound.WET, 9.0, "Active heavy rainfall detected on circuit."
            return TireCompound.INTERMEDIATE, 8.5, "Active rainfall on circuit; intermediate crossover active."

        # 2. Imminent rain forecast (arrival within 1-2 laps with >= 60% probability)
        if arrival is not None and arrival <= 2 and rain_prob >= 0.60:
            urgency = 7.5 if arrival == 1 else 6.0
            return (
                TireCompound.INTERMEDIATE,
                urgency,
                f"Rain expected in {arrival} lap(s) with {rain_prob*100:.0f}% confidence; pit window for Inters opening.",
            )

        # 3. Track is dry
        return TireCompound.HARD, 0.0, "Track is currently dry; slick compounds optimal."
