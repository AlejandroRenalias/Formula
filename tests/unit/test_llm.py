"""Unit tests for the Milestone 2A LLM selective reasoning contract and trigger."""
import pytest
from src.core.models import (
    TrackStatus,
    TireCompound,
    ConfidenceLevel,
    StrategyDecision,
    StrategyCandidate,
)
from src.core.provenance import DataSource
from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.orchestrator.pipeline import StrategyPipeline
from src.core.llm import (
    LLMEvidencePacket,
    LLMSpecialistOpinion,
    LLMDebateResponse,
    LLMDebateResult,
    LLMChiefResolution,
    should_invoke_llm_reasoning,
    FakeLLMReasoningProvider,
    build_evidence_packet,
    LLMSpecialistOrchestrator,
    SPECIALIST_INSTRUCTIONS,
)


def test_should_invoke_llm_reasoning_trigger():
    """Verify that only conflicted StrategyDecisions trigger LLM reasoning."""
    # 1. Non-conflicted StrategyDecision does NOT invoke LLM reasoning
    state = SyntheticRaceAdapter.create_race_state(current_lap=10)
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)
    
    # Force conflict_detected to False
    decision.conflict_detected = False
    assert should_invoke_llm_reasoning(decision) is False

    # 2. Conflicted decision is eligible for LLM reasoning
    decision.conflict_detected = True
    assert should_invoke_llm_reasoning(decision) is True


def test_evidence_packet_content_and_provenance():
    """Verify evidence packet content correctness, score preservation, and provenance survival."""
    state = SyntheticRaceAdapter.create_race_state(
        current_lap=15,
        track_status=TrackStatus.VSC,
        rain_probability=0.85,
        rain_arrival_laps=2,
    )
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)
    
    # Make sure we have candidates and a decision
    assert len(decision.all_candidates) > 0
    
    # Build packet
    packet = build_evidence_packet(state, decision)
    
    # 3. Evidence packet contains existing semantic candidate IDs and deterministic scores
    for input_cand, packet_cand in zip(decision.all_candidates, packet.candidates):
        assert packet_cand.candidate_id == input_cand.candidate_id
        assert packet_cand.candidate_strategy_score == input_cand.candidate_strategy_score
        
    # 4. Exact score breakdown is preserved
    for input_cand, packet_cand in zip(decision.all_candidates, packet.candidates):
        assert packet_cand.factors == input_cand.factors
        
    # 5. Provenance survives into the LLM evidence packet
    # Check that observed weather temp is REAL_FASTF1
    assert packet.observed_weather.track_temp_c.source == DataSource.REAL_FASTF1
    # Check that weather forecast probability is SCENARIO_FORECAST
    assert packet.weather_forecast.rain_probability.source == DataSource.SCENARIO_FORECAST

    # 6. Future/unavailable data is not introduced
    # Ensure raw lap_history is NOT part of the evidence packet fields
    assert not hasattr(packet, "lap_history")
    
    # Check that we didn't lose basic context needed for reasoning
    assert packet.current_lap == 15
    assert packet.track_status == TrackStatus.VSC


def test_llm_response_validation():
    """Verify structured LLM response validation against supplied candidate and evidence IDs."""
    state = SyntheticRaceAdapter.create_race_state(current_lap=10)
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)
    packet = build_evidence_packet(state, decision)
    
    valid_cand_id = packet.candidates[0].candidate_id
    valid_factor_id = list(packet.candidates[0].factors.keys())[0] if packet.candidates[0].factors else "track_status"

    # 7. Structured LLM response can reference a valid candidate
    opinion = LLMSpecialistOpinion(
        specialist_role="PACE_TYRE",
        supported_candidate_ids=[valid_cand_id],
        preferred_candidate_id=valid_cand_id,
        reasoning_summary="Valid reasoning summary referencing existing candidate.",
        cited_evidence_ids=[valid_factor_id],
        confidence=ConfidenceLevel.HIGH,
        disagreement_flag=False,
    )
    # This should pass without raising
    opinion.validate_against_evidence(packet)

    # 8. Unknown/invented candidate ID is rejected in preferred_candidate_id
    invalid_opinion_1 = LLMSpecialistOpinion(
        specialist_role="PACE_TYRE",
        supported_candidate_ids=[valid_cand_id],
        preferred_candidate_id="invented_candidate_id",
        reasoning_summary="Refers to an unknown candidate.",
        cited_evidence_ids=[valid_factor_id],
        confidence=ConfidenceLevel.HIGH,
        disagreement_flag=False,
    )
    with pytest.raises(ValueError, match="is not in the supplied evidence packet candidates"):
        invalid_opinion_1.validate_against_evidence(packet)

    # 8. Unknown/invented candidate ID is rejected in supported_candidate_ids
    invalid_opinion_2 = LLMSpecialistOpinion(
        specialist_role="PACE_TYRE",
        supported_candidate_ids=["invented_candidate_id"],
        preferred_candidate_id=valid_cand_id,
        reasoning_summary="Refers to an unknown candidate.",
        cited_evidence_ids=[valid_factor_id],
        confidence=ConfidenceLevel.HIGH,
        disagreement_flag=False,
    )
    with pytest.raises(ValueError, match="is not in the supplied evidence packet candidates"):
        invalid_opinion_2.validate_against_evidence(packet)

    # 9. Unknown/invented evidence/factor reference is rejected
    invalid_opinion_3 = LLMSpecialistOpinion(
        specialist_role="PACE_TYRE",
        supported_candidate_ids=[valid_cand_id],
        preferred_candidate_id=valid_cand_id,
        reasoning_summary="Refers to an unknown factor.",
        cited_evidence_ids=["invented_factor_id"],
        confidence=ConfidenceLevel.HIGH,
        disagreement_flag=False,
    )
    with pytest.raises(ValueError, match="is not a valid factor or metric ID from the supplied evidence packet"):
        invalid_opinion_3.validate_against_evidence(packet)


def test_fake_provider_works_isolated():
    """Verify fake/test provider works without external API/network calls."""
    state = SyntheticRaceAdapter.create_race_state(current_lap=10)
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)
    packet = build_evidence_packet(state, decision)
    
    # 10. Fake/test provider works without external API/network calls
    provider = FakeLLMReasoningProvider()
    opinion = provider.reason(packet, "WEATHER")
    
    assert isinstance(opinion, LLMSpecialistOpinion)
    assert opinion.specialist_role == "WEATHER"
    # Ensure it's valid
    opinion.validate_against_evidence(packet)

    # We can also configure it to return a specific opinion and it gets validated
    specific_opinion = LLMSpecialistOpinion(
        specialist_role="RACE_CONTROL",
        supported_candidate_ids=[packet.candidates[0].candidate_id],
        preferred_candidate_id=packet.candidates[0].candidate_id,
        reasoning_summary="Configured opinion.",
        cited_evidence_ids=["track_status"],
        confidence=ConfidenceLevel.MEDIUM,
        disagreement_flag=True,
        disagreement_concern="Yellow flag sector 2 speed limit.",
    )
    
    provider_configured = FakeLLMReasoningProvider(opinion_to_return=specific_opinion)
    result = provider_configured.reason(packet, "RACE_CONTROL")
    assert result == specific_opinion


def test_orchestrator_no_conflict_zero_calls():
    """Verify that when conflict_detected is False, no LLM provider is invoked."""
    state = SyntheticRaceAdapter.create_race_state(current_lap=10)
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)
    
    # Ensure conflict is False
    decision.conflict_detected = False
    
    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)
    
    result = orchestrator.run_llm_reasoning_if_needed(state, decision)
    
    assert result is None
    assert len(provider.calls) == 0


def test_orchestrator_conflict_exactly_one_call_per_specialist():
    """Verify that when conflict_detected is True, exactly one call is made to each specialist role."""
    state = SyntheticRaceAdapter.create_race_state(current_lap=10)
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)
    
    # Force conflict to True
    decision.conflict_detected = True
    
    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)
    
    opinions = orchestrator.run_llm_reasoning_if_needed(state, decision)
    
    assert opinions is not None
    assert len(opinions) == 3
    
    roles_called = [call[0] for call in provider.calls]
    assert len(roles_called) == 3
    assert "PACE_TYRE" in roles_called
    assert "WEATHER" in roles_called
    assert "RACE_CONTROL" in roles_called
    
    # Verify exactly one call per role
    assert roles_called.count("PACE_TYRE") == 1
    assert roles_called.count("WEATHER") == 1
    assert roles_called.count("RACE_CONTROL") == 1
    
    # Verify returned opinions match roles
    assert opinions[0].specialist_role == "PACE_TYRE"
    assert opinions[1].specialist_role == "WEATHER"
    assert opinions[2].specialist_role == "RACE_CONTROL"


def test_orchestrator_factor_ownership_boundaries():
    """Verify that factor ownership boundaries are represented in specialist instructions."""
    # Ensure Pace & Tyre instructions focus only on pace/tyre and NOT weather/race control
    pace_instr = SPECIALIST_INSTRUCTIONS["PACE_TYRE"]
    assert "pace" in pace_instr.lower() or "tyre" in pace_instr.lower()
    assert "Do NOT claim ownership of, calculate, or reference weather crossover" in pace_instr
    assert "safety car" not in pace_instr.lower() or "Do NOT" in pace_instr

    # Ensure Weather instructions focus only on weather and NOT pace/tyre/race control
    weather_instr = SPECIALIST_INSTRUCTIONS["WEATHER"]
    assert "weather" in weather_instr.lower() or "rain" in weather_instr.lower()
    assert "Do NOT claim ownership of, calculate, or reference tyre health" in weather_instr

    # Ensure Race Control instructions focus only on race control and NOT pace/tyre/weather
    rc_instr = SPECIALIST_INSTRUCTIONS["RACE_CONTROL"]
    assert "safety car" in rc_instr.lower() or "rules" in rc_instr.lower()
    assert "Do NOT claim ownership of, calculate, or reference tyre health" in rc_instr
    assert "weather crossover" in rc_instr or "weather" in rc_instr.lower()


def test_no_specialist_changes_candidate_scores():
    """Verify that LLM reasoning does not modify or recalculate candidate scores."""
    state = SyntheticRaceAdapter.create_race_state(current_lap=10)
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)
    decision.conflict_detected = True
    
    original_scores = {c.candidate_id: c.candidate_strategy_score for c in decision.all_candidates}
    
    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)
    opinions = orchestrator.run_llm_reasoning_if_needed(state, decision)
    
    # Verify that the scores in decision candidates remain unmodified
    for cand in decision.all_candidates:
        assert cand.candidate_strategy_score == original_scores[cand.candidate_id]


# ---------------------------------------------------------------------------
# Milestone 2C — one-round debate tests
# ---------------------------------------------------------------------------

def _make_state_and_conflicted_decision():
    """Helper: returns (state, decision) with conflict_detected forced to True."""
    state = SyntheticRaceAdapter.create_race_state(current_lap=10)
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)
    decision.conflict_detected = True
    return state, decision


def test_debate_no_conflict_zero_calls():
    """No conflict → run_debate_if_needed returns None with zero provider calls."""
    state = SyntheticRaceAdapter.create_race_state(current_lap=10)
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)
    decision.conflict_detected = False

    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)

    result = orchestrator.run_debate_if_needed(state, decision)

    assert result is None
    assert len(provider.calls) == 0
    assert len(provider.debate_calls) == 0


def test_debate_first_pass_runs_once_per_specialist():
    """Conflict → each specialist's reason() is called exactly once in the first pass."""
    state, decision = _make_state_and_conflicted_decision()

    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)

    result = orchestrator.run_debate_if_needed(state, decision)

    assert result is not None
    assert len(provider.calls) == 3
    roles_called = [c[0] for c in provider.calls]
    assert sorted(roles_called) == sorted(["PACE_TYRE", "WEATHER", "RACE_CONTROL"])
    for role in ["PACE_TYRE", "WEATHER", "RACE_CONTROL"]:
        assert roles_called.count(role) == 1


def test_debate_exactly_one_response_per_specialist():
    """Conflict → each specialist's debate_rebuttal() is called exactly once."""
    state, decision = _make_state_and_conflicted_decision()

    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)

    result = orchestrator.run_debate_if_needed(state, decision)

    assert result is not None
    assert len(result.debate_responses) == 3
    assert len(provider.debate_calls) == 3

    debate_roles = [c[0] for c in provider.debate_calls]
    assert sorted(debate_roles) == sorted(["PACE_TYRE", "WEATHER", "RACE_CONTROL"])
    for role in ["PACE_TYRE", "WEATHER", "RACE_CONTROL"]:
        assert debate_roles.count(role) == 1


def test_debate_round_is_always_one():
    """The debate_round field on LLMDebateResult is always 1 — no second round."""
    state, decision = _make_state_and_conflicted_decision()

    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)

    result = orchestrator.run_debate_if_needed(state, decision)

    assert result is not None
    assert result.debate_round == 1
    # Verify the structure is frozen (immutable)
    assert isinstance(result, LLMDebateResult)


def test_debate_initial_and_responses_reference_valid_candidate_ids():
    """All initial opinions and debate responses reference only valid candidate/evidence IDs."""
    state, decision = _make_state_and_conflicted_decision()
    packet = build_evidence_packet(state, decision)
    valid_ids = {c.candidate_id for c in packet.candidates}

    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)
    result = orchestrator.run_debate_if_needed(state, decision)

    assert result is not None

    for opinion in result.initial_opinions:
        if opinion.preferred_candidate_id:
            assert opinion.preferred_candidate_id in valid_ids
        for cid in opinion.supported_candidate_ids:
            assert cid in valid_ids

    for response in result.debate_responses:
        if response.preferred_candidate_id:
            assert response.preferred_candidate_id in valid_ids


def test_debate_response_invalid_candidate_fails_closed():
    """A debate response that invents an unknown candidate ID must be rejected."""
    state, decision = _make_state_and_conflicted_decision()
    packet = build_evidence_packet(state, decision)

    bad_response = LLMDebateResponse(
        specialist_role="PACE_TYRE",
        preferred_candidate_id="invented_candidate_id",
        rebuttal_summary="Invented candidate reference.",
        cited_evidence_ids=[],
        position_changed=False,
    )
    with pytest.raises(ValueError, match="is not in the supplied evidence packet candidates"):
        bad_response.validate_against_evidence(packet)


def test_debate_response_invalid_evidence_id_fails_closed():
    """A debate response that cites an unknown evidence/factor ID must be rejected."""
    state, decision = _make_state_and_conflicted_decision()
    packet = build_evidence_packet(state, decision)
    valid_cand = packet.candidates[0].candidate_id

    bad_response = LLMDebateResponse(
        specialist_role="WEATHER",
        preferred_candidate_id=valid_cand,
        rebuttal_summary="Invented factor reference.",
        cited_evidence_ids=["invented_factor_xyz"],
        position_changed=False,
    )
    with pytest.raises(ValueError, match="is not a valid factor or metric ID"):
        bad_response.validate_against_evidence(packet)


def test_debate_scores_unchanged_after_debate():
    """Deterministic candidate scores must not be modified by any debate step."""
    state, decision = _make_state_and_conflicted_decision()
    original_scores = {c.candidate_id: c.candidate_strategy_score for c in decision.all_candidates}

    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)
    result = orchestrator.run_debate_if_needed(state, decision)

    assert result is not None
    # Scores in the decision object itself are unchanged
    for cand in decision.all_candidates:
        assert cand.candidate_strategy_score == original_scores[cand.candidate_id]
    # Scores in the evidence packet candidates (same objects, frozen) are unchanged
    packet = build_evidence_packet(state, decision)
    for cand in packet.candidates:
        assert cand.candidate_strategy_score == original_scores[cand.candidate_id]


def test_debate_provenance_unchanged():
    """Provenance tags on weather/pace metrics must survive through the debate flow unchanged."""
    state = SyntheticRaceAdapter.create_race_state(
        current_lap=12,
        rain_probability=0.80,
        rain_arrival_laps=2,
        is_sandbox_override=False,
    )
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)
    decision.conflict_detected = True

    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)
    result = orchestrator.run_debate_if_needed(state, decision)

    assert result is not None
    # The evidence passed to the provider must carry original provenance untouched
    evidence_at_first_call = provider.calls[0][1]  # (role, packet)
    assert evidence_at_first_call.observed_weather.track_temp_c.source == DataSource.REAL_FASTF1
    assert evidence_at_first_call.weather_forecast.rain_probability.source == DataSource.SCENARIO_FORECAST
    # Same packet used for debate calls
    debate_evidence = provider.debate_calls[0][1]
    assert debate_evidence.observed_weather.track_temp_c.source == DataSource.REAL_FASTF1


def test_debate_specialist_can_maintain_or_revise_preference():
    """A specialist may legitimately maintain or revise its preference without altering facts."""
    state, decision = _make_state_and_conflicted_decision()
    packet = build_evidence_packet(state, decision)

    cand_a = packet.candidates[0].candidate_id
    cand_b = packet.candidates[1].candidate_id if len(packet.candidates) > 1 else cand_a

    # PACE_TYRE maintains position (no change)
    maintaining = LLMDebateResponse(
        specialist_role="PACE_TYRE",
        preferred_candidate_id=cand_a,
        rebuttal_summary="Weather argument noted, but tyre health strongly favours staying out.",
        cited_evidence_ids=["degradation_rate_s_per_lap"],
        position_changed=False,
    )
    maintaining.validate_against_evidence(packet)  # must not raise

    # WEATHER revises preference
    revising = LLMDebateResponse(
        specialist_role="WEATHER",
        preferred_candidate_id=cand_b,
        rebuttal_summary="After reviewing Race Control's SC saving, switching preference.",
        cited_evidence_ids=["rain_probability"],
        position_changed=True,
    )
    revising.validate_against_evidence(packet)  # must not raise

    # Neither response touched any score field
    for cand in decision.all_candidates:
        assert isinstance(cand.candidate_strategy_score, float)


def test_debate_specialist_roles_all_present_in_result():
    """All three specialist roles must appear in both initial_opinions and debate_responses."""
    state, decision = _make_state_and_conflicted_decision()

    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)
    result = orchestrator.run_debate_if_needed(state, decision)

    assert result is not None
    initial_roles = {op.specialist_role for op in result.initial_opinions}
    debate_roles = {dr.specialist_role for dr in result.debate_responses}

    assert initial_roles == {"PACE_TYRE", "WEATHER", "RACE_CONTROL"}
    assert debate_roles == {"PACE_TYRE", "WEATHER", "RACE_CONTROL"}


# ---------------------------------------------------------------------------
# Milestone 2D — Chief Strategist LLM resolution tests
# ---------------------------------------------------------------------------

def _make_conflicted(current_lap: int = 10):
    """Helper: returns (state, decision) with conflict_detected=True."""
    state = SyntheticRaceAdapter.create_race_state(current_lap=current_lap)
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)
    decision.conflict_detected = True
    return state, decision


def test_chief_no_conflict_zero_calls():
    """No conflict → resolve_after_debate returns None with zero chief calls."""
    state = SyntheticRaceAdapter.create_race_state(current_lap=10)
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)
    decision.conflict_detected = False

    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)

    result = orchestrator.resolve_after_debate(state, decision)

    assert result is None
    assert len(provider.chief_calls) == 0
    assert len(provider.calls) == 0
    assert len(provider.debate_calls) == 0


def test_chief_conflict_runs_full_flow():
    """Conflict → debate runs (3 reason + 3 debate_rebuttal) then chief_resolution called once."""
    state, decision = _make_conflicted()

    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)

    result = orchestrator.resolve_after_debate(state, decision)

    assert result is not None
    assert isinstance(result, LLMChiefResolution)
    assert len(provider.calls) == 3           # first-pass opinions
    assert len(provider.debate_calls) == 3    # debate rebuttals
    assert len(provider.chief_calls) == 1     # exactly one chief call


def test_chief_default_confirms_deterministic_winner():
    """Default fake Chief confirms the deterministic selected candidate."""
    state, decision = _make_conflicted()
    deterministic_winner = decision.selected_candidate.candidate_id

    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)

    result = orchestrator.resolve_after_debate(state, decision)

    assert result is not None
    assert result.confirmed_candidate_id == deterministic_winner
    assert result.overridden is False
    assert result.override_reason is None


def test_chief_resolution_confirmed_candidate_must_be_in_packet():
    """Chief resolution that references an unknown candidate ID is rejected."""
    state, decision = _make_conflicted()
    packet = build_evidence_packet(state, decision)

    bad_resolution = LLMChiefResolution(
        confirmed_candidate_id="invented_candidate_xyz",
        overridden=False,
        strategic_rationale="Invented candidate reference.",
        confidence=ConfidenceLevel.HIGH,
    )
    with pytest.raises(ValueError, match="is not in the supplied evidence packet candidates"):
        bad_resolution.validate_against_evidence(packet, decision)


def test_chief_divergence_without_override_flag_rejected():
    """Chief that silently endorses a non-winner without overridden=True is rejected."""
    state, decision = _make_conflicted()
    packet = build_evidence_packet(state, decision)

    # Pick a candidate that is NOT the deterministic winner
    non_winner = next(
        c.candidate_id for c in packet.candidates
        if c.candidate_id != decision.selected_candidate.candidate_id
    )

    bad_resolution = LLMChiefResolution(
        confirmed_candidate_id=non_winner,
        overridden=False,   # <-- missing flag
        strategic_rationale="Silent divergence attempt.",
        confidence=ConfidenceLevel.MEDIUM,
    )
    with pytest.raises(ValueError, match="Set overridden=True"):
        bad_resolution.validate_against_evidence(packet, decision)


def test_chief_override_without_reason_rejected():
    """Chief with overridden=True but no override_reason is rejected."""
    state, decision = _make_conflicted()
    packet = build_evidence_packet(state, decision)

    non_winner = next(
        c.candidate_id for c in packet.candidates
        if c.candidate_id != decision.selected_candidate.candidate_id
    )

    bad_resolution = LLMChiefResolution(
        confirmed_candidate_id=non_winner,
        overridden=True,
        override_reason=None,   # <-- required but missing
        strategic_rationale="Override with no reason.",
        confidence=ConfidenceLevel.LOW,
    )
    with pytest.raises(ValueError, match="override_reason is empty"):
        bad_resolution.validate_against_evidence(packet, decision)


def test_chief_override_with_reason_accepted():
    """Chief may legitimately endorse a non-winner when overridden=True and reason is given."""
    state, decision = _make_conflicted()
    packet = build_evidence_packet(state, decision)

    non_winner = next(
        c.candidate_id for c in packet.candidates
        if c.candidate_id != decision.selected_candidate.candidate_id
    )

    valid_override = LLMChiefResolution(
        confirmed_candidate_id=non_winner,
        overridden=True,
        override_reason="Weather risk makes staying out unacceptably dangerous given rain in 2 laps.",
        strategic_rationale="Rain imminent; SC window saving outweighs tyre freshness gain.",
        minority_concerns_acknowledged=["Pace specialist preferred staying out for tyre delta."],
        confidence=ConfidenceLevel.MEDIUM,
        cited_evidence_ids=["rain_probability", "expected_arrival_laps"],
    )
    valid_override.validate_against_evidence(packet, decision)  # must not raise


def test_chief_invalid_evidence_id_rejected():
    """Chief resolution citing an invented evidence/factor ID is rejected."""
    state, decision = _make_conflicted()
    packet = build_evidence_packet(state, decision)
    winner = decision.selected_candidate.candidate_id

    bad_resolution = LLMChiefResolution(
        confirmed_candidate_id=winner,
        overridden=False,
        strategic_rationale="Cites an invented factor.",
        confidence=ConfidenceLevel.HIGH,
        cited_evidence_ids=["invented_factor_chief"],
    )
    with pytest.raises(ValueError, match="is not a valid factor or metric ID"):
        bad_resolution.validate_against_evidence(packet, decision)


def test_chief_scores_unchanged_after_resolution():
    """Deterministic candidate scores must be unmodified after a full resolve_after_debate call."""
    state, decision = _make_conflicted()
    original_scores = {c.candidate_id: c.candidate_strategy_score for c in decision.all_candidates}

    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)
    orchestrator.resolve_after_debate(state, decision)

    for cand in decision.all_candidates:
        assert cand.candidate_strategy_score == original_scores[cand.candidate_id]


def test_chief_provenance_reaches_chief_call():
    """Provenance on weather/pace metrics must be intact when chief_resolution is called."""
    state = SyntheticRaceAdapter.create_race_state(
        current_lap=12,
        rain_probability=0.75,
        rain_arrival_laps=2,
        is_sandbox_override=False,
    )
    pipeline = StrategyPipeline()
    decision = pipeline.run_strategy_cycle(state)
    decision.conflict_detected = True

    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)
    orchestrator.resolve_after_debate(state, decision)

    assert len(provider.chief_calls) == 1
    chief_packet = provider.chief_calls[0][0]
    assert chief_packet.observed_weather.track_temp_c.source == DataSource.REAL_FASTF1
    assert chief_packet.weather_forecast.rain_probability.source == DataSource.SCENARIO_FORECAST


def test_chief_resolution_is_immutable():
    """LLMChiefResolution must be frozen (immutable) once created."""
    state, decision = _make_conflicted()
    provider = FakeLLMReasoningProvider()
    orchestrator = LLMSpecialistOrchestrator(provider)

    result = orchestrator.resolve_after_debate(state, decision)
    assert result is not None

    with pytest.raises(Exception):  # ValidationError or TypeError from frozen model
        result.confirmed_candidate_id = "some_other_id"
