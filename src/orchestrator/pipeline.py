"""End-to-end deterministic strategy pipeline with optional LLM resolution."""
from typing import Optional
from src.core.models import RaceState, StrategyDecision
from src.core.context_builder import ContextBuilder
from src.calculators.candidate_gen import CandidateGenerator
from src.calculators.rules_engine import RulesEngine, NoLegalCandidatesError
from src.agents.rules.pace_tyre import RuleBasedPaceTyreAgent
from src.agents.rules.weather import RuleBasedWeatherAgent
from src.agents.rules.race_control import RuleBasedRaceControlAgent
from src.agents.rules.chief import RuleBasedChiefStrategist
from src.orchestrator.conflict_detector import ConflictDetector
from src.core.llm import LLMSpecialistOrchestrator


class StrategyPipeline:
    """Orchestrates candidate generation, specialist evaluations, conflict detection, and final decision."""

    def __init__(
        self,
        pace_agent: Optional[RuleBasedPaceTyreAgent] = None,
        weather_agent: Optional[RuleBasedWeatherAgent] = None,
        race_control_agent: Optional[RuleBasedRaceControlAgent] = None,
        chief_strategist: Optional[RuleBasedChiefStrategist] = None,
        llm_orchestrator: Optional[LLMSpecialistOrchestrator] = None,
    ):
        self.pace_agent = pace_agent or RuleBasedPaceTyreAgent()
        self.weather_agent = weather_agent or RuleBasedWeatherAgent()
        self.race_control_agent = race_control_agent or RuleBasedRaceControlAgent()
        self.chief = chief_strategist or RuleBasedChiefStrategist()
        self.llm_orchestrator = llm_orchestrator

    def run_strategy_cycle(self, state: RaceState) -> StrategyDecision:
        """Executes a single end-to-end strategy evaluation cycle."""
        # 1. Deterministic Candidate Generation
        generated_candidates = CandidateGenerator.generate_candidates(state)
        validation = RulesEngine.validate_candidates(generated_candidates, state)
        if not validation.legal_candidates:
            raise NoLegalCandidatesError(state.current_lap, validation.rejected_candidates)
        candidates = validation.legal_candidates

        # 2. Build role-specific context models
        pace_ctx = ContextBuilder.build_pace_tyre_context(state, candidates)
        weather_ctx = ContextBuilder.build_weather_context(state, candidates)
        race_ctrl_ctx = ContextBuilder.build_race_control_context(state, candidates)

        # 3. Specialist agent evaluations
        pace_report = self.pace_agent.evaluate(pace_ctx)
        weather_report = self.weather_agent.evaluate(weather_ctx)
        race_ctrl_report = self.race_control_agent.evaluate(race_ctrl_ctx)

        specialist_reports = [pace_report, weather_report, race_ctrl_report]

        # 4. Conflict Detection (Ambiguity flag for Chief resolution in M0; triggers LLM debate in M2)
        conflict_detected, conflict_reason = ConflictDetector.should_trigger_debate(candidates, specialist_reports)

        # 5. Chief Strategist Final Call with factor audit
        decision = self.chief.make_decision(
            lap=state.current_lap,
            candidates=candidates,
            specialist_reports=specialist_reports,
            objective=state.objective,
            risk_profile=state.risk_profile,
            conflict_detected=conflict_detected,
            conflict_summary=conflict_reason if conflict_detected else None,
            debate_held=False,
            debate_transcript=None,
        )

        # LLM reasoning is strictly opt-in and conflict-gated. It returns
        # separate resolution metadata and cannot alter deterministic fields.
        decision = decision.model_copy(update={"rejected_candidates": validation.rejected_candidates})

        if self.llm_orchestrator is not None and conflict_detected:
            resolution = self.llm_orchestrator.resolve_after_debate(state, decision)
            return decision.model_copy(update={"llm_chief_resolution": resolution})

        return decision
