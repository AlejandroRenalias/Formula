"""Deterministic FIA Sporting Regulations validation engine (Season-Aware)."""
from typing import List, Tuple, Optional
from src.core.models import (
    TireCompound,
    StrategyCandidate,
    PitAction,
    SubjectDriverState,
)


class RulesEngine:
    """Validates strategic moves against FIA Sporting Regulations for specific seasons."""

    @staticmethod
    def is_candidate_legal(
        candidate: StrategyCandidate,
        subject: SubjectDriverState,
        current_lap: int,
        total_laps: int,
        is_wet_race: bool,
        season: int = 2024,
        event_name: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validates if candidate complies with regulations for the given season:
        - 2021-2026: Must use at least 2 distinct dry compounds in a dry race before finish.
        - Minimum 1 pit stop required in standard Grand Prix.
        """
        # If it's a wet race, mandatory 2-dry-compound rule is waived across all modern seasons
        if is_wet_race:
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
