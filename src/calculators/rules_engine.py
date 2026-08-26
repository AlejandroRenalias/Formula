"""Deterministic FIA Sporting Regulations validation engine (Season-Aware)."""
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from src.core.models import (
    TireCompound,
    StrategyCandidate,
    PitAction,
    SubjectDriverState,
    RaceState,
)


@dataclass(frozen=True)
class CandidateValidationResult:
    """Deterministic legality outcome before candidates enter strategy reasoning."""
    legal_candidates: List[StrategyCandidate]
    rejected_candidates: Dict[str, str]


class NoLegalCandidatesError(ValueError):
    """Raised when no generated candidate passes deterministic legality checks."""

    def __init__(self, current_lap: int, rejected_candidates: Dict[str, str]):
        self.current_lap = current_lap
        self.rejected_candidates = dict(rejected_candidates)
        details = "; ".join(
            f"{candidate_id}: {reason}"
            for candidate_id, reason in self.rejected_candidates.items()
        )
        super().__init__(
            f"No legal strategy candidates remain at lap {current_lap}. "
            f"Rejected candidates: {details}"
        )


class RulesEngine:
    """Validates strategic moves against FIA Sporting Regulations for specific seasons."""

    @classmethod
    def validate_candidates(
        cls, candidates: List[StrategyCandidate], state: RaceState
    ) -> CandidateValidationResult:
        """Filter generated candidates through the existing deterministic legality contract."""
        legal_candidates: List[StrategyCandidate] = []
        rejected_candidates: Dict[str, str] = {}
        # Current rainfall is an observation, not proof of the race-wide
        # regulatory exemption. Existing domain semantics treat use of an
        # intermediate/wet compound as the deterministic exemption evidence.
        dry_compound_rule_exempt = any(
            compound in (TireCompound.INTERMEDIATE, TireCompound.WET)
            for compound in state.subject_driver.used_compounds
        )

        for candidate in candidates:
            legal, reason = cls.is_candidate_legal(
                candidate=candidate,
                subject=state.subject_driver,
                current_lap=state.current_lap,
                total_laps=state.total_laps,
                dry_compound_rule_exempt=dry_compound_rule_exempt,
            )
            if legal:
                legal_candidates.append(candidate)
            else:
                rejected_candidates[candidate.candidate_id] = reason or "Rejected by RulesEngine."

        return CandidateValidationResult(
            legal_candidates=legal_candidates,
            rejected_candidates=rejected_candidates,
        )

    @staticmethod
    def is_candidate_legal(
        candidate: StrategyCandidate,
        subject: SubjectDriverState,
        current_lap: int,
        total_laps: int,
        dry_compound_rule_exempt: Optional[bool] = None,
        season: int = 2024,
        event_name: Optional[str] = None,
        is_wet_race: Optional[bool] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates if candidate complies with regulations for the given season:
        - 2021-2026: Must use at least 2 distinct dry compounds in a dry race before finish.
        - Minimum 1 pit stop required in standard Grand Prix.
        """
        # Backwards-compatible legacy keyword. New production callers must
        # provide the explicitly named regulatory meaning.
        if dry_compound_rule_exempt is None:
            dry_compound_rule_exempt = bool(is_wet_race)

        # The dry-compound rule is waived only when deterministic regulatory
        # evidence establishes the exemption.
        if dry_compound_rule_exempt:
            return True, None

        # Check if driver is attempting to finish race without fulfilling 2 compounds
        remaining_laps = total_laps - current_lap
        if remaining_laps <= 1:
            if candidate.pit_action == PitAction.STAY_OUT:
                used_dry = {
                    c for c in subject.used_compounds
                    if c in (TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD)
                }
                if len(used_dry) < 2:
                    return (
                        False,
                        f"Illegal ({season} Regs): Driver has only used {list(used_dry)} and must pit for a second dry compound before finish.",
                    )

        # If candidate pits, verify target compound is specified
        if candidate.pit_action == PitAction.BOX_NOW:
            if candidate.target_compound is None:
                return False, f"Illegal ({season} Regs): Pit action specified without target compound."

        return True, None
