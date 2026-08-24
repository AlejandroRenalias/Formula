"""Deterministic Rule-Based Race Control Specialist Agent with Factor Ownership."""
from typing import Dict, List
from src.agents.base import BaseSpecialistAgent
from src.core.context_builder import RaceControlContext
from src.core.models import (
    AgentReport,
    ConfidenceLevel,
    PitAction,
    TrackStatus,
)


class RuleBasedRaceControlAgent(BaseSpecialistAgent[RaceControlContext]):
    """
    Race Control Specialist Agent.
    Strictly owns:
    - neutralised_pit_delta_saving (VSC/SC)
    - green_flag_full_pit_loss_cost
    - mandatory_dry_compound_fulfillment
    """

    def __init__(self):
        super().__init__(name="Race Control Specialist", role="Safety Car, Flags & Regulations")

    def evaluate(self, context: RaceControlContext) -> AgentReport:
        scores: Dict[str, float] = {}
        factors_map: Dict[str, Dict[str, float]] = {}
        key_risks: List[str] = []

        is_sc = context.track_status == TrackStatus.SAFETY_CAR
        is_vsc = context.track_status == TrackStatus.VSC
        saving_s = context.pit_time_saving_s

        if not context.mandatory_two_compounds_fulfilled:
            key_risks.append("Mandatory 2-dry-compound rule has not been fulfilled yet.")

        for cand in context.candidates:
            factors: Dict[str, float] = {}

            # 1. SC / VSC Pit Loss Delta Saving
            if is_sc or is_vsc:
                if cand.pit_action == PitAction.BOX_NOW:
                    factors["neutralised_pit_delta_saving"] = +7.0 if is_sc else +5.0
                else:
                    factors["missed_cheap_pit_window_penalty"] = -4.0 if is_sc else -2.5
            else:
                # Green flag
                if cand.pit_action == PitAction.BOX_NOW:
                    factors["green_flag_full_pit_loss_cost"] = 0.0
                else:
                    factors["green_flag_stay_out_preservation"] = +1.0

            # 2. Sporting Regulation fulfillment
            if not context.mandatory_two_compounds_fulfilled and cand.pit_action == PitAction.BOX_NOW:
                factors["mandatory_compound_fulfillment_progress"] = +2.0

            total = round(sum(factors.values()), 2)
            scores[cand.candidate_id] = total
            factors_map[cand.candidate_id] = factors

        best_cand_id = max(scores, key=scores.get)
        confidence = ConfidenceLevel.HIGH

        rationale = (
            f"Track Status: {context.track_status.value}. Pit delta saving: {saving_s:.1f}s. "
            f"Mandatory compound rule fulfilled: {context.mandatory_two_compounds_fulfilled}."
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
