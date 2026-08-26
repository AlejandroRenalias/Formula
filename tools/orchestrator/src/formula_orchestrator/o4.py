"""Python-owned bounded repair controller and isolated repair smoke."""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol

from .codex_executor import CodexExecutionResult, CodexExecutor
from .config import OrchestratorConfig
from .evidence import EvidenceError, ReviewInput, collect_git_evidence, sanitize_review_input
from .mutation import MutationCheck, MutationSafetyError, capture_baseline, capture_execution_snapshot, verify_mutation
from .repair import RepairRequest, RepairTrigger, build_repair_prompt
from .reviewer import ReviewResult, ReviewVerdict
from .run_record import RunRecord
from .scope import TaskScope
from .smoke import ExecutorProtocol, require_authentication, _write_record
from .test_runner import FormulaTestRunner, TestRunResult, is_repairable_test_failure


class ReviewerProtocol(Protocol):
    def review(self, review_input: ReviewInput, model) -> ReviewResult: ...


class TestRunnerProtocol(Protocol):
    def run(self, repository_root: Path, command: str, timeout_seconds: float) -> TestRunResult: ...


@dataclass(frozen=True)
class O4Result:
    run_record: RunRecord
    last_test_result: TestRunResult | None = None
    last_review_result: ReviewResult | None = None


class FixtureObservationError(RuntimeError):
    pass


@dataclass(frozen=True)
class FixtureObservation:
    path: Path
    content: str

    @property
    def evidence(self) -> str:
        return f"observed_content={self.content!r}"


def observe_fixture(path: Path, max_chars: int = 4_096) -> FixtureObservation:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise FixtureObservationError(f"Could not read repair-smoke fixture: {exc}") from exc
    if len(content) > max_chars:
        raise FixtureObservationError("Repair-smoke fixture observation exceeds the configured bound")
    return FixtureObservation(path, content)


class BoundedRepairController:
    """Own all O4 counters, transitions, scope checks, and stop conditions."""

    def __init__(self, config: OrchestratorConfig) -> None:
        self.config = config

    def run(
        self,
        original_task: str,
        scope: TaskScope,
        baseline_test_result: TestRunResult,
        executor: ExecutorProtocol | None = None,
        test_runner: TestRunnerProtocol | None = None,
        reviewer: ReviewerProtocol | None = None,
    ) -> O4Result:
        self._validate_scope(scope)
        from .preflight import run_preflight

        run_preflight(self.config)
        baseline = capture_baseline(self.config.repository_root)
        require_authentication()
        record = self._new_record(baseline, "bounded-repair")
        if not baseline_test_result.passed:
            record.final_status = "BASELINE_UNHEALTHY"
            record.last_failure = "BASELINE_UNHEALTHY"
            record.error = "A successful baseline test result is required before automatic repair"
            _write_record(self.config, record)
            return O4Result(record)

        executor = executor or CodexExecutor()
        test_runner = test_runner or FormulaTestRunner()
        reviewer = reviewer or self._default_reviewer()
        repair_count = 0
        execution_index = 0
        execution_type = "INITIAL"
        repair_attempt = 0
        repair_trigger: RepairTrigger | None = None
        task_text = self._initial_prompt(original_task, scope)
        last_test: TestRunResult | None = None
        last_review: ReviewResult | None = None

        while True:
            execution_index += 1
            codex_result, mutation, execution_delta = self._execute_once(
                executor, task_text, record.run_id, baseline, scope
            )
            record.codex_success = codex_result.success
            record.codex_thread_id = codex_result.thread_id
            record.usage_summary = codex_result.usage
            if not mutation.passed:
                self._append_cycle(record, execution_index, execution_type, repair_attempt, repair_trigger, mutation, None, None, "SAFETY_FAILED")
                record.final_status = "SAFETY_FAILED"
                record.error = mutation.message
                record.finished_at = _now()
                _write_record(self.config, record)
                return O4Result(record, last_test, last_review)
            if not codex_result.success:
                self._append_cycle(record, execution_index, execution_type, repair_attempt, repair_trigger, mutation, None, None, "CODEX_FAILED")
                record.final_status = "REPAIR_EXECUTION_FAILED" if execution_type == "REPAIR" else "CODEX_FAILED"
                record.error = codex_result.error or "Codex execution failed"
                record.finished_at = _now()
                _write_record(self.config, record)
                return O4Result(record, last_test, last_review)

            try:
                last_test = test_runner.run(self.config.repository_root, self.config.test_command, self.config.test_timeout_seconds)
            except Exception as exc:
                last_test = TestRunResult((self.config.test_command,), None, False, "", "", 0.0, False, f"Test runner failed: {exc}")
            record.test_gate_status = last_test.gate_status.value
            record.test_exit_code = last_test.exit_code
            record.test_duration_seconds = last_test.duration_seconds
            record.test_timed_out = last_test.timed_out
            record.test_output = {"stdout": last_test.stdout, "stderr": last_test.stderr}
            if not last_test.passed:
                if not is_repairable_test_failure(last_test):
                    self._append_cycle(record, execution_index, execution_type, repair_attempt, repair_trigger, mutation, last_test, None, "TEST_INFRA_FAILED")
                    record.final_status = "TEST_INFRA_FAILED"
                    record.last_failure = "TEST_INFRA_FAILED"
                    record.error = _test_infrastructure_error(last_test)
                    record.finished_at = _now()
                    _write_record(self.config, record)
                    return O4Result(record, last_test, last_review)
                self._append_cycle(record, execution_index, execution_type, repair_attempt, repair_trigger, mutation, last_test, None, "TEST_FAILED")
                record.last_failure = "TEST_FAILED"
                if repair_count >= self.config.max_repair_loops:
                    record.final_status = "REPAIR_LIMIT_REACHED"
                    record.error = "Repair limit reached after deterministic test failure"
                    record.finished_at = _now()
                    _write_record(self.config, record)
                    return O4Result(record, last_test, last_review)
                try:
                    request = self._test_repair_request(record, original_task, scope, mutation, last_test)
                except EvidenceError as exc:
                    record.final_status = "REPAIR_INPUT_TOO_LARGE"
                    record.error = str(exc)
                    record.finished_at = _now()
                    _write_record(self.config, record)
                    return O4Result(record, last_test, last_review)
                try:
                    task_text = build_repair_prompt(request, self.config.repair_max_input_chars)
                except ValueError as exc:
                    record.final_status = "REPAIR_INPUT_TOO_LARGE"
                    record.error = str(exc)
                    record.finished_at = _now()
                    _write_record(self.config, record)
                    return O4Result(record, last_test, last_review)
                repair_count += 1
                record.repair_count = repair_count
                repair_attempt = repair_count
                repair_trigger = RepairTrigger.TEST_FAILURE
                execution_type = "REPAIR"
                continue

            try:
                review_input = self._review_input(original_task, codex_result, mutation, last_test, record.run_id)
            except EvidenceError as exc:
                self._append_cycle(record, execution_index, execution_type, repair_attempt, repair_trigger, mutation, last_test, None, "REVIEW_INPUT_TOO_LARGE")
                record.final_status = "REVIEW_INPUT_TOO_LARGE"
                record.error = str(exc)
                record.finished_at = _now()
                _write_record(self.config, record)
                return O4Result(record, last_test, last_review)
            try:
                last_review = reviewer.review(review_input, self.config.coordinator)
            except Exception as exc:
                last_review = ReviewResult(False, duration_seconds=0.0, error=f"Reviewer execution failed: {exc}")
            record.reviewer_model = self.config.coordinator.model
            record.review_duration_seconds = last_review.duration_seconds
            record.review_usage = last_review.usage
            record.review_verdict = last_review.decision.verdict.value if last_review.decision else None
            record.review_summary = last_review.decision.summary if last_review.decision else None
            record.review_findings = [finding.model_dump(mode="json") for finding in last_review.decision.findings] if last_review.decision else None
            record.review_error = last_review.error if not last_review.success else None
            self._append_cycle(record, execution_index, execution_type, repair_attempt, repair_trigger, mutation, last_test, last_review, "REVIEWED")
            if not last_review.success or last_review.decision is None:
                record.final_status = "REVIEW_FAILED"
                record.review_error = last_review.error or "Reviewer returned no valid decision"
                record.error = record.review_error
                record.finished_at = _now()
                _write_record(self.config, record)
                return O4Result(record, last_test, last_review)
            if last_review.decision.verdict is ReviewVerdict.PASS:
                record.final_status = "SUCCESS"
                record.finished_at = _now()
                _write_record(self.config, record)
                return O4Result(record, last_test, last_review)

            record.last_failure = "REVIEW_FIX_REQUIRED"
            if repair_count >= self.config.max_repair_loops:
                record.final_status = "REPAIR_LIMIT_REACHED"
                record.error = "Repair limit reached after reviewer FIX"
                record.finished_at = _now()
                _write_record(self.config, record)
                return O4Result(record, last_test, last_review)
            try:
                request = self._review_repair_request(record, original_task, scope, mutation, last_test, last_review.decision.findings)
            except EvidenceError as exc:
                record.final_status = "REPAIR_INPUT_TOO_LARGE"
                record.error = str(exc)
                record.finished_at = _now()
                _write_record(self.config, record)
                return O4Result(record, last_test, last_review)
            try:
                task_text = build_repair_prompt(request, self.config.repair_max_input_chars)
            except ValueError as exc:
                record.final_status = "REPAIR_INPUT_TOO_LARGE"
                record.error = str(exc)
                record.finished_at = _now()
                _write_record(self.config, record)
                return O4Result(record, last_test, last_review)
            repair_count += 1
            record.repair_count = repair_count
            repair_attempt = repair_count
            repair_trigger = RepairTrigger.REVIEW_FINDINGS
            execution_type = "REPAIR"

    def _execute_once(self, executor, task_text, run_id, baseline, scope):
        before = capture_execution_snapshot(self.config.repository_root)
        try:
            result = asyncio.run(executor.execute(self.config.repository_root, task_text, self.config.codex, run_id))
        except Exception as exc:
            result = CodexExecutionResult(False, error=f"Codex execution failed: {exc}")
        try:
            after = capture_execution_snapshot(self.config.repository_root)
            mutation = verify_mutation(baseline, before, after, scope)
            return result, mutation, mutation.delta_paths
        except MutationSafetyError as exc:
            return result, MutationCheck(False, (), (), (str(exc),), str(exc)), ()

    def _review_input(self, original_task, codex_result, mutation, test_result, run_id):
        diff, paths, status = collect_git_evidence(self.config.repository_root, self.config.review_max_diff_chars)
        return sanitize_review_input(ReviewInput(
            task_spec=original_task,
            codex_summary=codex_result.response_text,
            git_diff=diff,
            changed_paths=paths,
            git_status=status,
            test_result=test_result.gate_status.value,
            test_stdout=test_result.stdout,
            test_stderr=test_result.stderr,
            safety_verification=mutation.message,
            run_id=run_id,
        ), self.config.review_max_output_chars)

    def _initial_prompt(self, original_task, scope):
        return f"""{original_task}

This is one bounded workspace execution. Stay inside this supplied scope: {self._scope_text(scope)}.
Do not commit, stage, push, merge, reset, stash, checkout, switch branches, deploy, access credentials, or modify any path outside the allowed scope. Stop after the requested task and summarize observable changes."""

    def _test_repair_request(self, record, original_task, scope, mutation, test_result):
        diff, paths, _ = collect_git_evidence(self.config.repository_root, self.config.review_max_diff_chars)
        return RepairRequest(record.run_id, record.repair_count + 1, RepairTrigger.TEST_FAILURE, original_task, self._scope_text(scope), paths, diff, mutation.delta_paths, self.config.test_command, test_result.exit_code, test_result.stdout, test_result.stderr, constraints="The next execution is one bounded repair only.")

    def _review_repair_request(self, record, original_task, scope, mutation, test_result, findings):
        diff, paths, _ = collect_git_evidence(self.config.repository_root, self.config.review_max_diff_chars)
        return RepairRequest(record.run_id, record.repair_count + 1, RepairTrigger.REVIEW_FINDINGS, original_task, self._scope_text(scope), paths, diff, mutation.delta_paths, self.config.test_command, test_result.exit_code, test_result.stdout, test_result.stderr, tuple(findings), "The next execution is one bounded repair only.")

    def _new_record(self, baseline, task_type):
        return RunRecord(run_id=uuid.uuid4().hex, task_id=uuid.uuid4().hex, task_type=task_type, stage="bounded-repair", started_at=_now(), baseline={"head_sha": baseline.head_sha, "branch": baseline.branch, "status": baseline.status})

    @staticmethod
    def _scope_text(scope):
        return f"allowed_paths={scope.allowed_paths}; allowed_roots={scope.allowed_roots}; forbidden_paths={scope.forbidden_paths}"

    def _validate_scope(self, scope):
        if scope.repository_root != self.config.repository_root:
            raise ValueError("TaskScope repository_root must equal configured Formula repository_root")

    @staticmethod
    def _default_reviewer():
        from .reviewer import GptReviewer
        return GptReviewer()

    @staticmethod
    def _append_cycle(record, execution_index, execution_type, repair_attempt, trigger, mutation, test_result, review_result, cycle_status):
        record.cycles.append({
            "execution_index": execution_index,
            "execution_type": execution_type,
            "repair_attempt": repair_attempt,
            "repair_trigger": trigger.value if trigger else None,
            "changed_paths": list(mutation.changed_paths),
            "mutation_safety": "PASS" if mutation.passed else "FAIL",
            "test_result": test_result.gate_status.value if test_result else None,
            "review_result": review_result.decision.verdict.value if review_result and review_result.decision else ("FAILED" if review_result else None),
            "cycle_status": cycle_status,
        })


def run_repair_smoke(config: OrchestratorConfig, executor: ExecutorProtocol | None = None, reviewer: ReviewerProtocol | None = None) -> O4Result:
    """Verify one review FIX, one scoped Codex repair, and one fresh review."""
    from .preflight import run_preflight
    from .reviewer import GptReviewer

    run_preflight(config)
    baseline = capture_baseline(config.repository_root)
    require_authentication()
    run_id = uuid.uuid4().hex
    fixture = config.run_log_directory / f"repair-smoke-{run_id}.txt"
    record = RunRecord(run_id=run_id, task_id=run_id, task_type="repair-smoke", stage="bounded-repair", started_at=_now(), baseline={"head_sha": baseline.head_sha, "branch": baseline.branch, "status": baseline.status}, repair_count=0)
    try:
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_text("status=needs-repair\n", encoding="utf-8")
    except OSError as exc:
        record.final_status = "FIXTURE_SETUP_FAILED"; record.error = f"Could not create repair-smoke fixture: {exc}"; record.finished_at = _now(); _write_record(config, record)
        return O4Result(record)
    scope = TaskScope(config.repository_root, allowed_paths=(fixture.relative_to(config.repository_root).as_posix(),))
    reviewer = reviewer or GptReviewer()
    executor = executor or CodexExecutor()
    try:
        initial_observation = observe_fixture(fixture)
    except FixtureObservationError as exc:
        record.final_status = "FIXTURE_OBSERVATION_FAILED"; record.error = str(exc); record.finished_at = _now(); _write_record(config, record)
        return O4Result(record)
    initial_input = ReviewInput("The artifact must contain exactly status=ready. The deterministic fixture observation is authoritative evidence.", "Initial fixture observation was collected from disk.", "", (fixture.relative_to(config.repository_root).as_posix(),), "", "PASS", initial_observation.evidence, "", "PASS", run_id)
    try:
        initial_review = reviewer.review(sanitize_review_input(initial_input, config.review_max_output_chars), config.coordinator)
    except Exception as exc:
        initial_review = ReviewResult(False, duration_seconds=0.0, error=f"Reviewer execution failed: {exc}")
    record.review_verdict = initial_review.decision.verdict.value if initial_review.decision else None
    if not initial_review.success or initial_review.decision is None or initial_review.decision.verdict is not ReviewVerdict.FIX:
        record.final_status = "REVIEW_FAILED"
        record.error = "Repair smoke requires the initial reviewer decision to be FIX"
        record.finished_at = _now(); _write_record(config, record)
        return O4Result(record, None, initial_review)
    if config.max_repair_loops < 1:
        record.final_status = "REPAIR_LIMIT_REACHED"
        record.last_failure = "REVIEW_FIX_REQUIRED"
        record.finished_at = _now(); _write_record(config, record)
        return O4Result(record, None, initial_review)

    try:
        before = capture_execution_snapshot(config.repository_root)
    except MutationSafetyError as exc:
        record.final_status = "SAFETY_FAILED"; record.error = str(exc); record.finished_at = _now(); _write_record(config, record)
        return O4Result(record, None, initial_review)
    request = RepairRequest(run_id, 1, RepairTrigger.REVIEW_FINDINGS, "The artifact must contain exactly status=ready.", f"allowed_paths={(fixture.relative_to(config.repository_root).as_posix(),)}", (fixture.relative_to(config.repository_root).as_posix(),), "", (), None, None, "", "", tuple(initial_review.decision.findings), "Modify only the one fixture.")
    try:
        prompt = build_repair_prompt(request, config.repair_max_input_chars)
    except ValueError as exc:
        record.final_status = "REPAIR_INPUT_TOO_LARGE"; record.error = str(exc); record.finished_at = _now(); _write_record(config, record)
        return O4Result(record, None, initial_review)
    try:
        codex_result = asyncio.run(executor.execute(config.repository_root, prompt, config.codex, run_id))
    except Exception as exc:
        codex_result = CodexExecutionResult(False, error=f"Repair execution failed: {exc}")
    try:
        after = capture_execution_snapshot(config.repository_root)
        mutation = verify_mutation(baseline, before, after, scope)
    except MutationSafetyError as exc:
        record.final_status = "SAFETY_FAILED"; record.error = str(exc); record.finished_at = _now(); _write_record(config, record)
        return O4Result(record, None, initial_review)
    record.repair_count = 1
    record.cycles.append({"execution_index": 1, "execution_type": "REPAIR", "repair_attempt": 1, "repair_trigger": RepairTrigger.REVIEW_FINDINGS.value, "changed_paths": list(mutation.changed_paths), "mutation_safety": "PASS" if mutation.passed else "FAIL", "test_result": None, "review_result": "FIX", "cycle_status": "REPAIR_EXECUTED"})
    if not mutation.passed:
        record.final_status = "SAFETY_FAILED"; record.error = mutation.message; record.finished_at = _now(); _write_record(config, record)
        return O4Result(record, None, initial_review)
    if not codex_result.success:
        record.final_status = "REPAIR_EXECUTION_FAILED"; record.error = codex_result.error; record.finished_at = _now(); _write_record(config, record)
        return O4Result(record, None, initial_review)
    fixture_result = _fixture_test(fixture)
    if not fixture_result.passed:
        record.final_status = "TEST_FAILED"; record.last_failure = "TEST_FAILED"; record.error = fixture_result.execution_error; record.finished_at = _now(); _write_record(config, record)
        return O4Result(record, fixture_result, initial_review)
    try:
        fresh_observation = observe_fixture(fixture)
        diff, paths, status = collect_git_evidence(config.repository_root, config.review_max_diff_chars)
        fresh_input = sanitize_review_input(ReviewInput("The artifact must contain exactly status=ready. The deterministic fixture observation is authoritative evidence.", codex_result.response_text, diff, tuple(sorted(set(paths) | {fixture.relative_to(config.repository_root).as_posix()})), status, "PASS", fresh_observation.evidence, fixture_result.stderr, mutation.message, run_id), config.review_max_output_chars)
    except FixtureObservationError as exc:
        record.final_status = "FIXTURE_OBSERVATION_FAILED"; record.error = str(exc); record.finished_at = _now(); _write_record(config, record)
        return O4Result(record, fixture_result, initial_review)
    except EvidenceError as exc:
        record.final_status = "REVIEW_INPUT_TOO_LARGE" if "exceed" in str(exc).lower() else "GIT_EVIDENCE_FAILED"; record.error = str(exc); record.finished_at = _now(); _write_record(config, record)
        return O4Result(record, fixture_result, initial_review)
    try:
        final_review = reviewer.review(fresh_input, config.coordinator)
    except Exception as exc:
        final_review = ReviewResult(False, duration_seconds=0.0, error=f"Reviewer execution failed: {exc}")
    record.review_verdict = final_review.decision.verdict.value if final_review.decision else None
    record.review_summary = final_review.decision.summary if final_review.decision else None
    record.review_findings = [finding.model_dump(mode="json") for finding in final_review.decision.findings] if final_review.decision else None
    if final_review.success and final_review.decision and final_review.decision.verdict is ReviewVerdict.PASS:
        record.final_status = "SUCCESS"
    elif final_review.success and final_review.decision and final_review.decision.verdict is ReviewVerdict.FIX:
        record.final_status = "REVIEW_FIX_REQUIRED"
    else:
        record.final_status = "REVIEW_FAILED"
    record.finished_at = _now(); _write_record(config, record)
    return O4Result(record, fixture_result, final_review)


def _fixture_test(path: Path) -> TestRunResult:
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return TestRunResult(("fixture-validator",), None, False, "", "", 0.0, False, str(exc))
    passed = content == "status=ready\n"
    return TestRunResult(("fixture-validator",), 0 if passed else 1, passed, "fixture PASS" if passed else "fixture FAIL", "", 0.0, False, None if passed else "Fixture content is not exactly status=ready")


def _test_infrastructure_error(result: TestRunResult) -> str:
    if result.execution_error:
        return result.execution_error
    if result.timed_out:
        return "Test command timed out"
    return f"Test command failed with non-repairable exit code {result.exit_code!r}"


def _attach_review(record: RunRecord, result: ReviewResult) -> None:
    record.review_verdict = result.decision.verdict.value if result.decision else None


def _now():
    return datetime.now(timezone.utc)
