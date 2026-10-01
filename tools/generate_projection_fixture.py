"""Offline fixture generation: python -m tools.generate_projection_fixture."""
import json
from pathlib import Path

from src.adapters.synthetic_adapter import SyntheticRaceAdapter
from src.calculators.projection import ProjectionConfig
from src.orchestrator.projection_pipeline import run_projection_cycle
from src.ui.projection_fixture import build_projection_view


def main():
    state = SyntheticRaceAdapter.create_race_state(current_lap=18, total_laps=52,
        subject_driver="NOR", stint_length_laps=17, rain_probability=.70,
        rain_arrival_laps=4, rain_intensity="LIGHT")
    config = ProjectionConfig()
    result = run_projection_cycle(state, config)
    result['ui'] = build_projection_view(result, state)
    result["fixture"] = {"source": "synthetic", "generation": "python -m tools.generate_projection_fixture",
                         "state": state.model_dump(mode="json"), "config": config.model_dump(mode="json")}
    destination = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "projection_lap18.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(destination)
    for pid in result["ranking"]:
        plan = next(p for p in result["plans"] if p["id"] == pid)
        print(pid, plan["mean_time_to_finish_s"])
    for key in ("call", "call_margin_s", "plan_margin_s", "call_win_rate"):
        print(key, result[key])


if __name__ == "__main__":
    main()
