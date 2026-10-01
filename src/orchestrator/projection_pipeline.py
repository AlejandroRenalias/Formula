"""Projection owns the call; the existing pipeline supplies specialist reasoning."""
from src.calculators.projection import project, ProjectionConfig, Policy, _snapshot
from src.orchestrator.pipeline import StrategyPipeline
from src.core.models import RaceState


def run_projection_cycle(state: RaceState, config: ProjectionConfig | None = None,
                         policies: tuple[Policy, ...] | None = None) -> dict:
    config = config or ProjectionConfig()
    snapshot = _snapshot(state, config)
    result = project(snapshot, policies, config)
    reasoning = StrategyPipeline().run_strategy_cycle(snapshot)
    recommended = next(p for p in result["plans"] if p["id"] == result["recommended"])
    actions = {}
    for scenario in recommended["scenario_stops"]:
        stop = next((s for s in scenario["stops"] if s["lap"] == snapshot.current_lap), None)
        key = f"BOX_NOW:{stop['compound']}" if stop else "STAY_OUT"
        actions[key] = actions.get(key, 0.0) + scenario["weight"]
    dominant = max(sorted(actions), key=actions.get)
    initial_box_probability = sum(weight for action, weight in actions.items() if action.startswith("BOX_NOW:"))
    scorer_key = (f"BOX_NOW:{reasoning.target_compound.value}" if reasoning.pit_action.value == "BOX_NOW" else "STAY_OUT")
    mismatch_probability = sum(weight for key, weight in actions.items() if key != scorer_key)
    result["scorer"] = reasoning.model_dump(mode="json")
    result["disagreement"] = {"disagrees": mismatch_probability > 1e-9,
        "comparison": "initial action and compound across scenarios; heuristic candidates are not full policies",
        "scorer_candidate": reasoning.selected_candidate.candidate_id,
        "scorer_action": reasoning.pit_action.value,
        "projection_policy": result["recommended"],
        "projection_initial_box_probability": round(initial_box_probability, 6),
        "projection_initial_actions": {key: round(weight, 6) for key, weight in actions.items()},
        "disagreement_probability": round(mismatch_probability, 6),
        "projection_action": dominant.split(":")[0],
        "projection_compound": dominant.split(":")[1] if ":" in dominant else None}
    return result
