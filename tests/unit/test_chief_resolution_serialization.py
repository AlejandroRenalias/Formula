"""Serialization tests for the typed Milestone 2D resolution field."""
import pytest

from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.core.llm import LLMChiefResolution, build_evidence_packet
from src.orchestrator.pipeline import StrategyPipeline


def _decision_with_resolution():
    state = SyntheticRaceAdapter.create_race_state(current_lap=10)
    decision = StrategyPipeline().run_strategy_cycle(state)
    packet = build_evidence_packet(state, decision)
    resolution = LLMChiefResolution(
        confirmed_candidate_id=decision.selected_candidate.candidate_id,
        strategic_rationale="Confirmed deterministic strategy.",
        confidence="HIGH",
        cited_evidence_ids=["track_status"],
    )
    resolution.validate_against_evidence(packet, decision)
    return decision.model_copy(update={"llm_chief_resolution": resolution})


def test_chief_resolution_json_round_trip_preserves_type_and_values():
    decision = _decision_with_resolution()
    restored = type(decision).model_validate_json(decision.model_dump_json())

    assert isinstance(restored.llm_chief_resolution, LLMChiefResolution)
    assert restored.llm_chief_resolution == decision.llm_chief_resolution
    assert restored.selected_candidate == decision.selected_candidate
    assert restored.all_candidates == decision.all_candidates
    assert restored.score_breakdown == decision.score_breakdown
    assert restored.specialist_evaluations == decision.specialist_evaluations


def test_strategy_decision_rejects_arbitrary_chief_resolution_value():
    decision = _decision_with_resolution()
    payload = decision.model_dump()
    payload["llm_chief_resolution"] = {"not": "a chief resolution"}

    with pytest.raises(Exception):
        type(decision).model_validate(payload)


def test_strategy_decision_preserves_chief_validation_rules():
    decision = _decision_with_resolution()
    payload = decision.model_dump()
    payload["llm_chief_resolution"]["confirmed_candidate_id"] = "invented_candidate"

    restored = type(decision).model_validate(payload)
    assert isinstance(restored.llm_chief_resolution, LLMChiefResolution)

    with pytest.raises(ValueError, match="is not in the supplied evidence packet candidates"):
        restored.llm_chief_resolution.validate_against_evidence(
            build_evidence_packet(
                SyntheticRaceAdapter.create_race_state(current_lap=10),
                StrategyPipeline().run_strategy_cycle(
                    SyntheticRaceAdapter.create_race_state(current_lap=10)
                ),
            ),
            decision,
        )
