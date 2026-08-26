"""Human-gated general task intake and lifecycle for the O4 execution engine."""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from .codex_executor import CodexExecutionResult
from .config import OrchestratorConfig
from .evidence import EvidenceError, collect_git_evidence
from .finalization import FinalizationError, FinalizationPlan, build_finalization_plan, capture_git_state, get_origin_url, write_finalization_plan
from .mutation import capture_baseline
from .o4 import BoundedRepairController, O4Result
from .preflight import PreflightError, run_preflight
from .run_record import RunRecord
from .scope import TaskScope
from .smoke import ExecutorProtocol, _write_record, require_authentication
from .test_runner import FormulaTestRunner, TestRunResult


class O5Error(RuntimeError):
    """A deterministic O5 gate refused preparation or execution."""

    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class TaskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    schema_version: int = 1
    task_id: str
    title: str
    objective: str
    acceptance_criteria: list[str] = Field(min_length=1, max_length=20)
    allowed_paths: list[str] = []
    allowed_roots: list[str] = []
    repair_limit: int = 2
    commit_message: str | None = None

    @field_validator("schema_version")
    @classmethod
    def supported_schema(cls, value: int) -> int:
        if value != 1:
            raise ValueError("schema_version must be exactly 1")
        return value

    @field_validator("task_id")
    @classmethod
    def safe_task_id(cls, value: str) -> str:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", value):
            raise ValueError("task_id must be a non-empty safe slug-like identifier")
        return value

    @field_validator("title", "objective")
    @classmethod
    def bounded_text(cls, value: str) -> str:
        if not value.strip() or len(value) > 4_000:
            raise ValueError("text fields must be non-empty and at most 4000 characters")
        return value.strip()

    @field_validator("acceptance_criteria")
    @classmethod
    def valid_criteria(cls, value: list[str]) -> list[str]:
        if any(not item.strip() or len(item) > 2_000 for item in value):
            raise ValueError("acceptance criteria must be non-empty and at most 2000 characters")
        return [item.strip() for item in value]

    @field_validator("allowed_paths", "allowed_roots")
    @classmethod
    def valid_relative_paths(cls, value: list[str]) -> list[str]:
        return [_normalize_relative_path(item) for item in value]

    @field_validator("repair_limit")
    @classmethod
    def valid_repair_limit(cls, value: int) -> int:
        if value < 0 or value > 2:
            raise ValueError("repair_limit must be between 0 and 2")
        return value

    @field_validator("commit_message")
    @classmethod
    def valid_commit_message(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.split())
        if not normalized or len(normalized) > 72:
            raise ValueError("commit_message must be non-empty and at most 72 characters")
        return normalized

    @model_validator(mode="after")
    def nonempty_scope(self) -> "TaskRequest":
        if not self.allowed_paths and not self.allowed_roots:
            raise ValueError("at least one allowed_path or allowed_root is required")
        return self


class PreparedTaskPlan(BaseModel):
    """Immutable, approval-bound plan persisted as ignored local state."""

    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    schema_version: int = 1
    task_id: str
    title: str
    objective: str
    commit_message: str = ""
    acceptance_criteria: list[str]
    allowed_paths: list[str]
    allowed_roots: list[str]
    forbidden_paths: list[str]
    scope_risk: str
    baseline_head_sha: str
    baseline_branch: str
    baseline_test_status: str
    baseline_test_exit_code: int | None
    test_command: str
    test_timeout_seconds: float
    coordinator_model: str
    codex_model: str
    configured_max_repair_loops: int
    approved_repair_limit: int
    prepared_at: str
    repository_path: str
    plan_fingerprint: str
    approval_token: str


@dataclass(frozen=True)
class FinalEvidence:
    git_status: str
    changed_paths: tuple[str, ...]
    diff_char_count: int
    diff_sha256: str | None
    error: str | None = None


@dataclass
class O5RunRecord:
    run_id: str
    task_id: str
    plan_fingerprint: str
    approval_token_prefix: str
    approval_confirmed: bool
    plan_prepared_at: str
    plan_execution_at: str
    prepared_head: str
    prepared_branch: str
    scope: dict[str, Any]
    scope_risk: str
    approved_repair_budget: int
    baseline_prepare_test_status: str
    fresh_baseline_test_status: str | None = None
    fresh_baseline_exit_code: int | None = None
    o4_run_id: str | None = None
    o4_technical_status: str | None = None
    repair_count: int = 0
    final_evidence: dict[str, Any] | None = None
    human_review_required: bool = True
    final_status: str = "NOT_STARTED"
    error: str | None = None
    finalization_plan_path: str | None = None
    finalization_token: str | None = None
    finalization_status: str | None = None
    commit_sha: str | None = None
    push_remote: str | None = None
    push_branch: str | None = None
    push_success: bool | None = None
    finalized_at: str | None = None
    run_file_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PreparedTask:
    plan: PreparedTaskPlan
    plan_path: Path
    approval_token: str


@dataclass(frozen=True)
class O5Result:
    run_record: O5RunRecord
    o4_result: O4Result | None = None


def prepare_task(task_file: Path, config: OrchestratorConfig, test_runner: Any | None = None) -> PreparedTask:
    """Validate and prepare a plan without authentication or model calls."""
    request = _load_task_request(task_file)
    scope = _scope_from_request(request, config)
    run_preflight(config)
    baseline = capture_baseline(config.repository_root)
    result = _run_tests(config, test_runner)
    if not result.passed:
        status = "BASELINE_UNHEALTHY" if _ordinary_test_failure(result) else "BASELINE_INFRA_FAILED"
        raise O5Error(status, _test_failure_message(result, status))
    plan = _build_plan(request, scope, config, baseline, result)
    plan_path = config.run_log_directory / "prepared" / f"{request.task_id}-{plan.plan_fingerprint[:16]}.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return PreparedTask(plan, plan_path, plan.approval_token)


def run_task(
    plan_file: Path,
    approval_token: str,
    config: OrchestratorConfig,
    executor: ExecutorProtocol | None = None,
    reviewer: Any | None = None,
    test_runner: Any | None = None,
    controller_factory: Callable[[OrchestratorConfig], BoundedRepairController] = BoundedRepairController,
) -> O5Result:
    """Run one exact approved plan, delegating execution to O4."""
    plan = _load_and_verify_plan(plan_file, approval_token)
    _verify_current_policy(plan, config)
    try:
        run_preflight(config)
    except PreflightError as exc:
        raise O5Error("PLAN_STALE", f"Current Formula workspace is not the approved clean workspace: {exc}") from exc
    current = capture_baseline(config.repository_root)
    if current.head_sha != plan.baseline_head_sha or current.branch != plan.baseline_branch:
        raise O5Error("PLAN_STALE", "Repository HEAD or branch differs from the prepared plan")
    fresh = _run_tests(config, test_runner)
    if not fresh.passed:
        status = "BASELINE_UNHEALTHY" if _ordinary_test_failure(fresh) else "BASELINE_INFRA_FAILED"
        raise O5Error(status, _test_failure_message(fresh, status))
    require_authentication()

    run_id = uuid.uuid4().hex
    record = O5RunRecord(
        run_id=run_id,
        task_id=plan.task_id,
        plan_fingerprint=plan.plan_fingerprint,
        approval_token_prefix=plan.approval_token,
        approval_confirmed=True,
        plan_prepared_at=plan.prepared_at,
        plan_execution_at=_now().isoformat(),
        prepared_head=plan.baseline_head_sha,
        prepared_branch=plan.baseline_branch,
        scope={"allowed_paths": list(plan.allowed_paths), "allowed_roots": list(plan.allowed_roots), "forbidden_paths": list(plan.forbidden_paths)},
        scope_risk=plan.scope_risk,
        approved_repair_budget=plan.approved_repair_limit,
        baseline_prepare_test_status=plan.baseline_test_status,
        fresh_baseline_test_status=fresh.gate_status.value,
        fresh_baseline_exit_code=fresh.exit_code,
        run_file_path=str(config.run_log_directory / f"o5-{run_id}.json"),
    )
    lock = _ExecutionLock(config.run_log_directory / "active-task.lock", plan)
    lock.acquire()
    try:
        _consume_plan(plan, config)
        execution_config = replace(config, max_repair_loops=plan.approved_repair_limit)
        scope = TaskScope(config.repository_root, plan.allowed_paths, plan.allowed_roots, plan.forbidden_paths)
        technical_task = canonical_task_text(plan)
        try:
            o4_result = controller_factory(execution_config).run(
                technical_task,
                scope,
                fresh,
                executor=executor,
                test_runner=test_runner,
                reviewer=reviewer,
            )
        except Exception as exc:
            record.o4_technical_status = "O4_EXECUTION_ERROR"
            record.final_status = "TECHNICAL_FAILED: O4_EXECUTION_ERROR"
            record.error = f"O4 execution failed: {exc}"
            _write_o5_record(config, record)
            return O5Result(record)
        record.o4_run_id = o4_result.run_record.run_id
        record.o4_technical_status = o4_result.run_record.final_status
        record.repair_count = o4_result.run_record.repair_count
        evidence = _final_evidence(config)
        record.final_evidence = asdict(evidence)
        final_review = o4_result.last_review_result
        final_test = o4_result.last_test_result
        explicit_success_evidence = (
            o4_result.run_record.final_status == "SUCCESS"
            and final_test is not None
            and final_test.passed
            and final_test.gate_status.value == "PASS"
            and final_review is not None
            and final_review.success
            and final_review.decision is not None
            and final_review.decision.verdict.value == "PASS"
        )
        if o4_result.run_record.final_status == "SUCCESS" and not explicit_success_evidence:
            record.final_status = "TECHNICAL_FAILED: INCOMPLETE_SUCCESS_EVIDENCE"
            record.error = "O4 reported SUCCESS without explicit final PASS test and reviewer evidence"
        elif o4_result.run_record.final_status == "SUCCESS" and evidence.error:
            record.final_status = "TECHNICAL_FAILED: FINAL_EVIDENCE_FAILED"
            record.error = evidence.error
        elif o4_result.run_record.final_status == "SUCCESS":
            try:
                final_state = capture_git_state(config.repository_root, config.review_max_diff_chars)
                push_remote_url = get_origin_url(config.repository_root)
                finalization_plan = build_finalization_plan(
                    task_id=plan.task_id,
                    o5_run_id=record.run_id,
                    o4_run_id=o4_result.run_record.run_id,
                    prepared_plan_fingerprint=plan.plan_fingerprint,
                    baseline_head=plan.baseline_head_sha,
                    branch=plan.baseline_branch,
                    repository_path=plan.repository_path,
                    scope=scope,
                    state=final_state,
                    repair_count=o4_result.run_record.repair_count,
                    final_test_result=final_test.gate_status.value if final_test else "UNKNOWN",
                    final_gpt_verdict=final_review.decision.verdict.value if final_review and final_review.decision else "UNKNOWN",
                    commit_message=plan.commit_message,
                    prepared_timestamp=plan.prepared_at,
                    push_remote_url=push_remote_url,
                )
                finalization_path = write_finalization_plan(config, finalization_plan)
                record.finalization_plan_path = str(finalization_path)
                record.finalization_token = finalization_plan.finalization_token
                record.final_status = "READY_FOR_HUMAN_REVIEW"
            except FinalizationError as exc:
                record.final_status = "TECHNICAL_FAILED: FINALIZATION_PLAN_FAILED"
                record.error = str(exc)
        else:
            record.final_status = f"TECHNICAL_FAILED: {o4_result.run_record.final_status}"
            record.error = o4_result.run_record.error or evidence.error
        _write_o5_record(config, record)
        return O5Result(record, o4_result)
    finally:
        lock.release()


def canonical_task_text(plan: PreparedTaskPlan) -> str:
    criteria = "\n".join(f"{index}. {item}" for index, item in enumerate(plan.acceptance_criteria, 1))
    return f"Task ID: {plan.task_id}\n\nTitle:\n{plan.title}\n\nObjective:\n{plan.objective}\n\nAcceptance criteria:\n{criteria}"


def scope_risk(allowed_paths: tuple[str, ...], allowed_roots: tuple[str, ...]) -> str:
    broad_names = {"src", "tests", "app.py", "tools", ""}
    if allowed_roots or any(path in broad_names for path in allowed_paths) or len(allowed_paths) > 5:
        return "WIDE"
    return "NARROW"


def _load_task_request(path: Path) -> TaskRequest:
    try:
        return TaskRequest.model_validate_json(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise O5Error("TASK_INVALID", f"Could not read task request: {exc}") from exc
    except ValidationError as exc:
        raise O5Error("TASK_INVALID", f"Task request validation failed: {exc}") from exc


def _scope_from_request(request: TaskRequest, config: OrchestratorConfig) -> TaskScope:
    if request.repair_limit > config.max_repair_loops:
        raise O5Error("TASK_INVALID", "repair_limit cannot exceed the configured repair policy")
    for item in (*request.allowed_paths, *request.allowed_roots):
        resolved = (config.repository_root / item).resolve()
        try:
            resolved.relative_to(config.repository_root)
        except ValueError as exc:
            raise O5Error("SCOPE_INVALID", f"Scope resolves outside Formula: {item}") from exc
        if item in ("", ".", "/"):
            raise O5Error("SCOPE_INVALID", "Repository-root scope is not allowed")
        for forbidden in TaskScope(config.repository_root).forbidden_paths:
            if _scope_intersects_forbidden(item, forbidden):
                raise O5Error("SCOPE_INVALID", f"Scope intersects protected path: {forbidden}")
    return TaskScope(config.repository_root, request.allowed_paths, request.allowed_roots)


def _build_plan(request: TaskRequest, scope: TaskScope, config: OrchestratorConfig, baseline: Any, result: TestRunResult) -> PreparedTaskPlan:
    values: dict[str, Any] = {
        "schema_version": 1,
        "task_id": request.task_id,
        "title": request.title,
        "objective": request.objective,
        "commit_message": request.commit_message or " ".join(request.title.split()),
        "acceptance_criteria": list(request.acceptance_criteria),
        "allowed_paths": list(scope.allowed_paths),
        "allowed_roots": list(scope.allowed_roots),
        "forbidden_paths": list(scope.forbidden_paths),
        "scope_risk": scope_risk(scope.allowed_paths, scope.allowed_roots),
        "baseline_head_sha": baseline.head_sha,
        "baseline_branch": baseline.branch,
        "baseline_test_status": result.gate_status.value,
        "baseline_test_exit_code": result.exit_code,
        "test_command": config.test_command,
        "test_timeout_seconds": config.test_timeout_seconds,
        "coordinator_model": config.coordinator.model,
        "codex_model": config.codex.model,
        "configured_max_repair_loops": config.max_repair_loops,
        "approved_repair_limit": request.repair_limit,
        "prepared_at": _now().isoformat(),
        "repository_path": str(config.repository_root),
    }
    normalized = PreparedTaskPlan.model_validate({**values, "plan_fingerprint": "", "approval_token": ""}).model_dump(mode="json")
    normalized.pop("plan_fingerprint")
    normalized.pop("approval_token")
    fingerprint = _fingerprint(normalized)
    values["plan_fingerprint"] = fingerprint
    values["approval_token"] = fingerprint[:16]
    return PreparedTaskPlan.model_validate(values)


def _load_and_verify_plan(path: Path, approval_token: str) -> PreparedTaskPlan:
    try:
        plan = PreparedTaskPlan.model_validate_json(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise O5Error("APPROVAL_MISMATCH", f"Could not load prepared plan: {exc}") from exc
    except ValidationError as exc:
        raise O5Error("APPROVAL_MISMATCH", f"Prepared plan validation failed: {exc}") from exc
    values = plan.model_dump(mode="json")
    stored_fingerprint = values.pop("plan_fingerprint")
    stored_token = values.pop("approval_token")
    actual = _fingerprint(values)
    if stored_fingerprint != actual or stored_token != actual[:16] or approval_token != actual[:16]:
        raise O5Error("APPROVAL_MISMATCH", "Approval token or prepared-plan fingerprint does not match")
    return plan


def _verify_current_policy(plan: PreparedTaskPlan, config: OrchestratorConfig) -> None:
    if str(config.repository_root) != plan.repository_path:
        raise O5Error("PLAN_STALE", "Configured Formula repository differs from the prepared plan")
    if config.test_command != plan.test_command or config.test_timeout_seconds != plan.test_timeout_seconds:
        raise O5Error("PLAN_STALE", "Deterministic test policy differs from the prepared plan")
    if config.coordinator.model != plan.coordinator_model or config.codex.model != plan.codex_model:
        raise O5Error("PLAN_STALE", "Model configuration differs from the prepared plan")
    if config.max_repair_loops != plan.configured_max_repair_loops:
        raise O5Error("PLAN_STALE", "Repair policy differs from the prepared plan")


def _run_tests(config: OrchestratorConfig, test_runner: Any | None) -> TestRunResult:
    runner = test_runner or FormulaTestRunner()
    try:
        return runner.run(config.repository_root, config.test_command, config.test_timeout_seconds)
    except Exception as exc:
        return TestRunResult((config.test_command,), None, False, "", "", 0.0, False, f"Test runner failed: {exc}")


def _ordinary_test_failure(result: TestRunResult) -> bool:
    return not result.timed_out and result.execution_error is None and result.exit_code == 1


def _test_failure_message(result: TestRunResult, status: str) -> str:
    if result.execution_error:
        return result.execution_error
    return f"{status}: test command exit code {result.exit_code!r}"


def _fingerprint(values: dict[str, Any]) -> str:
    canonical = json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _normalize_relative_path(value: str) -> str:
    if not value.strip():
        raise ValueError("scope paths must be non-empty")
    path = Path(value)
    if path.is_absolute() or re.match(r"^[A-Za-z]:", value) or value.startswith(("/", "\\")):
        raise ValueError("scope paths must be repository-relative")
    normalized = path.as_posix().strip("/")
    if normalized in ("", ".") or ".." in Path(normalized).parts:
        raise ValueError("scope paths must not contain '..' or denote the repository root")
    return normalized


def _scope_intersects_forbidden(item: str, forbidden: str) -> bool:
    if forbidden.endswith(".*"):
        prefix = forbidden[:-2]
        return item == prefix or item.startswith(prefix + ".") or prefix.startswith(item + "/")
    return item == forbidden or item.startswith(forbidden + "/") or forbidden.startswith(item + "/")


class _ExecutionLock:
    def __init__(self, path: Path, plan: PreparedTaskPlan) -> None:
        self.path = path
        self.plan = plan
        self.held = False

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = f"task_id={self.plan.task_id}\nplan_fingerprint={self.plan.plan_fingerprint}\ntimestamp={_now().isoformat()}\npid={os.getpid()}\n"
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise O5Error("ANOTHER_TASK_ACTIVE", f"Active task lock exists; inspect {self.path} before removing it") from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
        self.held = True

    def release(self) -> None:
        if self.held:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            self.held = False


def _consume_plan(plan: PreparedTaskPlan, config: OrchestratorConfig) -> Path:
    marker = config.run_log_directory / "executed" / f"{plan.plan_fingerprint}.json"
    marker.parent.mkdir(parents=True, exist_ok=True)
    try:
        with marker.open("x", encoding="utf-8") as handle:
            json.dump({"task_id": plan.task_id, "plan_fingerprint": plan.plan_fingerprint, "consumed_at": _now().isoformat()}, handle, sort_keys=True)
            handle.write("\n")
    except FileExistsError as exc:
        raise O5Error("PLAN_ALREADY_EXECUTED", "This approved plan has already reached its execution point") from exc
    return marker


def _final_evidence(config: OrchestratorConfig) -> FinalEvidence:
    try:
        state = capture_git_state(config.repository_root, config.review_max_diff_chars)
    except (EvidenceError, FinalizationError) as exc:
        return FinalEvidence("", (), 0, None, str(exc))
    return FinalEvidence(state.status, state.changed_paths, state.diff_char_count, state.diff_sha256)


def _write_o5_record(config: OrchestratorConfig, record: O5RunRecord) -> None:
    path = config.run_log_directory / f"o5-{record.run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _now() -> datetime:
    return datetime.now(timezone.utc)
