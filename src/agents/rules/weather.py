"""Deterministic Rule-Based Weather Specialist Agent with Factor Ownership."""
from typing import Dict, List
from src.agents.base import BaseSpecialistAgent
from src.core.context_builder import WeatherContext
from src.core.models import (
    AgentReport,
    ConfidenceLevel,
    PitAction,
    TireCompound,
)


class RuleBasedWeatherAgent(BaseSpecialistAgent[WeatherContext]):
    """
    Weather Specialist Agent.
    Strictly owns:
    - wet_weather_crossover_gain
    - dry_track_wet_compound_penalty
    - slick_on_wet_track_penalty
    - rain_arrival_crossover_timing
    """

    def __init__(self):
        super().__init__(name="Weather Specialist", role="Meteorology & Crossover")

    def evaluate(self, context: WeatherContext) -> AgentReport:
        scores: Dict[str, float] = {}
        factors_map: Dict[str, Dict[str, float]] = {}
        key_risks: List[str] = []

        is_raining = context.is_raining_currently
        rain_prob = context.rain_probability
        arrival = context.rain_arrival_laps

        if rain_prob >= 0.60 and arrival is not None and arrival <= 3:
            key_risks.append(f"Rain arriving in {arrival} laps ({rain_prob*100:.0f}% confidence).")

        for cand in context.candidates:
            factors: Dict[str, float] = {}

            if is_raining:
                if cand.pit_action == PitAction.BOX_NOW and cand.target_compound in (TireCompound.INTERMEDIATE, TireCompound.WET):
                    factors["wet_weather_crossover_gain"] = +8.0
                elif cand.pit_action == PitAction.STAY_OUT and context.current_compound not in (TireCompound.INTERMEDIATE, TireCompound.WET):
                    factors["slick_on_wet_track_penalty"] = -8.0
            else:
                # Track is dry
                if arrival is not None and arrival <= 2 and rain_prob >= 0.60:
                    # Imminent rain
                    if cand.pit_action == PitAction.BOX_NOW and cand.target_compound in (TireCompound.INTERMEDIATE, TireCompound.WET):
                        factors["preemptive_wet_pit_stop_gain"] = +6.5
                    elif cand.pit_action == PitAction.BOX_NOW and cand.target_compound not in (TireCompound.INTERMEDIATE, TireCompound.WET):
                        factors["slicks_before_rain_penalty"] = -6.0
                    elif cand.pit_action == PitAction.STAY_OUT:
                        factors["stretch_slicks_to_rain_window"] = +4.0
                else:
                    # Stable dry conditions
                    if cand.pit_action == PitAction.BOX_NOW and cand.target_compound in (TireCompound.INTERMEDIATE, TireCompound.WET):
                        factors["wet_tyres_on_dry_track_penalty"] = -9.0
                    else:
                        factors["dry_track_normal_operation"] = +0.5

            total = round(sum(factors.values()), 2)
            scores[cand.candidate_id] = total
            factors_map[cand.candidate_id] = factors

        best_cand_id = max(scores, key=scores.get)
        confidence = ConfidenceLevel.HIGH if is_raining or rain_prob < 0.20 else ConfidenceLevel.MEDIUM

        rationale = (
            f"Observed track: {'WET' if is_raining else 'DRY'} ({context.track_temp_c:.1f}°C). "
            f"Rain forecast: {rain_prob*100:.0f}% probability, ETA: {arrival if arrival is not None else 'N/A'} laps."
        )

        return AgentReport(
            agent_name=self.name,
            role=self.role,
            recommended_candidate_id=best_cand_id,
            candidate_scores=scores,
            candidate_factors=factors_map,
            confidence=confidence,
            rationale=rationale,
            key_risks=key_risks,
            veto=False,
        )
