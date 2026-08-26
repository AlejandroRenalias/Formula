import asyncio
import json
from pathlib import Path

from formula_orchestrator.codex_executor import CodexExecutionResult
from formula_orchestrator.config import OrchestratorConfig
from formula_orchestrator.preflight import PreflightError
from formula_orchestrator.smoke import run_smoke
from .test_preflight import make_repo


class FakeExecutor:
    def __init__(self, action=None):
        self.calls = 0
        self.action = action

    async def execute(self, repository_root, task_text, model, run_id):
        self.calls += 1
        assert repository_root.is_dir()
        assert "Do not modify src/" in task_text
        if self.action:
            self.action(repository_root, task_text, run_id)
        return CodexExecutionResult(success=True, response_text="summary", thread_id="thread-1", usage={"total_tokens": 7})


def config_for(root: Path) -> OrchestratorConfig:
    return OrchestratorConfig(repository_root=root, run_log_directory=root / "tools" / "orchestrator" / ".run-logs")


def write_marker(root: Path, task_text: str, run_id: str) -> None:
    marker = root / "tools" / "orchestrator" / ".run-logs" / f"codex-smoke-{run_id}.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(json.dumps({"run_id": run_id, "task_type": "codex-smoke", "summary": "Formula F1 strategy project"}), encoding="utf-8")


def test_success_invokes_boundary_once_and_records_result(tmp_path: Path, monkeypatch) -> None:
    root = make_repo(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    fake = FakeExecutor(action=write_marker)
    result = run_smoke(config_for(root), fake)
    assert fake.calls == 1
    assert result.run_record.final_status == "SUCCESS"
    assert result.run_record.codex_thread_id == "thread-1"
    assert result.safety and result.safety.passed
    assert Path(result.run_record.smoke_marker_path).is_file()


def test_dirty_repository_does_not_invoke_codex(tmp_path: Path, monkeypatch) -> None:
    root = make_repo(tmp_path)
    (root / "dirty.txt").write_text("change", encoding="utf-8")
    fake = FakeExecutor()
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    try:
        run_smoke(config_for(root), fake)
    except PreflightError:
        pass
    else:
        raise AssertionError("dirty repository should fail")
    assert fake.calls == 0


def test_missing_credential_does_not_invoke_codex_or_display_secret(tmp_path: Path, monkeypatch, capsys) -> None:
    root = make_repo(tmp_path)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    fake = FakeExecutor()
    try:
        run_smoke(config_for(root), fake)
    except PreflightError as exc:
        assert "missing" in str(exc)
        assert "test-secret" not in str(exc)
    else:
        raise AssertionError("missing credential should fail")
    assert fake.calls == 0
    assert "test-secret" not in capsys.readouterr().out


def test_codex_failure_is_recorded_without_retry(tmp_path: Path, monkeypatch) -> None:
    root = make_repo(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")

    class FailedExecutor(FakeExecutor):
        async def execute(self, *args):
            self.calls += 1
            return CodexExecutionResult(success=False, error="tool failed")

    fake = FailedExecutor()
    result = run_smoke(config_for(root), fake)
    assert fake.calls == 1
    assert result.run_record.final_status == "CODEX_FAILED"
    assert result.run_record.error == "tool failed"


def test_unexpected_tracked_change_is_reported_and_not_reverted(tmp_path: Path, monkeypatch) -> None:
    root = make_repo(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")

    def mutate(root, task, run_id):
        (root / "src" / "placeholder.py").write_text("changed", encoding="utf-8")
        write_marker(root, task, run_id)

    result = run_smoke(config_for(root), FakeExecutor(action=mutate))
    assert result.run_record.final_status == "SAFETY_FAILED"
    assert "placeholder.py" in result.run_record.error
    assert (root / "src" / "placeholder.py").read_text(encoding="utf-8") == "changed"


def test_unexpected_untracked_file_is_reported(tmp_path: Path, monkeypatch) -> None:
    root = make_repo(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")

    def mutate(root, task, run_id):
        (root / "unexpected.txt").write_text("unexpected", encoding="utf-8")
        write_marker(root, task, run_id)

    result = run_smoke(config_for(root), FakeExecutor(action=mutate))
    assert result.run_record.final_status == "SAFETY_FAILED"
    assert "unexpected.txt" in result.run_record.error


def test_missing_marker_fails_successful_codex_result(tmp_path: Path, monkeypatch) -> None:
    root = make_repo(tmp_path)
    monkeypatch.setenv("OPENAI_API_KEY", "test-secret")
    result = run_smoke(config_for(root), FakeExecutor())
    assert result.run_record.final_status == "SAFETY_FAILED"
    assert "marker is missing" in result.run_record.error


def test_run_record_does_not_store_credential(tmp_path: Path, monkeypatch) -> None:
    root = make_repo(tmp_path)
    secret = "test-secret-value"
    monkeypatch.setenv("OPENAI_API_KEY", secret)
    result = run_smoke(config_for(root), FakeExecutor(action=write_marker))
    serialized = (config_for(root).run_log_directory / f"{result.run_record.run_id}.json").read_text(encoding="utf-8")
    assert secret not in serialized
    assert "OPENAI_API_KEY" not in serialized
