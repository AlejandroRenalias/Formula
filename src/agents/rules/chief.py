"""Deterministic Rule-Based Chief Race Strategist Agent with Auditable Score Breakdown."""
from typing import Dict, List, Optional
from src.core.models import (
    StrategyCandidate,
    AgentReport,
    StrategyDecision,
    ConfidenceLevel,
    NextTrigger,
    StrategyObjective,
    RiskProfile,
    PitAction,
)


class RuleBasedChiefStrategist:
    """Synthesizes specialist assessments, aggregates distinct factor breakdowns, and issues final calls."""

    def __init__(self, name: str = "Chief Race Strategist"):
        self.name = name

    def make_decision(
        self,
        lap: int,
        candidates: List[StrategyCandidate],
        specialist_reports: List[AgentReport],
        objective: StrategyObjective = StrategyObjective.MAXIMIZE_EXPECTED_POSITION,
        risk_profile: RiskProfile = RiskProfile.BALANCED,
        conflict_detected: bool = False,
        conflict_summary: Optional[str] = None,
        debate_held: bool = False,
        debate_transcript: Optional[str] = None,
    ) -> StrategyDecision:
        # 1. Weights based on objective and risk profile
        w_pace = 1.0
        w_weather = 1.2
        w_race_ctrl = 1.1

        if objective == StrategyObjective.PROTECT_TRACK_POSITION:
            w_race_ctrl += 0.3
        elif objective == StrategyObjective.CHASE_WIN:
            w_pace += 0.3

        if risk_profile == RiskProfile.CONSERVATIVE:
            w_weather += 0.3
        elif risk_profile == RiskProfile.AGGRESSIVE:
            w_pace += 0.4

        # 2. Aggregate candidate factors with zero overlap
        candidate_scores: Dict[str, float] = {}
        candidate_aggregated_factors: Dict[str, Dict[str, float]] = {}

        for cand in candidates:
            cand_id = cand.candidate_id
            cand_factors: Dict[str, float] = {}
            total = 0.0

            for report in specialist_reports:
                weight = w_pace if "Pace" in report.agent_name else (
                    w_weather if "Weather" in report.agent_name else w_race_ctrl
                )
                spec_factors = report.candidate_factors.get(cand_id, {})
                for factor_name, val in spec_factors.items():
                    weighted_val = round(val * weight, 2)
                    cand_factors[factor_name] = weighted_val
                    total += weighted_val

            candidate_scores[cand_id] = round(total, 2)
            candidate_aggregated_factors[cand_id] = cand_factors
            cand.candidate_strategy_score = round(total, 2)
            cand.factors = cand_factors

        # 3. Select winning candidate
        sorted_candidates = sorted(candidates, key=lambda c: c.candidate_strategy_score, reverse=True)
        winner = sorted_candidates[0]
        runner_up = sorted_candidates[1] if len(sorted_candidates) > 1 else None

        score_advantage = (
            round(winner.candidate_strategy_score - runner_up.candidate_strategy_score, 2)
            if runner_up
            else 5.0
        )

        # 4. Generate dynamic next triggers
        next_triggers = self._generate_next_triggers(lap, winner, specialist_reports)

        # 5. Build clear rationale summary
        specialist_summaries = " | ".join(
            f"{r.agent_name.split()[0]}: {r.recommended_candidate_id}"
            for r in specialist_reports
        )
        rationale = (
            f"Executed Candidate '{winner.candidate_id}' [{winner.ui_label}] ({winner.pit_action.value} - {winner.intent.value}). "
            f"Strategy score: {winner.candidate_strategy_score:.1f} vs next best: {runner_up.candidate_strategy_score if runner_up else 0:.1f}. "
            f"Specialist picks: [{specialist_summaries}]. {winner.description}"
        )

        confidence = (
            ConfidenceLevel.HIGH if score_advantage >= 3.0
            else ConfidenceLevel.MEDIUM if score_advantage >= 1.0
            else ConfidenceLevel.LOW
        )

        return StrategyDecision(
            lap=lap,
            selected_candidate=winner,
            all_candidates=sorted_candidates,
            pit_action=winner.pit_action,
            target_compound=winner.target_compound,
            pace_mode=winner.pace_mode,
            intent=winner.intent,
            target_driver=winner.target_driver,
            rationale=rationale,
            score_margin=score_advantage,
            confidence=confidence,
            specialist_evaluations=specialist_reports,
            score_breakdown=candidate_aggregated_factors.get(winner.candidate_id, {}),
            next_triggers=next_triggers,
            conflict_detected=conflict_detected,
            conflict_summary=conflict_summary,
            debate_held=debate_held,
            debate_transcript=debate_transcript,
        )

    def _generate_next_triggers(
        self,
        current_lap: int,
        selected: StrategyCandidate,
        reports: List[AgentReport],
    ) -> List[NextTrigger]:
        triggers: List[NextTrigger] = []

        if selected.pit_action == PitAction.STAY_OUT:
            triggers.append(
                NextTrigger(
                    condition_description=f"Routine lap {current_lap + 3} heartbeat review",
                    trigger_type="HEARTBEAT",
                    threshold_value=float(current_lap + 3),
                )
            )
            triggers.append(
                NextTrigger(
                    condition_description="Rival in pit window executes undercut",
                    trigger_type="RIVAL_PITTED",
                )
            )
            triggers.append(
                NextTrigger(
                    condition_description="Rain arrival countdown drops to <= 2 laps",
                    trigger_type="WEATHER_CHANGED",
                    threshold_value=2.0,
                )
            )
        else:
            triggers.append(
                NextTrigger(
                    condition_description="Post-pit out-lap traffic and delta check",
                    trigger_type="HEARTBEAT",
                    threshold_value=float(current_lap + 2),
                )
            )

        return triggers
