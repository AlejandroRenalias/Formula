"""Production-boundary tests for Milestone 2D LLM Chief integration."""
from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.core.llm import (
    FakeLLMReasoningProvider,
    LLMChiefResolution,
    LLMSpecialistOrchestrator,
)
from src.orchestrator.pipeline import StrategyPipeline


def _pipeline_with_provider(provider):
    return StrategyPipeline(llm_orchestrator=LLMSpecialistOrchestrator(provider))


def _force_conflict(monkeypatch, value=True):
    monkeypatch.setattr(
        "src.orchestrator.pipeline.ConflictDetector.should_trigger_debate",
        lambda candidates, reports: (value, "test conflict" if value else "test clear"),
    )


def test_clear_pipeline_path_has_no_llm_resolution_or_calls(monkeypatch):
    _force_conflict(monkeypatch, False)
    provider = FakeLLMReasoningProvider()
    state = SyntheticRaceAdapter.create_race_state(current_lap=10)

    decision = _pipeline_with_provider(provider).run_strategy_cycle(state)

    assert decision.llm_chief_resolution is None
    assert not provider.calls
    assert not provider.debate_calls
    assert not provider.chief_calls


def test_conflict_pipeline_confirms_without_mutating_deterministic_result(monkeypatch):
    _force_conflict(monkeypatch, True)
    provider = FakeLLMReasoningProvider()
    state = SyntheticRaceAdapter.create_race_state(current_lap=10)
    original_state = state.model_dump()
    baseline = StrategyPipeline().run_strategy_cycle(state)

    decision = _pipeline_with_provider(provider).run_strategy_cycle(state)

    assert decision.llm_chief_resolution is not None
    assert decision.llm_chief_resolution.confirmed_candidate_id == decision.selected_candidate.candidate_id
    assert len(provider.calls) == 3
    assert len(provider.debate_calls) == 3
    assert len(provider.chief_calls) == 1
    assert decision.selected_candidate.candidate_id == baseline.selected_candidate.candidate_id
    assert [c.model_dump() for c in decision.all_candidates] == [c.model_dump() for c in baseline.all_candidates]
    assert state.model_dump() == original_state


class _OverrideProvider(FakeLLMReasoningProvider):
    def chief_resolution(self, evidence_packet, decision, debate_result):
        other = next(c.candidate_id for c in evidence_packet.candidates if c.candidate_id != decision.selected_candidate.candidate_id)
        return LLMChiefResolution(
            confirmed_candidate_id=other,
            overridden=True,
            override_reason="Explicit test override reason.",
            strategic_rationale="Explicit test Chief rationale.",
            confidence="MEDIUM",
            cited_evidence_ids=["track_status"],
        )


def test_conflict_pipeline_keeps_override_separate(monkeypatch):
    _force_conflict(monkeypatch, True)
    state = SyntheticRaceAdapter.create_race_state(current_lap=10)
    original_state = state.model_dump()
    provider = _OverrideProvider()
    baseline = StrategyPipeline().run_strategy_cycle(state)
    original_candidates = [candidate.model_dump() for candidate in baseline.all_candidates]
    original_breakdown = baseline.score_breakdown.copy()
    original_evaluations = [report.model_dump() for report in baseline.specialist_evaluations]
    original_winner = baseline.selected_candidate.candidate_id

    decision = _pipeline_with_provider(provider).run_strategy_cycle(state)
    resolution = decision.llm_chief_resolution

    assert resolution is not None
    assert resolution.overridden is True
    assert resolution.confirmed_candidate_id != decision.selected_candidate.candidate_id
    assert resolution.override_reason
    assert decision.selected_candidate.candidate_id == original_winner
    assert [candidate.model_dump() for candidate in decision.all_candidates] == original_candidates
    assert decision.score_breakdown == original_breakdown
    assert [report.model_dump() for report in decision.specialist_evaluations] == original_evaluations
    assert state.model_dump() == original_state
