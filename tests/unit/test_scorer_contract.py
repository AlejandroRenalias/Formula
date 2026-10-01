import pytest
from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.agents.rules.race_control import RuleBasedRaceControlAgent
from src.calculators.candidate_gen import CandidateGenerator
from src.core.context_builder import ContextBuilder
from src.core.models import PitAction, TireCompound, StrategyDecision
from src.orchestrator.pipeline import StrategyPipeline


@pytest.mark.parametrize("target,progress", [
    (TireCompound.MEDIUM, False), (TireCompound.HARD, True),
    (TireCompound.INTERMEDIATE, True), (TireCompound.WET, True), (None, False),
])
def test_compound_progress_requires_new_compound(target, progress):
    state = SyntheticRaceAdapter.create_race_state()
    candidates = CandidateGenerator.generate_candidates(state)
    candidates = [c.model_copy(update={"target_compound": target})
                  if c.pit_action == PitAction.BOX_NOW else c for c in candidates]
    report = RuleBasedRaceControlAgent().evaluate(ContextBuilder.build_race_control_context(state, candidates))
    box = next(c for c in candidates if c.pit_action == PitAction.BOX_NOW)
    assert (report.candidate_factors[box.candidate_id].get("mandatory_compound_fulfillment_progress") == 2) == progress


def test_score_margin_roundtrip_has_points_contract():
    decision = StrategyPipeline().run_strategy_cycle(SyntheticRaceAdapter.create_race_state())
    payload = decision.model_dump()
    assert "expected_advantage_s" not in payload
    assert decision.score_margin == round(decision.all_candidates[0].candidate_strategy_score
                                         - decision.all_candidates[1].candidate_strategy_score, 2)
    assert StrategyDecision.model_validate_json(decision.model_dump_json()).score_margin == decision.score_margin
