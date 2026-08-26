"""Unit tests for deterministic strategy calculators."""
import pytest
from datetime import datetime, timezone
from src.core.models import (
    LapObservation,
    TrackStatus,
    TireCompound,
    SubjectDriverState,
    CompetitorState,
    StrategyCandidate,
    PitAction,
    PaceMode,
    StrategyIntent,
)
from src.core.provenance import DataSource
from src.calculators.pace_model import PaceModel
from src.calculators.pit_loss_model import PitLossModel
from src.calculators.traffic_model import TrafficModel
from src.calculators.rules_engine import RulesEngine
from src.calculators.candidate_gen import CandidateGenerator
from src.adapters.synthetic_adapter import SyntheticRaceAdapter


def test_pace_model_filters_unusable_laps():
    """Verify that SC, pit, and unusable laps are excluded from regression."""
    laps = [
        LapObservation(lap_number=1, lap_time_s=95.0, compound=TireCompound.MEDIUM, tyre_age_laps=1, is_pit_out_lap=True),
        LapObservation(lap_number=2, lap_time_s=90.2, compound=TireCompound.MEDIUM, tyre_age_laps=2, usable_for_pace_model=True),
        LapObservation(lap_number=3, lap_time_s=90.3, compound=TireCompound.MEDIUM, tyre_age_laps=3, usable_for_pace_model=True),
        LapObservation(lap_number=4, lap_time_s=115.0, compound=TireCompound.MEDIUM, tyre_age_laps=4, track_status=TrackStatus.SAFETY_CAR),
        LapObservation(lap_number=5, lap_time_s=90.5, compound=TireCompound.MEDIUM, tyre_age_laps=5, usable_for_pace_model=True),
    ]

    clean = PaceModel.filter_clean_laps(laps)
    assert len(clean) == 3
    assert [l.lap_number for l in clean] == [2, 3, 5]

    metrics = PaceModel.calculate_pace_metrics(laps)
    assert metrics.recent_pace_trend_s_per_lap.source == DataSource.DERIVED_MODEL
    assert metrics.degradation_rate_s_per_lap.value >= 0.0


def test_pit_loss_model():
    """Verify pit delta savings under VSC and Safety Car."""
    green = PitLossModel.calculate_pit_loss(TrackStatus.GREEN)
    vsc = PitLossModel.calculate_pit_loss(TrackStatus.VSC)
    sc = PitLossModel.calculate_pit_loss(TrackStatus.SAFETY_CAR)

    assert green.current_pit_loss_s == 21.5
    assert vsc.current_pit_loss_s == 12.5
    assert sc.current_pit_loss_s == 9.5
    assert vsc.current_pit_loss_s < green.current_pit_loss_s
    assert sc.current_pit_loss_s < vsc.current_pit_loss_s


def test_traffic_rejoin_model():
    """Verify projected position and gap calculation when pitting."""
    subject = SubjectDriverState(
        driver="NOR",
        team="McLaren",
        position=1,
        current_compound=TireCompound.MEDIUM,
        stint_length_laps=20,
        total_pit_stops=0,
        used_compounds=[TireCompound.MEDIUM],
        last_lap_time_s=91.0,
    )
    competitors = [
        CompetitorState(
            driver="VER",
            team="Red Bull",
            position=2,
            current_compound=TireCompound.HARD,
            tyre_age_laps=5,
            gap_to_subject_s=-10.0,
        ),
        CompetitorState(
            driver="HAM",
            team="Mercedes",
            position=3,
            current_compound=TireCompound.HARD,
            tyre_age_laps=5,
            gap_to_subject_s=-25.0,
        ),
    ]

    pos, gap = TrafficModel.predict_rejoin(subject, competitors, pit_loss_s=21.5)
    assert pos == 2
    assert gap == pytest.approx(3.5, 0.1)


def test_rules_engine_validation():
    """Verify FIA sporting regulations enforcement and season awareness."""
    subject = SubjectDriverState(
        driver="NOR",
        team="McLaren",
        position=1,
        current_compound=TireCompound.MEDIUM,
        stint_length_laps=56,
        total_pit_stops=0,
        used_compounds=[TireCompound.MEDIUM],
        last_lap_time_s=91.0,
    )

    illegal_stay_out = StrategyCandidate(
        candidate_id="stay_out_baseline",
        ui_label="A",
        pit_action=PitAction.STAY_OUT,
        pace_mode=PaceMode.NORMAL,
        intent=StrategyIntent.BASELINE,
        target_lap=57,
        description="Stay out",
    )
    legal, reason = RulesEngine.is_candidate_legal(
        illegal_stay_out, subject, current_lap=56, total_laps=57,
        dry_compound_rule_exempt=False, season=2024
    )
    assert not legal
    assert "must pit for a second dry compound" in reason


def test_candidate_generator():
    """Verify candidate generator produces distinct options with semantic IDs and UI labels."""
    state = SyntheticRaceAdapter.create_race_state(current_lap=25, stint_length_laps=24)
    candidates = CandidateGenerator.generate_candidates(state)

    assert len(candidates) >= 3
    ui_labels = {c.ui_label for c in candidates}
    assert "A" in ui_labels
    assert "B" in ui_labels
    assert any(c.pit_action == PitAction.BOX_NOW for c in candidates)
    assert any(c.pit_action == PitAction.STAY_OUT for c in candidates)
