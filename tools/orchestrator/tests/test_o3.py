import json

from formula_orchestrator.codex_executor import CodexExecutionResult
from formula_orchestrator.config import OrchestratorConfig
from formula_orchestrator.evidence import ReviewInput
from formula_orchestrator.o3 import run_codex_test_review_smoke, run_review_smoke
from formula_orchestrator.reviewer import ReviewDecision, ReviewResult
from formula_orchestrator.test_runner import TestRunResult
from .test_preflight import make_repo


class FakeCodex:
    def __init__(self, action): self.calls, self.action = 0, action
    async def execute(self, root, task, model, run_id):
        self.calls += 1
        self.action(root, task, run_id)
        return CodexExecutionResult(True, "Codex claims the marker was created.", "thread-3", {"total_tokens": 9})


class FakeTests:
    def __init__(self, result): self.calls, self.result = 0, result
    def run(self, root, command, timeout): self.calls += 1; return self.result


class FakeReviewer:
    def __init__(self, result): self.calls, self.result, self.input = 0, result, None
    def review(self, review_input, model): self.calls += 1; self.input = review_input; return self.result


def config_for(root, **kwargs):
    return OrchestratorConfig(repository_root=root, run_log_directory=root / "tools" / "orchestrator" / ".run-logs", **kwargs)


def marker(root, task, run_id):
    path = root / "tools" / "orchestrator" / ".run-logs" / f"codex-smoke-{run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"run_id": run_id, "task_type": "codex-smoke"}), encoding="utf-8")


def passing_tests(): return TestRunResult(("pytest",), 0, True, "63 passed", "", 0.1, False)


def passing_review(): return ReviewResult(True, ReviewDecision(verdict="PASS", summary="The smoke evidence satisfies the task."), {"total_tokens": 5}, 0.2)


def test_reviewer_runs_only_after_passing_codex_safety_and_tests(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake-secret")
    codex, tests, reviewer = FakeCodex(marker), FakeTests(passing_tests()), FakeReviewer(passing_review())
    result = run_codex_test_review_smoke(config_for(root), codex, tests, reviewer)
    assert codex.calls == tests.calls == reviewer.calls == 1
    assert result.run_record.final_status == "SUCCESS"
    assert result.run_record.review_verdict == "PASS"


def test_codex_failure_skips_tests_and_review(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    class Failed(FakeCodex):
        async def execute(self, *args): self.calls += 1; return CodexExecutionResult(False, error="codex failed")
    tests, reviewer = FakeTests(passing_tests()), FakeReviewer(passing_review())
    result = run_codex_test_review_smoke(config_for(root), Failed(None), tests, reviewer)
    assert result.run_record.final_status == "CODEX_FAILED" and tests.calls == reviewer.calls == 0


def test_safety_failure_skips_tests_and_review(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    def unsafe(root, task, run_id): (root / "src" / "placeholder.py").write_text("unsafe")
    tests, reviewer = FakeTests(passing_tests()), FakeReviewer(passing_review())
    result = run_codex_test_review_smoke(config_for(root), FakeCodex(unsafe), tests, reviewer)
    assert result.run_record.final_status == "SAFETY_FAILED" and tests.calls == reviewer.calls == 0


def test_test_failure_skips_review(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    failed = TestRunResult(("pytest",), 1, False, "failed", "", 0.1, False, "test command failed")
    tests, reviewer = FakeTests(failed), FakeReviewer(passing_review())
    result = run_codex_test_review_smoke(config_for(root), FakeCodex(marker), tests, reviewer)
    assert result.run_record.final_status == "TEST_FAILED" and tests.calls == 1 and reviewer.calls == 0


def test_fix_stops_without_repair(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    fix = ReviewResult(True, ReviewDecision(verdict="FIX", summary="A required issue remains.", findings=[{"finding_id": "F-1", "severity": "BLOCKER", "title": "Issue", "description": "Fix needed.", "evidence": "Evidence", "required_fix": "Fix it."}]), duration_seconds=0.1)
    codex, tests, reviewer = FakeCodex(marker), FakeTests(passing_tests()), FakeReviewer(fix)
    result = run_codex_test_review_smoke(config_for(root), codex, tests, reviewer)
    assert result.run_record.final_status == "REVIEW_FIX_REQUIRED"
    assert codex.calls == tests.calls == reviewer.calls == 1


def test_reviewer_failure_is_safe_failure(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    failed = ReviewResult(False, error="API failure")
    result = run_codex_test_review_smoke(config_for(root), FakeCodex(marker), FakeTests(passing_tests()), FakeReviewer(failed))
    assert result.run_record.final_status == "REVIEW_FAILED"


def test_oversized_evidence_skips_reviewer(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    import formula_orchestrator.o3 as o3
    from formula_orchestrator.evidence import EvidenceError
    monkeypatch.setattr(o3, "collect_git_evidence", lambda *args: (_ for _ in ()).throw(EvidenceError("diff too large")))
    reviewer = FakeReviewer(passing_review())
    result = run_codex_test_review_smoke(config_for(root), FakeCodex(marker), FakeTests(passing_tests()), reviewer)
    assert result.run_record.final_status == "REVIEW_INPUT_TOO_LARGE" and reviewer.calls == 0


def test_review_input_redacts_credentials_and_review_smoke_has_no_codex(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "fake-review-secret")
    captured = FakeReviewer(passing_review())
    result = run_review_smoke(config_for(tmp_path), captured)
    assert result.run_record.final_status == "SUCCESS" and captured.calls == 1
    assert "fake-review-secret" not in captured.input.to_prompt()
