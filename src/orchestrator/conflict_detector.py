"""Conflict detection and debate trigger engine."""
from typing import List, Tuple
from src.core.models import StrategyCandidate, AgentReport


class ConflictDetector:
    """Detects when specialist agent evaluations are in close contention or conflict."""

    DEBATE_SCORE_MARGIN_THRESHOLD = 2.0

    @classmethod
    def should_trigger_debate(
        cls,
        candidates: List[StrategyCandidate],
        reports: List[AgentReport],
    ) -> Tuple[bool, str]:
        """
        Determines if a debate round should be conducted.
        Returns: (should_debate, reason)
        """
        if not reports or len(reports) < 2:
            return False, "Insufficient reports"

        # 1. Check if specialists recommended different top candidates
        picks = {r.agent_name: r.recommended_candidate_id for r in reports}
        unique_picks = set(picks.values())

        if len(unique_picks) > 1:
            # 2. Check if the scores for competing picks are close
            avg_scores = {}
            for cand in candidates:
                scores = [r.candidate_scores.get(cand.candidate_id, 0.0) for r in reports]
                avg_scores[cand.candidate_id] = sum(scores) / len(scores)

            sorted_scores = sorted(avg_scores.values(), reverse=True)
            if len(sorted_scores) >= 2:
                margin = sorted_scores[0] - sorted_scores[1]
                if margin <= cls.DEBATE_SCORE_MARGIN_THRESHOLD:
                    return (
                        True,
                        f"Close call between candidates (score margin: {margin:.2f} <= {cls.DEBATE_SCORE_MARGIN_THRESHOLD}). Specialists differ: {picks}",
                    )

        return False, "Clear consensus among specialists."
