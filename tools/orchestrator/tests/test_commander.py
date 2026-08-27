import asyncio
import json
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from formula_orchestrator import commander
from formula_orchestrator.cli import main
from formula_orchestrator.config import ModelConfig, OrchestratorConfig


def prepared_plan_payload() -> dict[str, object]:
    return {
        "schema_version": 1, "task_id": "t", "title": "Authoritative title", "objective": "Objective",
        "commit_message": "commit", "acceptance_criteria": ["criterion"], "allowed_paths": ["src/x.py"],
        "allowed_roots": [], "forbidden_paths": [".git"], "scope_risk": "LOW", "baseline_head_sha": "abc",
        "baseline_branch": "main", "baseline_test_status": "PASS", "baseline_test_exit_code": 0,
        "test_command": "pytest", "test_timeout_seconds": 30.0, "coordinator_model": "coord",
        "coordinator_reasoning_effort": "high", "codex_model": "codex", "codex_reasoning_effort": "low",
        "configured_max_repair_loops": 2, "approved_repair_limit": 2, "prepared_at": "2026-01-01T00:00:00+00:00",
        "repository_path": "/formula", "plan_fingerprint": "fingerprint", "approval_token": "token",
    }


def config_for(tmp_path: Path) -> OrchestratorConfig:
    root = tmp_path / "formula"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='formula'\n", encoding="utf-8")
    return OrchestratorConfig(repository_root=root, run_log_directory=root / "logs",
                              coordinator=ModelConfig(model="coord", reasoning_effort="high"),
                              codex=ModelConfig(model="codex", reasoning_effort="low"))


def test_cli_accepts_commander(monkeypatch):
    monkeypatch.setattr("formula_orchestrator.cli.run_commander", lambda config: 7)
    assert main(["commander"]) == 7


def test_agent_uses_configured_model_reasoning_and_approvals(tmp_path):
    agent = commander.build_commander_agent(config_for(tmp_path))
    assert agent.model == "coord"
    assert agent.model_settings.reasoning.effort == "high"
    tools = {tool.name: tool for tool in agent.tools}
    assert set(tools) == {"inspect_project_state", "prepare_formula_task", "run_prepared_task", "inspect_o5_run", "finalize_ready_task"}
    assert tools["run_prepared_task"].needs_approval is True
    assert tools["finalize_ready_task"].needs_approval is True


def test_run_commander_constructs_fixed_sqlite_session(tmp_path, monkeypatch):
    config = config_for(tmp_path)
    captured = {}

    def session(session_id, *, db_path):
        captured.update(session_id=session_id, db_path=db_path)
        return object()

    monkeypatch.setattr(commander, "require_authentication", lambda: None)
    monkeypatch.setattr(commander, "build_commander_agent", lambda config: object())
    monkeypatch.setattr("agents.SQLiteSession", session)
    monkeypatch.setattr("builtins.input", lambda prompt="": "exit")
    assert commander.run_commander(config) == 0
    assert captured == {"session_id": "formula-main",
                        "db_path": str(config.run_log_directory / "commander" / "commander.sqlite")}


def test_project_state_uses_fixed_read_only_git_commands(tmp_path, monkeypatch):
    config = config_for(tmp_path)
    calls = []

    def fake_run(command, **kwargs):
        calls.append(command)
        output = {("git", "status", "--porcelain", "--untracked-files=all"): " M src/x.py\n",
                  ("git", "rev-parse", "HEAD"): "abc\n", ("git", "symbolic-ref", "--short", "-q", "HEAD"): "main\n"}[tuple(command)]
        return SimpleNamespace(returncode=0, stdout=output, stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    state = commander.inspect_project_state(config)
    assert state["changed_paths"] == ["src/x.py"]
    assert all(call[0] == "git" and call[1] in {"status", "rev-parse", "symbolic-ref"} for call in calls)
    with pytest.raises(ValueError):
        commander._git(config.repository_root, ("reset", "--hard"))


def test_prepare_delegates_to_o5(tmp_path, monkeypatch):
    config = config_for(tmp_path)
    captured = {}
    plan = SimpleNamespace(task_id="t", title="Title", baseline_head_sha="head", baseline_test_status="PASS",
                           scope_risk="LOW", allowed_paths=["src/x.py"], allowed_roots=[], approved_repair_limit=1,
                           codex_model="codex", codex_reasoning_effort="low", coordinator_model="coord",
                           coordinator_reasoning_effort="high", plan_path=Path("unused"), approval_token="token")
    monkeypatch.setattr(commander, "prepare_task", lambda path, cfg: captured.update(path=path, config=cfg) or SimpleNamespace(plan=plan, plan_path=config.run_log_directory / "prepared.json", approval_token="token"))
    result = commander.prepare_formula_task(config, "t", "Title", "Objective", ["criterion"], ["src/x.py"], [], 1, "commit")
    assert captured["config"] is config
    assert captured["path"].is_relative_to(config.run_log_directory / "commander")
    assert result["approval_token"] == "token"


def test_o5_path_must_be_inside_run_logs(tmp_path):
    config = config_for(tmp_path)
    outside = tmp_path / "outside.json"
    outside.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="inside"):
        commander.inspect_o5_run(config, str(outside))


def test_run_approval_is_loaded_from_plan_not_prose(tmp_path):
    config = config_for(tmp_path)
    plan = config.run_log_directory / "prepared.json"
    plan.parent.mkdir(parents=True)
    plan.write_text(json.dumps(prepared_plan_payload()), encoding="utf-8")
    rendered = commander.render_run_approval(config, str(plan))
    assert "Authoritative title" in rendered
    assert "model-generated" not in rendered


def test_run_approval_rejects_malformed_prepared_plan(tmp_path):
    config = config_for(tmp_path)
    plan = config.run_log_directory / "prepared.json"
    plan.parent.mkdir(parents=True)
    plan.write_text(json.dumps({"task_id": "incomplete"}), encoding="utf-8")
    with pytest.raises(ValueError, match="invalid prepared plan"):
        commander.render_run_approval(config, str(plan))


def test_run_result_distinguishes_baseline_from_final_technical_test(tmp_path, monkeypatch):
    from formula_orchestrator.finalization import FinalizationPlan

    config = config_for(tmp_path)
    plan_path = config.run_log_directory / "prepared.json"
    finalization_path = config.run_log_directory / "finalization" / "run.json"
    finalization_path.parent.mkdir(parents=True)
    plan_path.write_text("{}", encoding="utf-8")
    finalization = FinalizationPlan.model_construct(
        task_id="t", final_changed_paths=[], final_diff_char_count=0, final_test_result="PASS",
        final_gpt_verdict="PASS", repair_count=0, commit_message="msg", push_remote="origin",
        push_branch="main", o5_run_id="run", o4_run_id="o4", prepared_plan_fingerprint="fp",
        baseline_head="abc", branch="main", repository_path=str(config.repository_root), allowed_paths=[],
        allowed_roots=[], forbidden_paths=[], final_git_status="", final_diff_sha256="sha",
        push_remote_url="url", prepared_timestamp="now", finalization_fingerprint="finger",
        finalization_token="token",
    )
    finalization_path.write_text(finalization.model_dump_json(), encoding="utf-8")
    record = SimpleNamespace(final_status="READY_FOR_HUMAN_REVIEW", task_id="t", final_evidence={},
                             fresh_baseline_test_status="PASS", repair_count=0, run_file_path="run",
                             finalization_token="token", finalization_plan_path=str(finalization_path), error=None)
    monkeypatch.setattr(commander, "run_task", lambda *args: SimpleNamespace(run_record=record))
    result = commander.run_prepared_task(config, str(plan_path), "token")
    assert result["fresh_baseline_test_status"] == "PASS"
    assert result["final_technical_test_status"] == "PASS"
    assert "tests" not in result


@pytest.mark.parametrize(("tool_name", "arguments", "target_name"), [
    ("run_prepared_task", {"plan_path": "placeholder", "approval_token": "token"}, "run_task"),
    ("finalize_ready_task", {"run_path": "placeholder", "approval_token": "token"}, "finalize_task"),
])
@pytest.mark.parametrize("approved", [False, True])
def test_sdk_approval_boundary_controls_commander_execution(tmp_path, monkeypatch, tool_name, arguments, target_name, approved):
    """Exercise the actual SDK interruption and RunState resume boundary offline."""
    from agents import Runner
    from agents.testing import ScriptedModel, assistant_message, function_call

    config = config_for(tmp_path)
    record_path = config.run_log_directory / "placeholder"
    record_path.parent.mkdir(parents=True)
    record_path.write_text("{}", encoding="utf-8")
    arguments = ({"plan_path": str(record_path), "approval_token": "token"}
                 if tool_name == "run_prepared_task"
                 else {"run_path": str(record_path), "approval_token": "token"})
    calls = []

    def invoked(*args):
        calls.append(args)
        if target_name == "run_task":
            return SimpleNamespace(run_record=SimpleNamespace(
                final_status="TECHNICAL_FAILED", task_id="t", final_evidence=None,
                fresh_baseline_test_status="PASS", repair_count=0, run_file_path="run",
                finalization_token=None, finalization_plan_path=None, error=None,
            ))
        return SimpleNamespace(status="FINALIZED", commit_sha="sha", push_success=True)

    monkeypatch.setattr(commander, target_name, invoked)
    model = ScriptedModel([
        [function_call(tool_name, arguments, call_id="call-1")],
        [assistant_message("resumed")],
    ])
    agent = commander.build_commander_agent(config)
    agent.model = model
    interrupted = asyncio.run(Runner.run(agent, "perform action", max_turns=3))
    assert len(interrupted.interruptions) == 1
    state = interrupted.to_state()
    item = interrupted.interruptions[0]
    if approved:
        state.approve(item)
    else:
        state.reject(item, rejection_message="rejected")
    resumed = asyncio.run(Runner.run(agent, state, max_turns=3))
    assert resumed.final_output == "resumed"
    assert len(calls) == (1 if approved else 0)
    model.assert_complete()


def test_finalization_approval_uses_pass_evidence_and_exact_paths(tmp_path):
    config = config_for(tmp_path)
    final = config.run_log_directory / "finalization" / "run.json"
    final.parent.mkdir(parents=True)
    from formula_orchestrator.finalization import FinalizationPlan
    data = FinalizationPlan.model_construct(task_id="t", final_changed_paths=["src/a.py", "tests/a.py"], final_diff_char_count=10,
            final_test_result="PASS", final_gpt_verdict="PASS", repair_count=1, commit_message="msg",
            push_remote="origin", push_branch="main", o5_run_id="run", o4_run_id="o4", prepared_plan_fingerprint="fp",
            baseline_head="abc", branch="main", repository_path=str(config.repository_root), allowed_paths=[], allowed_roots=[],
            forbidden_paths=[], final_git_status=" M src/a.py", final_diff_sha256="sha", push_remote_url="url",
            prepared_timestamp="now", finalization_fingerprint="finger", finalization_token="token")
    final.write_text(data.model_dump_json(), encoding="utf-8")
    run = config.run_log_directory / "o5-run.json"
    run.write_text(json.dumps({"run_id": "run", "task_id": "t", "final_status": "READY_FOR_HUMAN_REVIEW",
                               "finalization_plan_path": str(final)}), encoding="utf-8")
    rendered = commander.render_finalization_approval(config, str(run))
    assert "Tests: PASS" in rendered and "GPT review: PASS" in rendered
    assert "src/a.py, tests/a.py" in rendered


def test_exit_quit_and_eof_are_clean(monkeypatch, tmp_path):
    config = config_for(tmp_path)
    monkeypatch.setattr(commander, "require_authentication", lambda: None)
    monkeypatch.setattr(commander, "build_commander_agent", lambda config: object())
    monkeypatch.setattr("agents.SQLiteSession", lambda *args, **kwargs: object())
    monkeypatch.setattr("builtins.input", lambda prompt="": "exit")
    assert commander.run_commander(config) == 0


def test_commander_api_rejection_is_concise_recovers_read_only_and_returns_to_prompt(monkeypatch, tmp_path, capsys):
    from openai import BadRequestError

    config = config_for(tmp_path)
    error = BadRequestError(
        "Error code: 400",
        response=SimpleNamespace(status_code=400, headers={}, request=SimpleNamespace()),
        body={"error": {"message": "Invalid schema for function 'prepare_formula_task'.", "param": "tools[1]"}},
    )
    answers = iter(["inspect", "exit"])
    inspections = []
    runner_calls = []

    def inspect(config):
        inspections.append(config)
        return {"branch": "main", "head": "abc123", "clean": False, "changed_paths": ["src/x.py"],
                "latest_local_o5": {"task_id": "task-1", "final_status": "READY_FOR_HUMAN_REVIEW"}}

    monkeypatch.setattr(commander, "require_authentication", lambda: None)
    monkeypatch.setattr(commander, "build_commander_agent", lambda config: object())
    monkeypatch.setattr("agents.SQLiteSession", lambda *args, **kwargs: object())
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))
    monkeypatch.setattr(commander, "inspect_project_state", inspect)
    monkeypatch.setattr(commander, "run_task", lambda *args: pytest.fail("run_task must not retry after API failure"))
    monkeypatch.setattr(commander, "finalize_task", lambda *args: pytest.fail("finalize_task must not retry after API failure"))
    monkeypatch.setattr(commander, "_run_turn", lambda *args: object())
    monkeypatch.setattr(commander.asyncio, "run", lambda *args: runner_calls.append(args) or (_ for _ in ()).throw(error))
    assert commander.run_commander(config) == 0
    output = capsys.readouterr().out
    assert "Commander API error (400): Invalid schema for function 'prepare_formula_task'." in output
    assert "Commander recovery state (read-only):" in output
    assert "Branch: main" in output and "HEAD: abc123" in output and "Clean: False" in output
    assert "Changed paths: src/x.py" in output and '"task_id": "task-1"' in output
    assert "Do not retry any approved action" in output
    assert "Traceback" not in output
    assert len(runner_calls) == 1
    assert inspections == [config]
