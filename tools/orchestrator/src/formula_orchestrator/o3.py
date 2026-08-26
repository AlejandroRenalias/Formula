"""O3 composition: Codex smoke, test gate, then one independent GPT review."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from .config import OrchestratorConfig
from .evidence import EvidenceError, ReviewInput, collect_git_evidence, sanitize_review_input
from .preflight import run_preflight
from .reviewer import GptReviewer, ReviewDecision, ReviewResult, ReviewVerdict
from .run_record import RunRecord
from .smoke import ExecutorProtocol, require_authentication, run_preflighted_smoke, _write_record
from .test_runner import FormulaTestRunner, TestRunResult


class ReviewerProtocol(Protocol):
    def review(self, review_input: ReviewInput, model) -> ReviewResult: ...


@dataclass(frozen=True)
class O3Result:
    run_record: RunRecord
    review_result: ReviewResult | None


def run_codex_test_review_smoke(
    config: OrchestratorConfig,
    executor: ExecutorProtocol | None = None,
    test_runner: FormulaTestRunner | None = None,
    reviewer: ReviewerProtocol | None = None,
) -> O3Result:
    run_preflight(config)
    require_authentication()
    smoke = run_preflighted_smoke(config, executor)
    record = smoke.run_record
    if not smoke.codex_result or not smoke.codex_result.success:
        record.final_status = "CODEX_FAILED"
        _write_record(config, record)
        return O3Result(record, None)
    if not smoke.safety or not smoke.safety.passed:
        record.final_status = "SAFETY_FAILED"
        _write_record(config, record)
        return O3Result(record, None)

    test_result = (test_runner or FormulaTestRunner()).run(config.repository_root, config.test_command, config.test_timeout_seconds)
    _attach_test_result(record, test_result)
    if not test_result.passed:
        record.final_status = "TEST_FAILED"
        record.error = test_result.execution_error or "Formula test gate failed"
        _write_record(config, record)
        return O3Result(record, None)

    try:
        git_diff, changed_paths, git_status = collect_git_evidence(config.repository_root, config.review_max_diff_chars)
        review_input = sanitize_review_input(
            ReviewInput(
                task_spec="Verify the Codex smoke task created exactly one permitted harmless marker, made no tracked or unexpected changes, and that the Formula deterministic test gate passed.",
                codex_summary=smoke.codex_result.response_text,
                git_diff=git_diff,
                changed_paths=changed_paths,
                git_status=git_status,
                test_result=test_result.gate_status.value,
                test_stdout=test_result.stdout,
                test_stderr=test_result.stderr,
                safety_verification=smoke.safety.message,
                run_id=record.run_id,
            ),
            config.review_max_output_chars,
        )
    except EvidenceError as exc:
        record.final_status = "REVIEW_INPUT_TOO_LARGE"
        record.review_error = str(exc)
        record.error = str(exc)
        _write_record(config, record)
        return O3Result(record, None)

    review_result = (reviewer or GptReviewer()).review(review_input, config.coordinator)
    _attach_review_result(record, review_result, config.coordinator.model)
    if not review_result.success or review_result.decision is None:
        record.final_status = "REVIEW_FAILED"
    elif review_result.decision.verdict is ReviewVerdict.PASS:
        record.final_status = "SUCCESS"
    else:
        record.final_status = "REVIEW_FIX_REQUIRED"
    _write_record(config, record)
    return O3Result(record, review_result)


def run_review_smoke(config: OrchestratorConfig, reviewer: ReviewerProtocol | None = None) -> O3Result:
    """Run one structured review against a tiny local fixture; no Codex or workspace edits."""
    require_authentication()
    run_id = uuid.uuid4().hex
    record = RunRecord(
        run_id=run_id,
        task_id=run_id,
        task_type="review-smoke",
        stage="gpt-review",
        started_at=datetime.now(timezone.utc),
    )
    fixture = ReviewInput(
        task_spec="Add a harmless greeting constant to the small demo module.",
        codex_summary="Added the requested greeting constant.",
        git_diff="+GREETING = 'hello'",
        changed_paths=("demo.py",),
        git_status=" M demo.py",
        test_result="PASS",
        test_stdout="1 passed",
        test_stderr="",
        safety_verification="PASS; only demo.py changed as requested",
        run_id=run_id,
    )
    result = (reviewer or GptReviewer()).review(sanitize_review_input(fixture, config.review_max_output_chars), config.coordinator)
    _attach_review_result(record, result, config.coordinator.model)
    if not result.success or result.decision is None:
        record.final_status = "REVIEW_FAILED"
    elif result.decision.verdict is ReviewVerdict.PASS:
        record.final_status = "SUCCESS"
    else:
        record.final_status = "REVIEW_FIX_REQUIRED"
    record.finished_at = datetime.now(timezone.utc)
    _write_record(config, record)
    return O3Result(record, result)


def _attach_test_result(record: RunRecord, result: TestRunResult) -> None:
    record.test_gate_status = result.gate_status.value
    record.test_exit_code = result.exit_code
    record.test_duration_seconds = result.duration_seconds
    record.test_timed_out = result.timed_out
    record.test_output = {"stdout": result.stdout, "stderr": result.stderr}


def _attach_review_result(record: RunRecord, result: ReviewResult, model: str) -> None:
    record.reviewer_model = model
    record.review_duration_seconds = result.duration_seconds
    record.review_usage = result.usage
    if result.decision is not None:
        record.review_verdict = result.decision.verdict.value
        record.review_summary = result.decision.summary
        record.review_findings = [finding.model_dump(mode="json") for finding in result.decision.findings]
    else:
        record.review_error = result.error or "Reviewer returned no valid decision"
        record.error = record.review_error
