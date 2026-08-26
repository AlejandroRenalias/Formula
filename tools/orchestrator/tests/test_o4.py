import json
import subprocess

import pytest

from formula_orchestrator.codex_executor import CodexExecutionResult
from formula_orchestrator.config import OrchestratorConfig
from formula_orchestrator.evidence import ReviewInput
from formula_orchestrator.mutation import capture_baseline, capture_execution_snapshot, verify_mutation
from formula_orchestrator.o4 import BoundedRepairController, run_repair_smoke
from formula_orchestrator.repair import RepairRequest, RepairTrigger, build_repair_prompt
from formula_orchestrator.reviewer import ReviewDecision, ReviewResult, ReviewVerdict
from formula_orchestrator.scope import TaskScope
from formula_orchestrator.test_runner import TestRunResult
from .test_preflight import make_repo


def passing_test(text="passed"):
    return TestRunResult(("pytest",), 0, True, text, "", 0.1, False)


def failing_test(text="failed", code=1, error=None, timed_out=False):
    return TestRunResult(("pytest",), code, False, text, "details", 0.1, timed_out, error)


def pass_review():
    return ReviewResult(True, ReviewDecision(verdict="PASS", summary="No task issue found."), duration_seconds=0.1)


def fix_review(number="F-1"):
    return ReviewResult(True, ReviewDecision(verdict="FIX", summary="A required repair remains.", findings=[{
        "finding_id": number, "severity": "IMPORTANT", "title": "Required repair", "description": "The implementation is incomplete.",
        "evidence": "The supplied evidence shows the incomplete state.", "required_fix": "Complete the requested behavior.",
    }]), duration_seconds=0.1)


class FakeCodex:
    def __init__(self, actions, results=None):
        self.actions = list(actions); self.results = list(results or []); self.calls = 0; self.prompts = []
    async def execute(self, root, task, model, run_id):
        index = self.calls; self.calls += 1; self.prompts.append(task)
        if index < len(self.actions) and self.actions[index]: self.actions[index](root, task, run_id)
        return self.results[index] if index < len(self.results) else CodexExecutionResult(True, "completed")


class FakeTests:
    def __init__(self, results): self.results = list(results); self.calls = 0
    def run(self, root, command, timeout):
        result = self.results[min(self.calls, len(self.results) - 1)]; self.calls += 1; return result


class RaisingTests:
    calls = 0
    def run(self, root, command, timeout):
        self.calls += 1
        raise RuntimeError("runner exploded")


class FakeReviewer:
    def __init__(self, results): self.results = list(results); self.calls = 0; self.inputs = []
    def review(self, review_input, model):
        self.inputs.append(review_input); result = self.results[min(self.calls, len(self.results) - 1)]; self.calls += 1; return result


def config_for(root, **kwargs):
    return OrchestratorConfig(repository_root=root, run_log_directory=root / "tools" / "orchestrator" / ".run-logs", **kwargs)


def scope_for(root): return TaskScope(root, allowed_paths=("src/placeholder.py",))


def mutate_allowed(root, task, run_id): (root / "src" / "placeholder.py").write_text("changed", encoding="utf-8")


def run_controller(tmp_path, monkeypatch, tests, reviews, actions=None, results=None, **config_kwargs):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    codex = FakeCodex(actions or [mutate_allowed] * 3, results)
    test_runner = FakeTests(tests); reviewer = FakeReviewer(reviews)
    result = BoundedRepairController(config_for(root, **config_kwargs)).run("Implement the bounded task.", scope_for(root), passing_test(), codex, test_runner, reviewer)
    return result, codex, test_runner, reviewer, root


def test_immediate_success_has_no_repair(tmp_path, monkeypatch):
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [passing_test()], [pass_review()])
    assert result.run_record.final_status == "SUCCESS" and codex.calls == tests.calls == reviewer.calls == 1


def test_one_test_repair(tmp_path, monkeypatch):
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [failing_test(), passing_test()], [pass_review()])
    assert result.run_record.final_status == "SUCCESS" and codex.calls == tests.calls == 2 and reviewer.calls == 1
    assert result.run_record.cycles[1]["repair_trigger"] == "TEST_FAILURE"


@pytest.mark.parametrize("result", [
    TestRunResult(("pytest",), None, False, "", "", 0.1, True, "Test command timed out"),
    TestRunResult(("pytest",), None, False, "", "", 0.1, False, "Test command could not execute"),
    TestRunResult(("pytest",), 2, False, "", "", 0.1, False, None),
    TestRunResult(("pytest",), 3, False, "", "", 0.1, False, None),
    TestRunResult(("pytest",), 4, False, "", "", 0.1, False, None),
    TestRunResult(("pytest",), 5, False, "", "", 0.1, False, None),
])
def test_test_infrastructure_failure_never_consumes_repair_budget(tmp_path, monkeypatch, result):
    outcome, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [result], [pass_review()])
    assert outcome.run_record.final_status == "TEST_INFRA_FAILED"
    assert outcome.run_record.repair_count == 0
    assert codex.calls == tests.calls == 1 and reviewer.calls == 0
    assert outcome.run_record.cycles[0]["cycle_status"] == "TEST_INFRA_FAILED"


def test_test_runner_exception_is_infrastructure_failure(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    codex = FakeCodex([mutate_allowed]); tests = RaisingTests(); reviewer = FakeReviewer([pass_review()])
    outcome = BoundedRepairController(config_for(root)).run("task", scope_for(root), passing_test(), codex, tests, reviewer)
    assert outcome.run_record.final_status == "TEST_INFRA_FAILED"
    assert outcome.run_record.repair_count == 0 and codex.calls == 1 and reviewer.calls == 0


def test_one_review_repair(tmp_path, monkeypatch):
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [passing_test(), passing_test()], [fix_review(), pass_review()])
    assert result.run_record.final_status == "SUCCESS" and codex.calls == tests.calls == reviewer.calls == 2


def test_mixed_two_repairs_success_has_three_codex_calls(tmp_path, monkeypatch):
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [failing_test(), passing_test(), passing_test()], [fix_review(), pass_review()])
    assert result.run_record.final_status == "SUCCESS" and codex.calls == 3 and tests.calls == 3 and reviewer.calls == 2
    assert result.run_record.repair_count == 2


def test_test_repair_limit_has_no_fourth_codex_call(tmp_path, monkeypatch):
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [failing_test()] * 3, [], max_repair_loops=2)
    assert result.run_record.final_status == "REPAIR_LIMIT_REACHED" and codex.calls == 3 and tests.calls == 3 and reviewer.calls == 0
    assert result.run_record.last_failure == "TEST_FAILED"


def test_reviewer_repair_limit_has_no_fourth_codex_call(tmp_path, monkeypatch):
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [passing_test()] * 3, [fix_review("F-1"), fix_review("F-2"), fix_review("F-3")])
    assert result.run_record.final_status == "REPAIR_LIMIT_REACHED" and codex.calls == tests.calls == reviewer.calls == 3
    assert result.run_record.last_failure == "REVIEW_FIX_REQUIRED"


def test_global_budget_allows_one_test_and_one_review_repair(tmp_path, monkeypatch):
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [failing_test(), passing_test(), passing_test()], [fix_review(), pass_review()])
    assert result.run_record.final_status == "SUCCESS" and result.run_record.repair_count == 2


def test_zero_repair_budget_stops_after_initial_failure(tmp_path, monkeypatch):
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [failing_test()], [], max_repair_loops=0)
    assert result.run_record.final_status == "REPAIR_LIMIT_REACHED" and codex.calls == tests.calls == 1 and reviewer.calls == 0


def test_safety_failure_after_initial_skips_tests_and_review(tmp_path, monkeypatch):
    def unsafe(root, task, run_id): (root / "tests" / "bad.py").write_text("bad")
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [passing_test()], [pass_review()], actions=[unsafe])
    assert result.run_record.final_status == "SAFETY_FAILED" and tests.calls == reviewer.calls == 0


def test_safety_failure_after_repair_stops(tmp_path, monkeypatch):
    def unsafe(root, task, run_id): (root / "tests" / "bad.py").write_text("bad")
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [failing_test(), passing_test()], [pass_review()], actions=[mutate_allowed, unsafe])
    assert result.run_record.final_status == "SAFETY_FAILED" and codex.calls == 2 and tests.calls == 1 and reviewer.calls == 0


def test_codex_repair_failure_has_no_infrastructure_retry(tmp_path, monkeypatch):
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [failing_test(), passing_test()], [], results=[CodexExecutionResult(True, "ok"), CodexExecutionResult(False, error="repair API failed")])
    assert result.run_record.final_status == "REPAIR_EXECUTION_FAILED" and codex.calls == 2 and tests.calls == 1 and reviewer.calls == 0


def test_reviewer_failure_has_no_repair(tmp_path, monkeypatch):
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [passing_test()], [ReviewResult(False, error="review API failed")])
    assert result.run_record.final_status == "REVIEW_FAILED" and codex.calls == tests.calls == reviewer.calls == 1


def test_oversized_repair_input_skips_repair_executor(tmp_path, monkeypatch):
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [failing_test("x" * 100)], [], repair_max_input_chars=10)
    assert result.run_record.final_status == "REPAIR_INPUT_TOO_LARGE" and codex.calls == 1 and tests.calls == 1


def test_fresh_test_evidence_reaches_next_repair_prompt(tmp_path, monkeypatch):
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [failing_test("first"), failing_test("newest")], [], max_repair_loops=2)
    assert result.run_record.final_status == "REPAIR_LIMIT_REACHED" and "newest" in codex.prompts[2] and "first" not in codex.prompts[2]


def test_fresh_git_evidence_reaches_reviewer(tmp_path, monkeypatch):
    result, codex, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [passing_test(), passing_test()], [fix_review(), pass_review()])
    assert "placeholder.py" in reviewer.inputs[0].git_diff and reviewer.inputs[0].run_id == result.run_record.run_id
    assert len(reviewer.inputs) == 2


def test_max_repair_loops_above_two_is_rejected(tmp_path):
    root = make_repo(tmp_path)
    with pytest.raises(ValueError, match="cannot exceed 2"):
        OrchestratorConfig(repository_root=root, max_repair_loops=3)


def test_mutation_verifier_rejects_head_branch_and_index_changes(tmp_path):
    root = make_repo(tmp_path); baseline = capture_baseline(root); before = capture_execution_snapshot(root)
    (root / "src" / "placeholder.py").write_text("changed")
    subprocess.run(["git", "add", "src/placeholder.py"], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "mutated"], cwd=root, check=True)
    after = capture_execution_snapshot(root)
    check = verify_mutation(baseline, before, after, TaskScope(root, allowed_paths=("src/placeholder.py",)))
    assert not check.passed and any("HEAD changed" in item or "staged path" in item for item in check.violations)


def test_mutation_verifier_rejects_branch_change(tmp_path):
    root = make_repo(tmp_path); baseline = capture_baseline(root); before = capture_execution_snapshot(root)
    subprocess.run(["git", "checkout", "-qb", "unexpected-branch"], cwd=root, check=True)
    after = capture_execution_snapshot(root)
    check = verify_mutation(baseline, before, after, TaskScope(root, allowed_paths=("src/placeholder.py",)))
    assert not check.passed and "branch/ref changed" in check.violations


def test_unhealthy_baseline_stops_before_codex(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    codex = FakeCodex([mutate_allowed]); tests = FakeTests([failing_test()]); reviewer = FakeReviewer([])
    result = BoundedRepairController(config_for(root)).run("task", scope_for(root), failing_test(), codex, tests, reviewer)
    assert result.run_record.final_status == "BASELINE_UNHEALTHY" and codex.calls == 0 and tests.calls == reviewer.calls == 0


def test_out_of_scope_path_is_rejected(tmp_path, monkeypatch):
    def unsafe(root, task, run_id): (root / "README.md").write_text("unsafe")
    result, _, tests, reviewer, _ = run_controller(tmp_path, monkeypatch, [passing_test()], [pass_review()], actions=[unsafe])
    assert result.run_record.final_status == "SAFETY_FAILED" and tests.calls == reviewer.calls == 0


def test_repair_prompt_contains_constraints_and_structured_trigger():
    prompt = build_repair_prompt(RepairRequest("run", 1, RepairTrigger.TEST_FAILURE, "task", "scope", ("src/a.py",), "diff", ("src/a.py",), "pytest", 1, "failed", "stderr", constraints="no broadening"), 10_000)
    assert "Do not commit, stage" in prompt and "TEST_FAILURE" in prompt and "no broadening" in prompt


def test_repair_smoke_uses_one_codex_repair_and_two_reviews(tmp_path, monkeypatch):
    root = make_repo(tmp_path); monkeypatch.setenv("OPENAI_API_KEY", "fake")
    def repair(root, task, run_id):
        path = root / "tools" / "orchestrator" / ".run-logs" / f"repair-smoke-{run_id}.txt"
        path.write_text("status=ready\n", encoding="utf-8")
    codex = FakeCodex([repair]); reviewer = FakeReviewer([fix_review(), pass_review()])
    result = run_repair_smoke(config_for(root), codex, reviewer)
    assert result.run_record.final_status == "SUCCESS" and codex.calls == 1 and reviewer.calls == 2
    assert "status=needs-repair" in reviewer.inputs[0].test_stdout
    assert "status=ready" in reviewer.inputs[1].test_stdout
    assert reviewer.inputs[0].test_stdout != reviewer.inputs[1].test_stdout
    assert not subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True).stdout
