"""Traffic and rejoin prediction model."""
from typing import List, Tuple
from src.core.models import CompetitorState, SubjectDriverState


class TrafficModel:
    """Predicts rejoin position and traffic window risk."""

    @staticmethod
    def predict_rejoin(
        subject: SubjectDriverState,
        competitors: List[CompetitorState],
        pit_loss_s: float,
    ) -> Tuple[int, float, float]:
        """
        Calculates projected position and gap to surrounding cars if subject pits now.
        Returns: (projected_position, gap_to_traffic_ahead_s, gap_to_traffic_behind_s)
        """
        # Subject's current effective race time offset = 0.0
        # If subject pits, they lose `pit_loss_s`.
        # Competitors behind subject have negative gap (e.g. -5.0s means 5.0s behind).
        # Competitors ahead have positive gap (e.g. +3.0s means 3.0s ahead).
        
        # After pit stop, subject's gap to leader becomes:
        # (current gap to leader) + pit_loss_s.
        
        # For each competitor:
        # gap_to_subject_s is relative to subject (positive = ahead, negative = behind).
        # If subject loses pit_loss_s, new gap to competitor = comp.gap_to_subject_s - pit_loss_s.
        # If new gap > 0, competitor is ahead of subject.
        # If new gap < 0, competitor is behind subject.
        
        cars_ahead_after_pit = 0
        closest_gap_ahead = 999.0
        closest_gap_behind = 999.0

        for comp in competitors:
            # Competitor is already ahead
            if comp.gap_to_subject_s >= 0:
                cars_ahead_after_pit += 1
            else:
                # Competitor is currently behind (gap_to_subject_s is negative)
                gap_behind = abs(comp.gap_to_subject_s)
                if pit_loss_s > gap_behind:
                    # Competitor jumps subject during pit stop!
                    cars_ahead_after_pit += 1
                    lead_gap = pit_loss_s - gap_behind
                    closest_gap_ahead = min(closest_gap_ahead, lead_gap)
                else:
                    # Subject stays ahead of competitor
                    margin = gap_behind - pit_loss_s
                    closest_gap_behind = min(closest_gap_behind, margin)

        projected_position = cars_ahead_after_pit + 1
        min_gap_traffic = min(closest_gap_ahead, closest_gap_behind)
        if min_gap_traffic == 999.0:
            min_gap_traffic = 10.0

        return projected_position, round(min_gap_traffic, 2)
