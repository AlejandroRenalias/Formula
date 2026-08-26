import asyncio
import sys
from types import ModuleType, SimpleNamespace
from pathlib import Path

import pytest

from formula_orchestrator.config import DEFAULT_TEST_COMMAND, ModelConfig, OrchestratorConfig, discover_repository_root
from formula_orchestrator.codex_executor import CodexExecutor
from formula_orchestrator.evidence import ReviewInput
from formula_orchestrator.reviewer import GptReviewer


def test_repository_root_detection_from_nested_path(tmp_path: Path) -> None:
    root = tmp_path / "formula"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='formula'\n", encoding="utf-8")
    assert discover_repository_root(root / "src") == root.resolve()


def test_defaults() -> None:
    config = OrchestratorConfig(repository_root=Path.cwd())
    assert config.max_repair_loops == 2
    assert config.test_command == DEFAULT_TEST_COMMAND
    assert config.coordinator.model == "gpt-5.6-luna"
    assert config.codex.model == "gpt-5.6-luna"
    assert config.coordinator.reasoning_effort == "medium"
    assert config.codex.reasoning_effort == "medium"


@pytest.mark.parametrize("effort", ["", " ", "ultra"])
def test_invalid_reasoning_effort_is_rejected(effort: str) -> None:
    with pytest.raises(ValueError, match="reasoning_effort"):
        ModelConfig(reasoning_effort=effort)


def test_sdk_boundaries_receive_explicit_configured_medium_reasoning(monkeypatch, tmp_path: Path) -> None:
    captured_agents = []
    captured_threads = []

    class FakeAgent:
        def __init__(self, **kwargs):
            captured_agents.append(kwargs)
            self.name = kwargs["name"]

    class FakeRunner:
        @staticmethod
        async def run(agent, prompt, max_turns):
            if agent.name == "Formula Independent Reviewer":
                return SimpleNamespace(final_output={"verdict": "PASS", "summary": "All good.", "findings": []})
            return SimpleNamespace(final_output="completed", context_wrapper=None)

    class FakeThreadOptions:
        def __init__(self, **kwargs):
            captured_threads.append(kwargs)

    class FakeTurnOptions:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    fake_agents = ModuleType("agents")
    fake_agents.Agent = FakeAgent
    fake_agents.Runner = FakeRunner
    from agents import ModelSettings
    fake_agents.ModelSettings = ModelSettings
    codex_module = ModuleType("agents.extensions.experimental.codex")
    codex_module.ThreadOptions = FakeThreadOptions
    codex_module.TurnOptions = FakeTurnOptions
    codex_module.codex_tool = lambda **kwargs: kwargs
    monkeypatch.setitem(sys.modules, "agents", fake_agents)
    monkeypatch.setitem(sys.modules, "agents.extensions", ModuleType("agents.extensions"))
    monkeypatch.setitem(sys.modules, "agents.extensions.experimental", ModuleType("agents.extensions.experimental"))
    monkeypatch.setitem(sys.modules, "agents.extensions.experimental.codex", codex_module)

    model = ModelConfig(model="gpt-5.6-luna", reasoning_effort="medium")
    codex_result = asyncio.run(CodexExecutor().execute(tmp_path, "bounded task", model, "run"))
    review_result = asyncio.run(GptReviewer()._review(ReviewInput("task", "summary", "", (), "", "PASS", "", "", "PASS", "run"), model))

    assert codex_result.success and review_result.success
    assert captured_threads[0]["model"] == "gpt-5.6-luna"
    assert captured_threads[0]["model_reasoning_effort"] == "medium"
    assert captured_agents[0]["model"] == "gpt-5.6-luna"
    assert captured_agents[0]["model_settings"].reasoning.effort == "medium"
    assert captured_agents[1]["model"] == "gpt-5.6-luna"
    assert captured_agents[1]["model_settings"].reasoning.effort == "medium"


def test_serialization_contains_no_credentials(tmp_path: Path) -> None:
    config = OrchestratorConfig(repository_root=tmp_path)
    serialized = repr(config.to_dict())
    assert "OPENAI_API_KEY" not in serialized
    assert "sk-" not in serialized


def test_run_log_directory_cannot_escape_repository(tmp_path: Path) -> None:
    try:
        OrchestratorConfig(repository_root=tmp_path, run_log_directory=tmp_path.parent / "outside")
    except ValueError as exc:
        assert "inside the Formula repository" in str(exc)
    else:
        raise AssertionError("run log directory must be workspace-scoped")
