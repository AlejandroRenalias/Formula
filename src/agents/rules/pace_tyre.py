"""Deterministic Rule-Based Pace & Tyre Specialist Agent with Factor Ownership."""
from typing import Dict, List
from src.agents.base import BaseSpecialistAgent
from src.core.context_builder import PaceTyreContext
from src.core.models import (
    AgentReport,
    ConfidenceLevel,
    PitAction,
    PaceMode,
    StrategyIntent,
)
from src.calculators.tyre_model import TyreModel


class RuleBasedPaceTyreAgent(BaseSpecialistAgent[PaceTyreContext]):
    """
    Pace & Tyre Specialist Agent.
    Strictly owns:
    - tyre_health_gain
    - traffic_rejoin_penalty
    - pace_mode_offset
    - undercut_pace_gain
    """

    def __init__(self):
        super().__init__(name="Pace & Tyre Specialist", role="Pace & Tyre Modelling")

    def evaluate(self, context: PaceTyreContext) -> AgentReport:
        scores: Dict[str, float] = {}
        factors_map: Dict[str, Dict[str, float]] = {}
        tyre_health = TyreModel.estimate_tyre_condition(context.current_compound, context.stint_length_laps)
        deg_rate = context.degradation_rate_s_per_lap

        key_risks: List[str] = []
        if tyre_health < 0.25:
            key_risks.append(f"Current {context.current_compound.value} tyres near end of life ({context.stint_length_laps} laps).")
        if context.expected_rejoin_gap_s < 1.5:
            key_risks.append(f"Pitting now risks rejoining in heavy traffic behind P{context.expected_rejoin_position}.")

        for cand in context.candidates:
            factors: Dict[str, float] = {}

            # 1. Tyre health gain / penalty
            if cand.pit_action == PitAction.BOX_NOW:
                tyre_gain = round((1.0 - tyre_health) * 5.0, 2)
                factors["tyre_freshness_gain"] = tyre_gain

                # Traffic penalty / clean air bonus
                if context.expected_rejoin_gap_s < 1.5:
                    factors["traffic_rejoin_penalty"] = -2.0
                elif context.expected_rejoin_gap_s > 4.0:
                    factors["clean_air_rejoin_bonus"] = +1.2

                # Undercut incentive
                if cand.intent == StrategyIntent.UNDERCUT:
                    if context.gap_ahead_s and context.gap_ahead_s < 2.5:
                        factors["undercut_pace_advantage"] = +2.0
                    elif context.gap_behind_s and context.gap_behind_s < 2.0:
                        factors["undercut_defense_advantage"] = +1.5
            else:
                # STAY_OUT
                if tyre_health > 0.60:
                    factors["tyre_life_remaining"] = +3.5
                elif tyre_health < 0.25:
                    factors["tyre_cliff_penalty"] = -4.5

                if cand.pace_mode == PaceMode.PUSH:
                    if tyre_health > 0.40:
                        factors["overcut_push_pace"] = +1.5
                    else:
                        factors["pushing_on_dead_tyres_penalty"] = -2.5

                if cand.pace_mode == PaceMode.CONSERVE:
                    if tyre_health < 0.40:
                        factors["tyre_conservation_benefit"] = +1.0

            total = round(sum(factors.values()), 2)
            scores[cand.candidate_id] = total
            factors_map[cand.candidate_id] = factors

        best_cand_id = max(scores, key=scores.get)
        confidence = ConfidenceLevel.HIGH if context.stint_length_laps >= 5 else ConfidenceLevel.MEDIUM

        rationale = (
            f"Tyre health is at {tyre_health*100:.0f}% with degradation rate of {deg_rate:.2f} s/lap. "
            f"Candidate '{best_cand_id}' provides best pace/traffic compromise."
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
