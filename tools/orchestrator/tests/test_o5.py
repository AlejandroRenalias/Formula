import json
import subprocess
from types import SimpleNamespace
from pathlib import Path

import pytest

from formula_orchestrator.codex_executor import CodexExecutionResult
from formula_orchestrator.cli import main
from formula_orchestrator.config import ModelConfig, OrchestratorConfig
from formula_orchestrator.o4 import O4Result
from formula_orchestrator.reviewer import ReviewDecision, ReviewResult
from formula_orchestrator.o5 import (
    O5Error,
    PreparedTaskPlan,
    TaskRequest,
    canonical_task_text,
    prepare_task,
    run_task,
)
from formula_orchestrator.run_record import RunRecord
from formula_orchestrator.test_runner import TestRunResult
from .test_preflight import make_repo


def passing_test():
    return TestRunResult(("pytest",), 0, True, "passed", "", 0.1, False)


def failing_test(code=1, error=None, timed_out=False):
    return TestRunResult(("pytest",), code, False, "failed", "", 0.1, timed_out, error)


def request(**updates):
    value = {
        "schema_version": 1,
        "task_id": "task-one",
        "title": "Small tooling task",
        "objective": "Make the approved change.",
        "acceptance_criteria": ["The requested behavior is implemented."],
        "allowed_paths": ["src/placeholder.py"],
        "repair_limit": 2,
    }
    value.update(updates)
    return value


def config_for(root, **updates):
    return OrchestratorConfig(repository_root=root, run_log_directory=root / "tools" / "orchestrator" / ".run-logs", **updates)


class FakeTests:
    def __init__(self, results):
        self.results = list(results)
        self.calls = 0

    def run(self, root, command, timeout):
        result = self.results[min(self.calls, len(self.results) - 1)]
        self.calls += 1
        return result


class FakeController:
    calls = []

    def __init__(self, config):
        self.config = config

    def run(self, task, scope, baseline_test_result, **kwargs):
        self.__class__.calls.append((self.config, task, scope, baseline_test_result, kwargs))
        record = RunRecord(run_id="o4-run", task_id="task-one", stage="bounded-repair", final_status="SUCCESS", repair_count=1)
        review = ReviewResult(True, ReviewDecision(verdict="PASS", summary="approved"), duration_seconds=0.1)
        return O4Result(record, passing_test(), review)


def prepared(tmp_path, monkeypatch, task_data=None, tests=None):
    root = make_repo(tmp_path)
    bare = tmp_path / "origin.git"
    subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
    subprocess.run(["git", "remote", "add", "origin", str(bare)], cwd=root, check=True)
    task_file = tmp_path / "task.json"
    task_file.write_text(json.dumps(task_data or request()), encoding="utf-8")
    config = config_for(root)
    runner = FakeTests(tests or [passing_test()])
    result = prepare_task(task_file, config, runner)
    return root, config, result, runner


def test_task_request_strict_validation():
    parsed = TaskRequest.model_validate(request())
    assert parsed.task_id == "task-one"
    with pytest.raises(ValueError):
        TaskRequest.model_validate(request(extra_field=True))
    with pytest.raises(ValueError):
        TaskRequest.model_validate(request(acceptance_criteria=[]))
    with pytest.raises(ValueError):
        TaskRequest.model_validate(request(allowed_paths=["C:/outside.py"]))
    with pytest.raises(ValueError):
        TaskRequest.model_validate(request(allowed_paths=["src/../README.md"]))
    with pytest.raises(ValueError):
        TaskRequest.model_validate(request(allowed_paths=[], allowed_roots=[]))
    with pytest.raises(ValueError):
        TaskRequest.model_validate(request(allowed_roots=["."]))
    with pytest.raises(ValueError):
        TaskRequest.model_validate(request(repair_limit=3))


def test_forbidden_scope_is_rejected(tmp_path):
    root = make_repo(tmp_path)
    with pytest.raises(O5Error, match="protected path"):
        from formula_orchestrator.o5 import _scope_from_request
        _scope_from_request(TaskRequest.model_validate(request(allowed_paths=["tools/orchestrator/src/x.py"])), config_for(root))
    with pytest.raises(O5Error, match="protected path"):
        from formula_orchestrator.o5 import _scope_from_request
        _scope_from_request(TaskRequest.model_validate(request(allowed_paths=[".env.local"])), config_for(root))
    with pytest.raises(O5Error, match="repair_limit"):
        from formula_orchestrator.o5 import _scope_from_request
        _scope_from_request(TaskRequest.model_validate(request()), config_for(root, max_repair_loops=1))


def test_prepare_is_local_and_runs_baseline(tmp_path, monkeypatch):
    root, config, result, runner = prepared(tmp_path, monkeypatch)
    assert result.plan.baseline_test_status == "PASS"
    assert runner.calls == 1
    assert result.plan_path.is_file()
    assert result.plan.approval_token == result.plan.plan_fingerprint[:16]
    assert result.plan.coordinator_reasoning_effort == "medium"
    assert result.plan.codex_reasoning_effort == "medium"


@pytest.mark.parametrize("test_result,status", [
    (failing_test(), "BASELINE_UNHEALTHY"),
    (failing_test(code=None, error="could not execute"), "BASELINE_INFRA_FAILED"),
    (failing_test(timed_out=True, error="timed out"), "BASELINE_INFRA_FAILED"),
])
def test_prepare_failure_creates_no_executable_plan(tmp_path, monkeypatch, test_result, status):
    root = make_repo(tmp_path)
    task_file = tmp_path / "task.json"
    task_file.write_text(json.dumps(request()), encoding="utf-8")
    with pytest.raises(O5Error) as error:
        prepare_task(task_file, config_for(root), FakeTests([test_result]))
    assert error.value.status == status
    assert not (root / "tools" / "orchestrator" / ".run-logs" / "prepared").exists()


def test_fingerprint_changes_for_approval_relevant_fields(tmp_path, monkeypatch):
    _, config, first, _ = prepared(tmp_path, monkeypatch)
    for field, value in (("objective", "different"), ("acceptance_criteria", ["different"]), ("allowed_paths", ["src/other.py"]), ("repair_limit", 1)):
        data = request(**{field: value})
        other_root = make_repo(tmp_path / field)
        task_file = tmp_path / f"{field}.json"
        task_file.write_text(json.dumps(data), encoding="utf-8")
        other = prepare_task(task_file, config_for(other_root), FakeTests([passing_test()]))
        assert other.plan.plan_fingerprint != first.plan.plan_fingerprint


def test_separate_preparations_have_distinct_fingerprints(tmp_path, monkeypatch):
    root, config, first, _ = prepared(tmp_path, monkeypatch)
    task_file = tmp_path / "task.json"
    second = prepare_task(task_file, config, FakeTests([passing_test()]))
    assert second.plan.prepared_at != first.plan.prepared_at
    assert second.plan.plan_fingerprint != first.plan.plan_fingerprint


def test_plan_edit_invalidates_approval(tmp_path, monkeypatch):
    root, config, result, _ = prepared(tmp_path, monkeypatch)
    data = json.loads(result.plan_path.read_text(encoding="utf-8"))
    data["objective"] = "tampered"
    result.plan_path.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    with pytest.raises(O5Error, match="fingerprint"):
        run_task(result.plan_path, result.approval_token, config, controller_factory=FakeController)


@pytest.mark.parametrize("field,value", [
    ("prepared_at", "2000-01-01T00:00:00+00:00"),
    ("repository_path", "C:/other-formula"),
    ("baseline_head_sha", "0" * 40),
    ("baseline_branch", "other-branch"),
    ("coordinator_model", "different-coordinator"),
    ("coordinator_reasoning_effort", "high"),
    ("codex_model", "different-codex"),
    ("codex_reasoning_effort", "high"),
    ("test_command", "pytest"),
    ("test_timeout_seconds", 301.0),
    ("allowed_paths", ["src/other.py"]),
    ("approved_repair_limit", 1),
    ("objective", "tampered objective"),
    ("acceptance_criteria", ["tampered criterion"]),
    ("commit_message", "Tampered commit"),
])
def test_any_persisted_plan_field_tampering_invalidates_approval(tmp_path, monkeypatch, field, value):
    _, config, result, _ = prepared(tmp_path, monkeypatch)
    data = json.loads(result.plan_path.read_text(encoding="utf-8"))
    data[field] = value
    result.plan_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(O5Error) as error:
        run_task(result.plan_path, result.approval_token, config, controller_factory=FakeController)
    assert error.value.status == "APPROVAL_MISMATCH"


def test_success_requires_explicit_final_test_and_review_evidence(tmp_path, monkeypatch):
    root, config, result, _ = prepared(tmp_path, monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "fake")

    class IncompleteController(FakeController):
        def run(self, task, scope, baseline_test_result, **kwargs):
            record = RunRecord(run_id="o4-run", task_id="task-one", stage="bounded-repair", final_status="SUCCESS")
            return O4Result(record, passing_test(), None)

    outcome = run_task(result.plan_path, result.approval_token, config, test_runner=FakeTests([passing_test()]), controller_factory=IncompleteController)
    assert outcome.run_record.final_status == "TECHNICAL_FAILED: INCOMPLETE_SUCCESS_EVIDENCE"
    assert outcome.run_record.finalization_plan_path is None
    assert outcome.run_record.finalization_token is None


def test_approval_gate_blocks_missing_and_wrong_tokens(tmp_path, monkeypatch):
    root, config, result, _ = prepared(tmp_path, monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    FakeController.calls = []
    for token in ("", "wrong-token"):
        with pytest.raises(O5Error, match="Approval token"):
            run_task(result.plan_path, token, config, controller_factory=FakeController)
    assert not FakeController.calls


def test_run_uses_fresh_baseline_and_delegates_approved_policy(tmp_path, monkeypatch):
    root, config, result, _ = prepared(tmp_path, monkeypatch, task_data=request(repair_limit=1))
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    FakeController.calls = []
    fresh_runner = FakeTests([passing_test()])
    outcome = run_task(result.plan_path, result.approval_token, config, test_runner=fresh_runner, controller_factory=FakeController)
    assert outcome.run_record.final_status == "READY_FOR_HUMAN_REVIEW"
    assert fresh_runner.calls == 1
    used_config, task, scope, baseline, _ = FakeController.calls[0]
    assert used_config.max_repair_loops == 1 and baseline is fresh_runner.results[0]
    assert "Task ID: task-one" in task and scope.allowed_paths == ["src/placeholder.py"]
    assert outcome.run_record.human_review_required is True


def test_stale_head_and_policy_are_rejected_before_controller(tmp_path, monkeypatch):
    root, config, result, _ = prepared(tmp_path, monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    (root / "src" / "placeholder.py").write_text("changed", encoding="utf-8")
    with pytest.raises(Exception) as error:
        run_task(result.plan_path, result.approval_token, config, controller_factory=FakeController)
    assert getattr(error.value, "status", None) == "PLAN_STALE"


@pytest.mark.parametrize("role", ["coordinator", "codex"])
def test_reasoning_effort_drift_makes_approved_plan_stale(tmp_path, monkeypatch, role):
    root, config, result, _ = prepared(tmp_path, monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    drifted = config_for(root, **{role: ModelConfig(model="gpt-5.6-luna", reasoning_effort="high")})
    with pytest.raises(O5Error) as error:
        run_task(result.plan_path, result.approval_token, drifted, controller_factory=FakeController)
    assert error.value.status == "PLAN_STALE"


def test_single_use_marker_and_final_evidence(tmp_path, monkeypatch):
    root, config, result, _ = prepared(tmp_path, monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    FakeController.calls = []
    fresh_runner = FakeTests([passing_test()])
    first = run_task(result.plan_path, result.approval_token, config, test_runner=fresh_runner, controller_factory=FakeController)
    assert first.run_record.final_status == "READY_FOR_HUMAN_REVIEW"
    assert first.run_record.final_evidence["diff_sha256"]
    with pytest.raises(O5Error) as error:
        run_task(result.plan_path, result.approval_token, config, test_runner=FakeTests([passing_test()]), controller_factory=FakeController)
    assert error.value.status == "PLAN_ALREADY_EXECUTED"
    assert len(FakeController.calls) == 1


def test_active_lock_fails_closed_and_is_released(tmp_path, monkeypatch):
    root, config, result, _ = prepared(tmp_path, monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "fake")
    lock = config.run_log_directory / "active-task.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    lock.write_text("unexplained lock", encoding="utf-8")
    with pytest.raises(O5Error) as error:
        run_task(result.plan_path, result.approval_token, config, test_runner=FakeTests([passing_test()]), controller_factory=FakeController)
    assert error.value.status == "ANOTHER_TASK_ACTIVE"
    lock.unlink()
    run_task(result.plan_path, result.approval_token, config, test_runner=FakeTests([passing_test()]), controller_factory=FakeController)
    assert not lock.exists()


def test_o4_failure_preserves_technical_status(tmp_path, monkeypatch):
    root, config, result, _ = prepared(tmp_path, monkeypatch)
    monkeypatch.setenv("OPENAI_API_KEY", "fake")

    class FailedController(FakeController):
        def run(self, task, scope, baseline_test_result, **kwargs):
            record = RunRecord(run_id="o4-fail", task_id="task-one", stage="bounded-repair", final_status="REVIEW_FAILED", error="review failed")
            return O4Result(record, baseline_test_result, None)

    outcome = run_task(result.plan_path, result.approval_token, config, test_runner=FakeTests([passing_test()]), controller_factory=FailedController)
    assert outcome.run_record.final_status == "TECHNICAL_FAILED: REVIEW_FAILED"


def test_canonical_task_text_is_reproducible():
    plan = PreparedTaskPlan.model_validate({
        "schema_version": 1, "task_id": "task-one", "title": "Title", "objective": "Objective", "acceptance_criteria": ["First", "Second"],
        "allowed_paths": ["src/a.py"], "allowed_roots": [], "forbidden_paths": [], "scope_risk": "NARROW", "baseline_head_sha": "h", "baseline_branch": "main",
        "baseline_test_status": "PASS", "baseline_test_exit_code": 0, "test_command": "pytest", "test_timeout_seconds": 1.0, "coordinator_model": "review", "coordinator_reasoning_effort": "medium", "codex_model": "codex", "codex_reasoning_effort": "medium",
        "configured_max_repair_loops": 2, "approved_repair_limit": 2, "prepared_at": "now", "repository_path": "root", "plan_fingerprint": "f", "approval_token": "f" * 16,
    })
    assert canonical_task_text(plan) == canonical_task_text(plan)


def test_cli_task_prepare_and_task_run_return_success(tmp_path, monkeypatch, capsys):
    plan = SimpleNamespace(
        task_id="task-one", baseline_head_sha="head", baseline_test_status="PASS", scope_risk="NARROW",
        allowed_paths=["src/placeholder.py"], allowed_roots=[], approved_repair_limit=2,
        codex_model="codex", codex_reasoning_effort="medium", coordinator_model="review", coordinator_reasoning_effort="medium",
    )
    prepared_result = SimpleNamespace(plan=plan, plan_path=tmp_path / "plan.json", approval_token="0123456789abcdef")
    monkeypatch.setattr("formula_orchestrator.cli.prepare_task", lambda task_file, config: prepared_result)
    assert main(["task-prepare", "--task-file", "task.json"]) == 0
    output = capsys.readouterr().out
    assert "Codex model: codex" in output and "Codex reasoning: medium" in output
    assert "Reviewer model: review" in output and "Reviewer reasoning: medium" in output
    assert "No Codex execution has occurred" in output
    run_result = SimpleNamespace(run_record=SimpleNamespace(final_status="READY_FOR_HUMAN_REVIEW", error=None))
    monkeypatch.setattr("formula_orchestrator.cli.run_task", lambda plan_file, token, config: run_result)
    assert main(["task-run", "--plan-file", "plan.json", "--approve", "0123456789abcdef"]) == 0
    assert "READY FOR HUMAN REVIEW" in capsys.readouterr().out


def test_cli_task_run_failure_returns_nonzero(tmp_path, monkeypatch, capsys):
    result = SimpleNamespace(run_record=SimpleNamespace(final_status="TECHNICAL_FAILED: REVIEW_FAILED", error="review failed"))
    monkeypatch.setattr("formula_orchestrator.cli.run_task", lambda plan_file, token, config: result)
    assert main(["task-run", "--plan-file", "plan.json", "--approve", "0123456789abcdef"]) == 1
    assert "TECHNICAL_FAILED: REVIEW_FAILED" in capsys.readouterr().out
