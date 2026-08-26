"""Selective LLM reasoning contracts, triggers, and provider abstractions."""
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field, ConfigDict

from src.core.models import (
    TrackStatus,
    SubjectDriverState,
    CompetitorState,
    WeatherForecast,
    DerivedPaceMetrics,
    PitLossMetrics,
    StrategyCandidate,
    AgentReport,
    ObservedWeather,
    ConfidenceLevel,
    StrategyDecision,
    LLMChiefResolution,
)


# ---------------------------------------------------------------------------
# Evidence packet (immutable input to every LLM call)
# ---------------------------------------------------------------------------

class LLMEvidencePacket(BaseModel):
    """
    Immutable structured evidence supplied to an LLM specialist.
    Contains only precomputed, derived, and current snapshot data.
    No raw lap history; no future data beyond the knowledge cutoff.
    """
    model_config = ConfigDict(frozen=True)

    current_lap: int
    total_laps: int
    track_status: TrackStatus
    subject_driver: SubjectDriverState
    competitors: List[CompetitorState]
    observed_weather: ObservedWeather
    weather_forecast: WeatherForecast
    derived_pace: DerivedPaceMetrics
    pit_loss: PitLossMetrics

    candidates: List[StrategyCandidate]
    specialist_evaluations: List[AgentReport]

    conflict_detected: bool
    conflict_summary: Optional[str] = None


# ---------------------------------------------------------------------------
# Shared validation helper — keeps valid-ID sets consistent
# ---------------------------------------------------------------------------

def _valid_evidence_ids(evidence: LLMEvidencePacket) -> set:
    ids: set = set()
    for c in evidence.candidates:
        ids.update(c.factors.keys())
    for report in evidence.specialist_evaluations:
        for factors in report.candidate_factors.values():
            ids.update(factors.keys())
    ids.update([
        "track_temp_c", "air_temp_c", "rainfall", "humidity_pct", "wind_speed_kmh",
        "rain_probability", "expected_arrival_laps", "intensity",
        "recent_pace_trend_s_per_lap", "degradation_rate_s_per_lap", "clean_air_potential_lap_time_s",
        "green_pit_loss_s", "vsc_pit_loss_s", "sc_pit_loss_s", "current_pit_loss_s",
        "expected_rejoin_position", "expected_rejoin_gap_to_traffic_s", "rejoin_traffic_density_penalty_s",
        "track_status",
    ])
    return ids


# ---------------------------------------------------------------------------
# First-pass opinion contract (Milestone 2A/2B)
# ---------------------------------------------------------------------------

class LLMSpecialistOpinion(BaseModel):
    """
    Strict structured first-pass response from an LLM specialist.
    """
    specialist_role: str
    supported_candidate_ids: List[str]
    preferred_candidate_id: Optional[str] = None
    reasoning_summary: str
    cited_evidence_ids: List[str]
    confidence: ConfidenceLevel
    disagreement_flag: bool = False
    disagreement_concern: Optional[str] = None
    uncertainty: Optional[str] = None

    def validate_against_evidence(self, evidence: LLMEvidencePacket) -> None:
        """
        Validates that all referenced candidate IDs and evidence/factor IDs
        exist in the supplied evidence packet.
        Raises ValueError if any unknown/invented IDs are referenced.
        """
        valid_candidate_ids = {c.candidate_id for c in evidence.candidates}

        if self.preferred_candidate_id is not None:
            if self.preferred_candidate_id not in valid_candidate_ids:
                raise ValueError(
                    f"Preferred candidate ID '{self.preferred_candidate_id}' is not in the supplied evidence packet candidates."
                )

        for cid in self.supported_candidate_ids:
            if cid not in valid_candidate_ids:
                raise ValueError(
                    f"Supported candidate ID '{cid}' is not in the supplied evidence packet candidates."
                )

        valid_ids = _valid_evidence_ids(evidence)
        for ref in self.cited_evidence_ids:
            if ref not in valid_ids:
                raise ValueError(
                    f"Cited evidence/factor ID '{ref}' is not a valid factor or metric ID from the supplied evidence packet."
                )


# ---------------------------------------------------------------------------
# Debate contracts (Milestone 2C)
# ---------------------------------------------------------------------------

class LLMDebateResponse(BaseModel):
    """
    One specialist's structured response in the single debate round.
    Contains a rebuttal / revised position after seeing peer initial opinions.
    Every candidate/evidence reference must validate against the original LLMEvidencePacket.
    A specialist must not introduce evidence that only another specialist mentioned.
    """
    specialist_role: str
    preferred_candidate_id: Optional[str] = None
    rebuttal_summary: str
    cited_evidence_ids: List[str]
    position_changed: bool = False
    disagreement_flag: bool = False
    disagreement_concern: Optional[str] = None
    uncertainty: Optional[str] = None

    def validate_against_evidence(self, evidence: LLMEvidencePacket) -> None:
        """
        Validates all candidate and evidence/factor IDs referenced in this debate response.
        Raises ValueError on any unknown/invented reference.
        """
        valid_candidate_ids = {c.candidate_id for c in evidence.candidates}

        if self.preferred_candidate_id is not None:
            if self.preferred_candidate_id not in valid_candidate_ids:
                raise ValueError(
                    f"Debate preferred candidate ID '{self.preferred_candidate_id}' is not in the supplied evidence packet candidates."
                )

        valid_ids = _valid_evidence_ids(evidence)
        for ref in self.cited_evidence_ids:
            if ref not in valid_ids:
                raise ValueError(
                    f"Debate cited evidence ID '{ref}' is not a valid factor or metric ID from the supplied evidence packet."
                )


class LLMDebateResult(BaseModel):
    """
    Structured result of the one-round selective specialist debate.
    Immutable — deterministic facts and scores are untouched.
    debate_round is always 1; no further rounds are ever run.
    """
    model_config = ConfigDict(frozen=True)

    initial_opinions: List[LLMSpecialistOpinion]
    debate_responses: List[LLMDebateResponse]
    debate_round: int = Field(default=1, description="Always 1 — no further rounds permitted.")


# ---------------------------------------------------------------------------
# Selective invocation trigger (Milestone 2A)
# ---------------------------------------------------------------------------

def should_invoke_llm_reasoning(decision: StrategyDecision) -> bool:
    """
    Deterministic helper deciding whether LLM reasoning should be invoked.
    Primary trigger: decision.conflict_detected.
    """
    return decision.conflict_detected


# ---------------------------------------------------------------------------
# Provider abstraction (Milestone 2A extended in 2C)
# ---------------------------------------------------------------------------

class LLMReasoningProvider(ABC):
    """Abstract interface for future LLM model providers."""

    @abstractmethod
    def reason(self, evidence_packet: LLMEvidencePacket, specialist_role: str) -> LLMSpecialistOpinion:
        """First-pass independent reasoning for a specialist role."""
        pass

    @abstractmethod
    def debate_rebuttal(
        self,
        evidence_packet: LLMEvidencePacket,
        specialist_role: str,
        own_initial_opinion: LLMSpecialistOpinion,
        peer_opinions: List[LLMSpecialistOpinion],
    ) -> LLMDebateResponse:
        """
        One-round debate response.
        The specialist sees the same immutable evidence plus peer initial opinions.
        Must NOT recalculate scores, invent candidates/factors, or cross factor-ownership boundaries.
        """
        pass

    @abstractmethod
    def chief_resolution(
        self,
        evidence_packet: LLMEvidencePacket,
        decision: StrategyDecision,
        debate_result: LLMDebateResult,
    ) -> LLMChiefResolution:
        """
        Chief Strategist resolution after the one-round debate (Milestone 2D).
        The Chief reads the deterministic decision and completed debate, then confirms
        or explicitly flags concern about the deterministic winner.
        Must NOT invent candidates, modify scores, or diverge silently from the
        deterministic ranking without overridden=True and a populated override_reason.
        """
        pass


class FakeLLMReasoningProvider(LLMReasoningProvider):
    """A fake provider for testing — no external API calls, no network, no API keys."""

    def __init__(
        self,
        opinions_to_return: Optional[Dict[str, LLMSpecialistOpinion]] = None,
        opinion_to_return: Optional[LLMSpecialistOpinion] = None,
        debate_responses_to_return: Optional[Dict[str, LLMDebateResponse]] = None,
        chief_resolution_to_return: Optional[LLMChiefResolution] = None,
    ):
        self.opinions_to_return = opinions_to_return or {}
        self.opinion_to_return = opinion_to_return
        self.debate_responses_to_return = debate_responses_to_return or {}
        self.chief_resolution_to_return = chief_resolution_to_return
        # Call tracking for test assertions
        self.calls: List[tuple] = []           # (role, evidence_packet)
        self.debate_calls: List[tuple] = []    # (role, evidence_packet)
        self.chief_calls: List[tuple] = []     # (evidence_packet, decision, debate_result)

    def reason(self, evidence_packet: LLMEvidencePacket, specialist_role: str) -> LLMSpecialistOpinion:
        self.calls.append((specialist_role, evidence_packet))

        if specialist_role in self.opinions_to_return:
            opinion = self.opinions_to_return[specialist_role]
            opinion.validate_against_evidence(evidence_packet)
            return opinion

        if self.opinion_to_return is not None:
            self.opinion_to_return.validate_against_evidence(evidence_packet)
            return self.opinion_to_return

        first_candidate = evidence_packet.candidates[0].candidate_id if evidence_packet.candidates else "box_now"
        return LLMSpecialistOpinion(
            specialist_role=specialist_role,
            supported_candidate_ids=[first_candidate],
            preferred_candidate_id=first_candidate,
            reasoning_summary=f"Default reasoning summary for {specialist_role}.",
            cited_evidence_ids=[],
            confidence=ConfidenceLevel.HIGH,
            disagreement_flag=False,
        )

    def debate_rebuttal(
        self,
        evidence_packet: LLMEvidencePacket,
        specialist_role: str,
        own_initial_opinion: LLMSpecialistOpinion,
        peer_opinions: List[LLMSpecialistOpinion],
    ) -> LLMDebateResponse:
        self.debate_calls.append((specialist_role, evidence_packet))

        if specialist_role in self.debate_responses_to_return:
            response = self.debate_responses_to_return[specialist_role]
            response.validate_against_evidence(evidence_packet)
            return response

        # Default: maintain own position, cite zero new evidence
        preferred = own_initial_opinion.preferred_candidate_id
        if preferred is None and evidence_packet.candidates:
            preferred = evidence_packet.candidates[0].candidate_id
        return LLMDebateResponse(
            specialist_role=specialist_role,
            preferred_candidate_id=preferred,
            rebuttal_summary=f"Maintaining position after reviewing peers. Role: {specialist_role}.",
            cited_evidence_ids=[],
            position_changed=False,
            disagreement_flag=False,
        )

    def chief_resolution(
        self,
        evidence_packet: LLMEvidencePacket,
        decision: StrategyDecision,
        debate_result: LLMDebateResult,
    ) -> LLMChiefResolution:
        self.chief_calls.append((evidence_packet, decision, debate_result))

        if self.chief_resolution_to_return is not None:
            self.chief_resolution_to_return.validate_against_evidence(evidence_packet, decision)
            return self.chief_resolution_to_return

        # Default: confirm the deterministic winner with no override
        return LLMChiefResolution(
            confirmed_candidate_id=decision.selected_candidate.candidate_id,
            overridden=False,
            strategic_rationale=(
                f"Default Chief confirmation of deterministic winner "
                f"'{decision.selected_candidate.candidate_id}' after reviewing debate."
            ),
            minority_concerns_acknowledged=[],
            confidence=ConfidenceLevel.HIGH,
            cited_evidence_ids=[],
        )


# ---------------------------------------------------------------------------
# Role-specific prompt instructions (factor ownership boundaries)
# ---------------------------------------------------------------------------

SPECIALIST_INSTRUCTIONS: Dict[str, str] = {
    "PACE_TYRE": (
        "You are the Pace & Tyre Specialist. "
        "Focus ONLY on your owned pace, tyre, and traffic evidence (e.g., tyre_health, tyre_freshness_gain, "
        "tyre_life_remaining, tyre_cliff_penalty, clean_air_rejoin_bonus, traffic_rejoin_penalty, "
        "undercut_pace_advantage, undercut_defense_advantage, overcut_push_pace, pushing_on_dead_tyres_penalty, "
        "tyre_conservation_benefit, recent_pace_trend_s_per_lap, degradation_rate_s_per_lap, "
        "clean_air_potential_lap_time_s, expected_rejoin_gap_to_traffic_s, rejoin_traffic_density_penalty_s). "
        "Do NOT claim ownership of, calculate, or reference weather crossover gains, "
        "wet/dry crossover timing, track temperature, rain probability, VSC/SC time savings, "
        "green flag pit loss costs, or sporting regulation compound fulfillment."
    ),
    "WEATHER": (
        "You are the Weather Specialist. "
        "Focus ONLY on your owned weather and crossover evidence (e.g., wet_weather_crossover_gain, "
        "dry_track_wet_compound_penalty, slick_on_wet_track_penalty, rain_arrival_crossover_timing, "
        "preemptive_wet_pit_stop_gain, slicks_before_rain_penalty, stretch_slicks_to_rain_window, "
        "wet_tyres_on_dry_track_penalty, track_temp_c, air_temp_c, rainfall, humidity_pct, wind_speed_kmh, "
        "rain_probability, expected_arrival_laps, intensity). "
        "Do NOT claim ownership of, calculate, or reference tyre health, degradation rates, traffic gaps, "
        "undercut/overcut margins, clean air bonuses, VSC/SC time savings, green flag pit loss, "
        "or sporting regulation compound fulfillment."
    ),
    "RACE_CONTROL": (
        "You are the Race Control Specialist. "
        "Focus ONLY on your owned safety car, virtual safety car, flags, and sporting regulation evidence "
        "(e.g., neutralised_pit_delta_saving, green_flag_full_pit_loss_cost, mandatory_dry_compound_fulfillment, "
        "mandatory_compound_fulfillment_progress, missed_cheap_pit_window_penalty, green_flag_stay_out_preservation, "
        "track_status, green_pit_loss_s, vsc_pit_loss_s, sc_pit_loss_s, current_pit_loss_s, "
        "expected_rejoin_position). "
        "Do NOT claim ownership of, calculate, or reference tyre health, degradation rates, traffic gaps, "
        "undercut/overcut margins, clean air bonuses, weather crossover gains, rain arrival times, "
        "or wet track compound penalties."
    ),
}


# ---------------------------------------------------------------------------
# Orchestrator (Milestone 2B single-pass + Milestone 2C one-round debate)
# ---------------------------------------------------------------------------

class LLMSpecialistOrchestrator:
    """
    Orchestrates single-pass (2B) and one-round debate (2C) LLM specialist reasoning flows.
    """
    SPECIALIST_ROLES = ["PACE_TYRE", "WEATHER", "RACE_CONTROL"]

    def __init__(self, provider: LLMReasoningProvider):
        self.provider = provider

    def run_llm_reasoning_if_needed(
        self, state: Any, decision: StrategyDecision
    ) -> Optional[List[LLMSpecialistOpinion]]:
        """
        Milestone 2B: selective single-pass opinions.
        Returns None (zero provider calls) when conflict_detected is False.
        """
        if not should_invoke_llm_reasoning(decision):
            return None

        evidence_packet = build_evidence_packet(state, decision)
        opinions: List[LLMSpecialistOpinion] = []

        for role in self.SPECIALIST_ROLES:
            opinion = self.provider.reason(evidence_packet, role)
            opinion.validate_against_evidence(evidence_packet)
            opinions.append(opinion)

        return opinions

    def run_debate_if_needed(
        self, state: Any, decision: StrategyDecision
    ) -> Optional[LLMDebateResult]:
        """
        Milestone 2C: one-round selective specialist debate.
        Returns None (zero provider calls) when conflict_detected is False.

        When conflict_detected is True:
          1. Build the immutable evidence packet once.
          2. Run first-pass independent opinions for all three specialist roles.
          3. Give each specialist exactly ONE debate_rebuttal call with validated peer opinions.
          4. Validate every debate response against the original evidence packet.
          5. Return LLMDebateResult with debate_round=1.

        No second round is ever run. The deterministic candidate scores are never modified.
        """
        if not should_invoke_llm_reasoning(decision):
            return None

        evidence_packet = build_evidence_packet(state, decision)

        # Step 1 — first-pass opinions
        initial_opinions: List[LLMSpecialistOpinion] = []
        for role in self.SPECIALIST_ROLES:
            opinion = self.provider.reason(evidence_packet, role)
            opinion.validate_against_evidence(evidence_packet)
            initial_opinions.append(opinion)

        # Step 2 — exactly one debate round
        debate_responses: List[LLMDebateResponse] = []
        for own_opinion in initial_opinions:
            role = own_opinion.specialist_role
            peer_opinions = [op for op in initial_opinions if op.specialist_role != role]
            response = self.provider.debate_rebuttal(
                evidence_packet, role, own_opinion, peer_opinions
            )
            response.validate_against_evidence(evidence_packet)
            debate_responses.append(response)

        # debate_round is hardcoded to 1 — no further rounds are permitted
        return LLMDebateResult(
            initial_opinions=initial_opinions,
            debate_responses=debate_responses,
            debate_round=1,
        )

    def resolve_after_debate(
        self, state: Any, decision: StrategyDecision
    ) -> Optional["LLMChiefResolution"]:
        """
        Milestone 2D: Chief Strategist LLM resolution after the debate.
        Returns None (zero provider calls) when conflict_detected is False.

        When conflict_detected is True:
          1. Runs the full one-round debate via run_debate_if_needed.
          2. Calls provider.chief_resolution with the evidence packet, the
             deterministic decision, and the completed debate result.
          3. Validates the resolution against the evidence packet.
          4. Returns the immutable LLMChiefResolution.

        The Chief may confirm or flag concern about the deterministic winner.
        It may NOT invent a new candidate or modify any score.
        """
        if not should_invoke_llm_reasoning(decision):
            return None

        debate_result = self.run_debate_if_needed(state, decision)
        if debate_result is None:
            return None  # defensive — should not happen given the trigger check above

        evidence_packet = build_evidence_packet(state, decision)

        resolution = self.provider.chief_resolution(
            evidence_packet, decision, debate_result
        )
        resolution.validate_against_evidence(evidence_packet, decision)
        return resolution


# ---------------------------------------------------------------------------
# Evidence packet builder
# ---------------------------------------------------------------------------

def build_evidence_packet(state: Any, decision: StrategyDecision) -> LLMEvidencePacket:
    """
    Constructs an immutable LLMEvidencePacket from the deterministic RaceState and StrategyDecision.
    Includes only existing structured data. No future/unbounded historical data is included.
    """
    return LLMEvidencePacket(
        current_lap=state.current_lap,
        total_laps=state.total_laps,
        track_status=state.track_status,
        subject_driver=state.subject_driver,
        competitors=state.competitors,
        observed_weather=state.observed_weather,
        weather_forecast=state.weather_forecast,
        derived_pace=state.derived_pace,
        pit_loss=state.pit_loss,
        candidates=decision.all_candidates,
        specialist_evaluations=decision.specialist_evaluations,
        conflict_detected=decision.conflict_detected,
        conflict_summary=decision.conflict_summary,
    )
