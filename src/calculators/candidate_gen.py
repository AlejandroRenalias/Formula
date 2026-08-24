"""Deterministic Candidate Generator for F1 Pit Wall Strategy System."""
from typing import List, Optional
from src.core.models import (
    RaceState,
    StrategyCandidate,
    PitAction,
    PaceMode,
    StrategyIntent,
    TireCompound,
    TrackStatus,
)
from src.calculators.weather_model import WeatherModel


class CandidateGenerator:
    """Generates 2 to 4 distinct, legal, and context-relevant strategy candidates with stable semantic IDs."""

    @classmethod
    def generate_candidates(cls, state: RaceState) -> List[StrategyCandidate]:
        candidates: List[StrategyCandidate] = []
        subject = state.subject_driver
        current_comp = subject.current_compound
        stint_len = subject.stint_length_laps

        # 1. Determine optimal next compound
        optimal_weather_comp, _, _ = WeatherModel.evaluate_crossover(
            state.observed_weather, state.weather_forecast, state.current_lap
        )
        
        if optimal_weather_comp in (TireCompound.INTERMEDIATE, TireCompound.WET):
            next_compound = optimal_weather_comp
        else:
            # Dry compound selection: choose a legal dry compound not currently used if 1-stop
            used_dry = {
                c for c in subject.used_compounds
                if c in (TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD)
            }
            if current_comp == TireCompound.SOFT:
                next_compound = TireCompound.HARD if TireCompound.HARD not in used_dry else TireCompound.MEDIUM
            elif current_comp == TireCompound.MEDIUM:
                next_compound = TireCompound.HARD
            else:
                next_compound = TireCompound.MEDIUM

        # Identify nearest rival for intent targeting
        ahead = [c for c in state.competitors if c.gap_to_subject_s > 0]
        behind = [c for c in state.competitors if c.gap_to_subject_s < 0]
        closest_ahead_driver = min(ahead, key=lambda c: c.gap_to_subject_s).driver if ahead else None
        closest_behind_driver = max(behind, key=lambda c: c.gap_to_subject_s).driver if behind else None

        # Candidate A: Baseline / Stay Out Normal
        candidates.append(
            StrategyCandidate(
                candidate_id="stay_out_baseline",
                ui_label="A",
                pit_action=PitAction.STAY_OUT,
                pace_mode=PaceMode.NORMAL,
                target_compound=None,
                intent=StrategyIntent.BASELINE,
                target_lap=state.current_lap + 1,
                description=f"Stay out on current {current_comp.value} ({stint_len} laps old) at normal pace.",
                estimated_time_delta_s=0.0,
                candidate_strategy_score=0.0,
            )
        )

        # Candidate B: Box Now (Pit Stop)
        # Determine intent and stable ID for pitting now
        if state.track_status in (TrackStatus.SAFETY_CAR, TrackStatus.VSC):
            pit_intent = StrategyIntent.SAFETY_CAR_OPPORTUNITY
            candidate_id = f"box_now_{state.track_status.value.lower()}_{next_compound.value.lower()}"
            target_driver = None
            desc = f"Box now under {state.track_status.value} for fresh {next_compound.value} (saving {state.pit_loss.green_pit_loss_s - state.pit_loss.current_pit_loss_s:.1f}s pit loss)."
        elif optimal_weather_comp in (TireCompound.INTERMEDIATE, TireCompound.WET):
            pit_intent = StrategyIntent.WEATHER_CROSSOVER
            candidate_id = f"box_now_{next_compound.value.lower()}_crossover"
            target_driver = None
            desc = f"Box now for {next_compound.value} to exploit wet crossover window."
        elif stint_len >= 18:
            pit_intent = StrategyIntent.UNDERCUT
            candidate_id = f"box_now_undercut_{next_compound.value.lower()}"
            target_driver = closest_ahead_driver
            desc = f"Box now for fresh {next_compound.value} to undercut {closest_ahead_driver or 'rival'}."
        else:
            pit_intent = StrategyIntent.COVER
            candidate_id = f"box_now_cover_{next_compound.value.lower()}"
            target_driver = closest_behind_driver
            desc = f"Box now for fresh {next_compound.value} to cover {closest_behind_driver or 'rival'}."

        candidates.append(
            StrategyCandidate(
                candidate_id=candidate_id,
                ui_label="B",
                pit_action=PitAction.BOX_NOW,
                pace_mode=PaceMode.NORMAL,
                target_compound=next_compound,
                intent=pit_intent,
                target_driver=target_driver,
                target_lap=state.current_lap,
                description=desc,
                estimated_time_delta_s=0.0,
                candidate_strategy_score=0.0,
            )
        )

        # Candidate C: Stay Out & Push (Overcut attack)
        candidates.append(
            StrategyCandidate(
                candidate_id="stay_out_push_overcut",
                ui_label="C",
                pit_action=PitAction.STAY_OUT,
                pace_mode=PaceMode.PUSH,
                target_compound=None,
                intent=StrategyIntent.OVERCUT,
                target_driver=closest_ahead_driver,
                target_lap=state.current_lap + 2,
                description=f"Stay out and push at maximum pace on {current_comp.value} to build gap before pitting.",
                estimated_time_delta_s=0.0,
                candidate_strategy_score=0.0,
            )
        )

        # Candidate D: Stay Out & Conserve (Extend Stint / Wait for Rain or SC)
        candidates.append(
            StrategyCandidate(
                candidate_id="stay_out_conserve_extend",
                ui_label="D",
                pit_action=PitAction.STAY_OUT,
                pace_mode=PaceMode.CONSERVE,
                target_compound=None,
                intent=StrategyIntent.EXTEND,
                target_lap=state.current_lap + 5,
                description="Stay out and conserve tyres to stretch stint window.",
                estimated_time_delta_s=0.0,
                candidate_strategy_score=0.0,
            )
        )

        return candidates
