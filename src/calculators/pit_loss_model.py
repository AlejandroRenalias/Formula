"""Pit loss calculation model under Green, VSC, and Safety Car conditions."""
from src.core.models import TrackStatus, PitLossMetrics


class PitLossModel:
    """Calculates pit lane delta loss under various race control conditions."""

    DEFAULT_GREEN_LOSS_S = 21.5
    DEFAULT_VSC_LOSS_S = 12.5
    DEFAULT_SC_LOSS_S = 9.5

    @classmethod
    def calculate_pit_loss(
        cls,
        track_status: TrackStatus,
        expected_rejoin_pos: int = 1,
        expected_rejoin_gap: float = 5.0,
        green_loss_s: float = DEFAULT_GREEN_LOSS_S,
        vsc_loss_s: float = DEFAULT_VSC_LOSS_S,
        sc_loss_s: float = DEFAULT_SC_LOSS_S,
    ) -> PitLossMetrics:
        if track_status == TrackStatus.SAFETY_CAR:
            current_loss = sc_loss_s
        elif track_status == TrackStatus.VSC:
            current_loss = vsc_loss_s
        else:
            current_loss = green_loss_s

        # Rejoin density penalty if dropping into a tight pack (< 1.5s gap)
        traffic_penalty = 1.2 if expected_rejoin_gap < 1.5 else 0.0

        return PitLossMetrics(
            green_pit_loss_s=green_loss_s,
            vsc_pit_loss_s=vsc_loss_s,
            sc_pit_loss_s=sc_loss_s,
            current_pit_loss_s=current_loss,
            expected_rejoin_position=expected_rejoin_pos,
            expected_rejoin_gap_to_traffic_s=expected_rejoin_gap,
            rejoin_traffic_density_penalty_s=traffic_penalty,
        )
