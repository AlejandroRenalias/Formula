"""Milestone 3A tests for the deterministic legality boundary."""
import pytest

from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.core.llm import FakeLLMReasoningProvider, LLMSpecialistOrchestrator
from src.core.models import (
    PitAction,
    PaceMode,
    StrategyCandidate,
    StrategyIntent,
    TireCompound,
)
from src.calculators.rules_engine import NoLegalCandidatesError, RulesEngine
from src.orchestrator.pipeline import StrategyPipeline


def _illegal_stay_out():
    return StrategyCandidate(
        candidate_id="illegal_stay_out",
        pit_action=PitAction.STAY_OUT,
        pace_mode=PaceMode.NORMAL,
        intent=StrategyIntent.BASELINE,
        target_lap=57,
        description="Illegal final-lap stay out.",
    )


def test_legal_candidates_preserve_normal_pipeline_behavior():
    state = SyntheticRaceAdapter.create_race_state(current_lap=25)
    decision = StrategyPipeline().run_strategy_cycle(state)

    assert decision.all_candidates
    assert decision.rejected_candidates == {}
    assert decision.selected_candidate.candidate_id in {
        candidate.candidate_id for candidate in decision.all_candidates
    }


def test_illegal_candidate_is_filtered_before_scoring_and_llm(monkeypatch):
    state = SyntheticRaceAdapter.create_race_state(current_lap=56, total_laps=57)
    original_generator = __import__(
        "src.orchestrator.pipeline", fromlist=["CandidateGenerator"]
    ).CandidateGenerator
    monkeypatch.setattr(
        original_generator,
        "generate_candidates",
        lambda state: [_illegal_stay_out()],
    )

    provider = FakeLLMReasoningProvider()
    with pytest.raises(NoLegalCandidatesError) as error:
        StrategyPipeline(
            llm_orchestrator=LLMSpecialistOrchestrator(provider)
        ).run_strategy_cycle(state)

    assert "illegal_stay_out" in error.value.rejected_candidates
    assert "must pit for a second dry compound" in error.value.rejected_candidates["illegal_stay_out"]
    assert not provider.calls
    assert not provider.debate_calls
    assert not provider.chief_calls


def test_mixed_candidates_only_legal_candidates_reach_strategy_and_llm(monkeypatch):
    state = SyntheticRaceAdapter.create_race_state(current_lap=56, total_laps=57)
    generated = [
        _illegal_stay_out(),
        StrategyCandidate(
            candidate_id="legal_box",
            pit_action=PitAction.BOX_NOW,
            pace_mode=PaceMode.NORMAL,
            target_compound=state.subject_driver.current_compound,
            intent=StrategyIntent.BASELINE,
            target_lap=56,
            description="Legal pit candidate.",
        ),
    ]
    pipeline_module = __import__("src.orchestrator.pipeline", fromlist=["CandidateGenerator"])
    monkeypatch.setattr(pipeline_module.CandidateGenerator, "generate_candidates", lambda state: generated)
    seen_by_conflict_detector = []
    monkeypatch.setattr(
        pipeline_module.ConflictDetector,
        "should_trigger_debate",
        lambda candidates, reports: (
            seen_by_conflict_detector.extend(candidate.candidate_id for candidate in candidates)
            or (True, "test conflict")
        ),
    )

    provider = FakeLLMReasoningProvider()
    decision = StrategyPipeline(
        llm_orchestrator=LLMSpecialistOrchestrator(provider)
    ).run_strategy_cycle(state)

    assert [candidate.candidate_id for candidate in decision.all_candidates] == ["legal_box"]
    assert decision.selected_candidate.candidate_id == "legal_box"
    assert list(decision.rejected_candidates) == ["illegal_stay_out"]
    assert "must pit for a second dry compound" in decision.rejected_candidates["illegal_stay_out"]
    assert seen_by_conflict_detector == ["legal_box"]
    assert all(
        [candidate.candidate_id for candidate in call[1].candidates] == ["legal_box"]
        for call in provider.calls
    )
    assert decision.llm_chief_resolution is not None


def test_zero_legal_candidates_fails_with_diagnostics_and_no_scoring(monkeypatch):
    state = SyntheticRaceAdapter.create_race_state(current_lap=56, total_laps=57)
    candidates = [_illegal_stay_out(), _illegal_stay_out().model_copy(update={"candidate_id": "illegal_2"})]
    pipeline_module = __import__("src.orchestrator.pipeline", fromlist=["CandidateGenerator"])
    monkeypatch.setattr(pipeline_module.CandidateGenerator, "generate_candidates", lambda state: candidates)

    with pytest.raises(NoLegalCandidatesError, match="lap 56") as error:
        StrategyPipeline().run_strategy_cycle(state)

    assert set(error.value.rejected_candidates) == {"illegal_stay_out", "illegal_2"}


def test_current_rainfall_does_not_grant_dry_compound_exemption():
    state = SyntheticRaceAdapter.create_race_state(
        current_lap=56,
        total_laps=57,
        is_raining=True,
        used_compounds=[],
    )

    result = RulesEngine.validate_candidates([_illegal_stay_out()], state)

    assert not result.legal_candidates
    assert "illegal_stay_out" in result.rejected_candidates


def test_intermediate_or_wet_usage_grants_supported_exemption():
    state = SyntheticRaceAdapter.create_race_state(
        current_lap=56,
        total_laps=57,
        is_raining=False,
        used_compounds=[
            TireCompound.MEDIUM,
            TireCompound.INTERMEDIATE,
        ],
    )

    result = RulesEngine.validate_candidates([_illegal_stay_out()], state)

    assert result.legal_candidates == [_illegal_stay_out()]
    assert result.rejected_candidates == {}


def test_pipeline_uses_compound_history_not_current_rainfall(monkeypatch):
    state = SyntheticRaceAdapter.create_race_state(
        current_lap=56,
        total_laps=57,
        is_raining=True,
        used_compounds=[],
    )
    pipeline_module = __import__("src.orchestrator.pipeline", fromlist=["CandidateGenerator"])
    monkeypatch.setattr(
        pipeline_module.CandidateGenerator,
        "generate_candidates",
        lambda state: [_illegal_stay_out()],
    )

    with pytest.raises(NoLegalCandidatesError):
        StrategyPipeline().run_strategy_cycle(state)
