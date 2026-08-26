import json
from pathlib import Path

from formula_orchestrator.codex_executor import CodexExecutionResult
from formula_orchestrator.config import OrchestratorConfig
from formula_orchestrator.o2 import run_codex_test_smoke
from formula_orchestrator.test_runner import TestGateStatus, TestRunResult
from .test_preflight import make_repo


class FakeCodex:
    def __init__(self, action): self.calls, self.action = 0, action
    async def execute(self, root, task, model, run_id):
        self.calls += 1
        self.action(root, task, run_id)
        return CodexExecutionResult(True, "summary", "thread-2", {"total_tokens": 8})


class FakeTests:
    def __init__(self, result): self.calls, self.result = 0, result
    def run(self, root, command, timeout): self.calls += 1; return self.result


def config_for(root):
    return OrchestratorConfig(repository_root=root, run_log_directory=root / "tools" / "orchestrator" / ".run-logs")


def marker(root, task, run_id):
    path = root / "tools" / "orchestrator" / ".run-logs" / f"codex-smoke-{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"run_id": run_id, "task_type": "codex-smoke"}), encoding="utf-8")


def test_complete_flow_calls_codex_and_tests_once(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    passing = TestRunResult(("pytest",), 0, True, "63 passed", "", 0.2, False)
    codex, tests = FakeCodex(marker), FakeTests(passing)
    result = run_codex_test_smoke(config_for(root), codex, tests)
    assert codex.calls == 1 and tests.calls == 1 and result.run_record.final_status == "O2_SUCCESS"


def test_codex_failure_skips_tests(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    class Failed(FakeCodex):
        async def execute(self, *args): self.calls += 1; return CodexExecutionResult(False, error="codex failed")
    tests = FakeTests(None); result = run_codex_test_smoke(config_for(root), Failed(None), tests)
    assert tests.calls == 0 and result.run_record.final_status == "O2_CODEX_FAILED"


def test_safety_failure_skips_tests(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    def unsafe(root, task, run_id): (root / "src" / "placeholder.py").write_text("unsafe")
    tests = FakeTests(None); result = run_codex_test_smoke(config_for(root), FakeCodex(unsafe), tests)
    assert tests.calls == 0 and result.run_record.final_status == "O2_SAFETY_FAILED"


def test_test_failure_is_recorded(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    failing = TestRunResult(("pytest",), 1, False, "failed", "details", 0.3, False, "test command failed")
    tests = FakeTests(failing); result = run_codex_test_smoke(config_for(root), FakeCodex(marker), tests)
    assert result.run_record.final_status == "O2_TEST_FAILED"
    assert result.run_record.test_gate_status == TestGateStatus.FAIL.value
    assert result.run_record.test_exit_code == 1 and tests.calls == 1


def test_test_timeout_is_failure(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    timed_out = TestRunResult(("pytest",), None, False, "", "", 300.0, True, "Test command timed out")
    result = run_codex_test_smoke(config_for(root), FakeCodex(marker), FakeTests(timed_out))
    assert result.run_record.final_status == "O2_TEST_FAILED" and result.run_record.test_timed_out is True

