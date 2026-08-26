"""Human-approved, deterministic Git finalization for successful O5 runs."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from .config import OrchestratorConfig
from .scope import TaskScope


class FinalizationError(RuntimeError):
    def __init__(self, status: str, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class FinalizationPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, frozen=True)

    schema_version: int = 1
    task_id: str
    o5_run_id: str
    o4_run_id: str
    prepared_plan_fingerprint: str
    baseline_head: str
    branch: str
    repository_path: str
    allowed_paths: list[str]
    allowed_roots: list[str]
    forbidden_paths: list[str]
    final_changed_paths: list[str]
    final_git_status: str
    final_diff_sha256: str
    final_diff_char_count: int
    repair_count: int
    final_test_result: str
    final_gpt_verdict: str
    commit_message: str
    push_remote: str
    push_remote_url: str
    push_branch: str
    prepared_timestamp: str
    finalization_fingerprint: str
    finalization_token: str

    @field_validator("final_test_result", "final_gpt_verdict")
    @classmethod
    def require_pass(cls, value: str) -> str:
        if value != "PASS":
            raise ValueError("finalization plans require explicit PASS test and GPT evidence")
        return value

    @field_validator("push_remote")
    @classmethod
    def require_origin(cls, value: str) -> str:
        if value != "origin":
            raise ValueError("push_remote must be origin")
        return value


@dataclass(frozen=True)
class GitState:
    status: str
    changed_paths: tuple[str, ...]
    staged_paths: tuple[str, ...]
    diff_char_count: int
    diff_sha256: str


@dataclass(frozen=True)
class FinalizationOutcome:
    status: str
    message: str
    commit_sha: str | None = None
    push_success: bool = False


def build_finalization_plan(
    *,
    task_id: str,
    o5_run_id: str,
    o4_run_id: str,
    prepared_plan_fingerprint: str,
    baseline_head: str,
    branch: str,
    repository_path: str,
    scope: TaskScope,
    state: GitState,
    repair_count: int,
    final_test_result: str,
    final_gpt_verdict: str,
    commit_message: str,
    prepared_timestamp: str,
    push_remote_url: str,
) -> FinalizationPlan:
    values: dict[str, Any] = {
        "schema_version": 1,
        "task_id": task_id,
        "o5_run_id": o5_run_id,
        "o4_run_id": o4_run_id,
        "prepared_plan_fingerprint": prepared_plan_fingerprint,
        "baseline_head": baseline_head,
        "branch": branch,
        "repository_path": repository_path,
        "allowed_paths": list(scope.allowed_paths),
        "allowed_roots": list(scope.allowed_roots),
        "forbidden_paths": list(scope.forbidden_paths),
        "final_changed_paths": list(state.changed_paths),
        "final_git_status": state.status,
        "final_diff_sha256": state.diff_sha256,
        "final_diff_char_count": state.diff_char_count,
        "repair_count": repair_count,
        "final_test_result": final_test_result,
        "final_gpt_verdict": final_gpt_verdict,
        "commit_message": commit_message,
        "push_remote": "origin",
        "push_remote_url": push_remote_url,
        "push_branch": branch,
        "prepared_timestamp": prepared_timestamp,
    }
    fingerprint = _fingerprint(values)
    values["finalization_fingerprint"] = fingerprint
    values["finalization_token"] = fingerprint[:16]
    return FinalizationPlan.model_validate(values)


def write_finalization_plan(config: OrchestratorConfig, plan: FinalizationPlan) -> Path:
    path = config.run_log_directory / "finalization" / f"{plan.o5_run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def finalize_task(run_file: Path, approval_token: str, config: OrchestratorConfig) -> FinalizationOutcome:
    run_path = Path(run_file)
    try:
        run_data = json.loads(run_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FinalizationError("RUN_INVALID", f"Could not load O5 run record: {exc}") from exc
    plan_path_value = run_data.get("finalization_plan_path")
    if not plan_path_value:
        raise FinalizationError("RUN_NOT_FINALIZABLE", "The O5 run has no finalization plan")
    plan_path = Path(plan_path_value).resolve()
    plan = _load_plan(plan_path, approval_token)
    expected_plan_path = (config.run_log_directory / "finalization" / f"{plan.o5_run_id}.json").resolve()
    if (
        run_data.get("run_id") != plan.o5_run_id
        or run_data.get("task_id") != plan.task_id
        or run_data.get("plan_fingerprint") != plan.prepared_plan_fingerprint
        or run_data.get("o4_run_id") != plan.o4_run_id
        or run_data.get("finalization_token") != plan.finalization_token
        or plan_path != expected_plan_path
    ):
        raise FinalizationError("RUN_INVALID", "O5 run record and finalization plan identities do not agree")
    if Path(plan.repository_path).resolve() != config.repository_root:
        raise FinalizationError("FINALIZATION_STALE", "Finalization plan repository differs from configured Formula repository")
    marker = config.run_log_directory / "finalized" / f"{plan.finalization_fingerprint}.json"
    if marker.exists():
        raise FinalizationError("ALREADY_FINALIZED", "This finalization approval has already reached the commit point")
    if run_data.get("final_status") != "READY_FOR_HUMAN_REVIEW":
        raise FinalizationError("RUN_NOT_FINALIZABLE", f"Only READY_FOR_HUMAN_REVIEW runs can be finalized; got {run_data.get('final_status')!r}")
    lock = _FinalizationLock(config.run_log_directory / "active-task.lock", plan)
    lock.acquire()
    staged = False
    try:
        state = capture_git_state(config.repository_root, config.review_max_diff_chars)
        _validate_pre_stage_state(plan, state)
        if get_origin_url(config.repository_root) != plan.push_remote_url:
            raise FinalizationError("FINALIZATION_STALE", "origin URL differs from the approved finalization plan")
        scope = TaskScope(config.repository_root, tuple(plan.allowed_paths), tuple(plan.allowed_roots), tuple(plan.forbidden_paths))
        violations = scope.violations(tuple(plan.final_changed_paths))
        if violations:
            raise FinalizationError("FINALIZATION_SCOPE_FAILED", f"Approved result contains protected or out-of-scope paths: {', '.join(violations)}")
        if not plan.final_changed_paths:
            raise FinalizationError("FINALIZATION_STALE", "There are no changed paths to finalize")
        staged = True
        _git(config.repository_root, ["add", "--", *plan.final_changed_paths])
        check = _git_result(config.repository_root, ["diff", "--cached", "--check"])
        if check.returncode != 0:
            raise FinalizationError("STAGED_CHECK_FAILED", check.stderr.strip() or "git diff --cached --check failed")
        staged_state = capture_staged_state(config.repository_root, config.review_max_diff_chars)
        if staged_state.changed_paths != tuple(sorted(plan.final_changed_paths)) or staged_state.diff_sha256 != plan.final_diff_sha256:
            raise FinalizationError("FINALIZATION_STALE", f"Staged content differs from the approved final result (expected={plan.final_diff_sha256}, actual={staged_state.diff_sha256})")
        _consume_finalization(marker, plan)
        commit_result = _git_result(config.repository_root, ["commit", "-m", plan.commit_message])
        if commit_result.returncode != 0:
            _update_run_record(run_path, {"finalization_status": "COMMIT_FAILED", "final_status": "COMMIT_FAILED", "error": commit_result.stderr.strip() or "git commit failed"})
            raise FinalizationError("COMMIT_FAILED", commit_result.stderr.strip() or "git commit failed")
        commit_sha = _git(config.repository_root, ["rev-parse", "HEAD"])
        try:
            verify_committed_result(config.repository_root, plan, commit_sha)
        except FinalizationError as exc:
            _update_run_record(run_path, {"finalization_status": "COMMIT_VERIFICATION_FAILED", "final_status": "COMMIT_VERIFICATION_FAILED", "commit_sha": commit_sha, "error": str(exc)})
            raise
        branch = _git(config.repository_root, ["symbolic-ref", "--short", "-q", "HEAD"])
        if branch != plan.push_branch or _git_result(config.repository_root, ["remote", "get-url", plan.push_remote]).returncode != 0 or _git(config.repository_root, ["rev-parse", "HEAD"]) != commit_sha:
            _update_run_record(run_path, {"finalization_status": "PUSH_FAILED", "final_status": "PUSH_FAILED", "commit_sha": commit_sha, "push_remote": plan.push_remote, "push_branch": plan.push_branch, "push_success": False, "error": "Push precondition failed; local commit was preserved"})
            raise FinalizationError("PUSH_FAILED", f"Commit {commit_sha} exists locally but push precondition failed")
        if get_origin_url(config.repository_root) != plan.push_remote_url:
            _update_run_record(run_path, {"finalization_status": "PUSH_FAILED", "final_status": "PUSH_FAILED", "commit_sha": commit_sha, "push_remote": plan.push_remote, "push_branch": plan.push_branch, "push_success": False, "error": "origin URL changed before push; local commit was preserved"})
            raise FinalizationError("PUSH_FAILED", "origin URL changed before push; local commit was preserved")
        push_result = _git_result(config.repository_root, ["push", plan.push_remote, plan.push_branch])
        if push_result.returncode != 0:
            _update_run_record(run_path, {"finalization_status": "PUSH_FAILED", "final_status": "PUSH_FAILED", "commit_sha": commit_sha, "push_remote": plan.push_remote, "push_branch": plan.push_branch, "push_success": False, "error": push_result.stderr.strip() or "git push failed"})
            raise FinalizationError("PUSH_FAILED", f"Commit {commit_sha} exists locally but push failed: {push_result.stderr.strip()}")
        remote_ref = _git_result(config.repository_root, ["ls-remote", plan.push_remote, f"refs/heads/{plan.push_branch}"])
        if remote_ref.returncode != 0 or not any(line.split()[0] == commit_sha and len(line.split()) > 1 and line.split()[1] == f"refs/heads/{plan.push_branch}" for line in remote_ref.stdout.splitlines() if line.split()):
            _update_run_record(run_path, {"finalization_status": "PUSH_VERIFICATION_FAILED", "final_status": "PUSH_VERIFICATION_FAILED", "commit_sha": commit_sha, "push_remote": plan.push_remote, "push_branch": plan.push_branch, "push_success": False, "error": "Remote branch could not be verified at the created commit"})
            raise FinalizationError("PUSH_VERIFICATION_FAILED", f"Remote {plan.push_remote}/{plan.push_branch} did not resolve to {commit_sha}")
        finalized_at = _now().isoformat()
        _update_run_record(run_path, {"finalization_status": "FINALIZED", "final_status": "FINALIZED", "commit_sha": commit_sha, "push_remote": plan.push_remote, "push_branch": plan.push_branch, "push_success": True, "finalized_at": finalized_at, "error": None})
        return FinalizationOutcome("FINALIZED", f"Commit {commit_sha} pushed to {plan.push_remote}/{plan.push_branch}", commit_sha, True)
    finally:
        if staged:
            _unstage_safely(config.repository_root, plan.final_changed_paths)
        lock.release()


def capture_git_state(root: Path, max_diff_chars: int) -> GitState:
    status = _git(root, ["status", "--porcelain", "--untracked-files=all"])
    diff = _git(root, ["diff", "HEAD", "--no-ext-diff", "--binary"])
    if len(diff) > max_diff_chars:
        raise FinalizationError("FINALIZATION_STALE", "Final diff exceeds configured review limit")
    return GitState(status, _status_paths(status), _staged_paths(status), len(diff), _content_digest(root, _status_paths(status)))


def get_origin_url(root: Path) -> str:
    result = _git_result(root, ["remote", "get-url", "origin"])
    if result.returncode != 0 or not result.stdout.strip():
        raise FinalizationError("FINALIZATION_STALE", "Git remote origin is not configured")
    return result.stdout.strip()


def capture_staged_state(root: Path, max_diff_chars: int) -> GitState:
    diff = _git(root, ["diff", "--cached", "--no-ext-diff", "--binary"])
    if len(diff) > max_diff_chars:
        raise FinalizationError("FINALIZATION_STALE", "Staged diff exceeds configured review limit")
    names = _git(root, ["diff", "--cached", "--name-only", "--diff-filter=ACDMRTUXB"])
    paths = tuple(sorted(path for path in names.splitlines() if path))
    return GitState("", paths, paths, len(diff), _content_digest(root, paths, staged=True))


def _validate_pre_stage_state(plan: FinalizationPlan, state: GitState) -> None:
    if state.staged_paths:
        raise FinalizationError("FINALIZATION_STALE", "Git index is not empty; refusing to stage anything")
    if state.changed_paths != tuple(sorted(plan.final_changed_paths)):
        raise FinalizationError("FINALIZATION_STALE", "Current changed paths differ from the approved final result")
    if state.status != plan.final_git_status:
        raise FinalizationError("FINALIZATION_STALE", "Current Git status differs from the approved final result")
    if state.diff_sha256 != plan.final_diff_sha256:
        raise FinalizationError("FINALIZATION_STALE", "Current working-tree result differs from the approved final result")
    current_head = _git(Path(plan.repository_path), ["rev-parse", "HEAD"])
    current_branch = _git(Path(plan.repository_path), ["symbolic-ref", "--short", "-q", "HEAD"]) or "DETACHED"
    if current_head != plan.baseline_head or current_branch != plan.branch:
        raise FinalizationError("FINALIZATION_STALE", "Current HEAD or branch differs from the approved finalization plan")


def verify_committed_result(root: Path, plan: FinalizationPlan, commit_sha: str) -> None:
    parents = _git(root, ["rev-list", "--parents", "-n", "1", commit_sha]).split()
    branch = _git(root, ["symbolic-ref", "--short", "-q", "HEAD"])
    if len(parents) != 2 or parents[1] != plan.baseline_head or _git(root, ["rev-parse", "HEAD"]) != commit_sha or branch != plan.push_branch:
        raise FinalizationError("COMMIT_VERIFICATION_FAILED", "Commit parent, HEAD, or branch does not match the approved result")
    paths = tuple(sorted(path for path in _git(root, ["diff-tree", "--no-commit-id", "--name-only", "-r", commit_sha]).splitlines() if path))
    if paths != tuple(sorted(plan.final_changed_paths)):
        raise FinalizationError("COMMIT_VERIFICATION_FAILED", "Committed paths differ from the approved result")
    if _content_digest(root, paths, commit=commit_sha) != plan.final_diff_sha256:
        raise FinalizationError("COMMIT_VERIFICATION_FAILED", "Committed content differs from the approved result")
    if _git(root, ["log", "-1", "--format=%s", commit_sha]) != plan.commit_message:
        raise FinalizationError("COMMIT_VERIFICATION_FAILED", "Committed message differs from the approved result")
    if _git(root, ["status", "--porcelain", "--untracked-files=all"]) or _staged_paths(_git(root, ["status", "--porcelain", "--untracked-files=all"])):
        raise FinalizationError("COMMIT_VERIFICATION_FAILED", "Committed result left a dirty working tree or index")


def _load_plan(path: Path, approval_token: str) -> FinalizationPlan:
    try:
        plan = FinalizationPlan.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValidationError) as exc:
        raise FinalizationError("APPROVAL_MISMATCH", f"Finalization plan validation failed: {exc}") from exc
    values = plan.model_dump(mode="json")
    fingerprint = values.pop("finalization_fingerprint")
    stored_token = values.pop("finalization_token")
    actual = _fingerprint(values)
    if fingerprint != actual or stored_token != actual[:16] or approval_token != actual[:16]:
        raise FinalizationError("APPROVAL_MISMATCH", "Finalization token or plan fingerprint does not match")
    return plan


def _fingerprint(values: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _content_digest(root: Path, paths: tuple[str, ...], staged: bool = False, commit: str | None = None) -> str:
    digest = hashlib.sha256()
    for relative in sorted(paths):
        path = root / relative
        digest.update(relative.encode("utf-8")); digest.update(b"\0")
        if staged or commit:
            object_spec = f":{relative}" if staged else f"{commit}:{relative}"
            result = _git_result(root, ["show", object_spec])
            if result.returncode == 0:
                data = _normalized_file_bytes(result.stdout_bytes)
                digest.update(b"present\0"); digest.update(hashlib.sha256(data).digest())
            else:
                digest.update(b"missing\0")
        elif path.is_file():
            digest.update(b"present\0"); digest.update(hashlib.sha256(_normalized_file_bytes(path.read_bytes())).digest())
        else:
            digest.update(b"missing\0")
    return digest.hexdigest()


def _normalized_file_bytes(value: bytes) -> bytes:
    """Match Git's normal text-line ending behavior on Windows for state comparison."""
    return value.replace(b"\r\n", b"\n")


def _status_paths(status: str) -> tuple[str, ...]:
    result = []
    for line in status.splitlines():
        if line.strip():
            path = line[3:] if len(line) >= 4 else line
            result.append(path.rsplit(" -> ", 1)[-1])
    return tuple(sorted(result))


def _staged_paths(status: str) -> tuple[str, ...]:
    return tuple(sorted(path for line, path in ((line, (line[3:] if len(line) >= 4 else line).rsplit(" -> ", 1)[-1]) for line in status.splitlines() if line.strip()) if line[0] not in (" ", "?")))


@dataclass(frozen=True)
class _GitResult:
    returncode: int
    stdout: str
    stderr: str
    stdout_bytes: bytes = b""


def _git_result(root: Path, args: list[str]) -> _GitResult:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=False, check=False)
    return _GitResult(result.returncode, result.stdout.decode(errors="replace"), result.stderr.decode(errors="replace"), result.stdout)


def _git(root: Path, args: list[str]) -> str:
    result = _git_result(root, args)
    if result.returncode != 0:
        raise FinalizationError("FINALIZATION_STALE", f"Git command failed: {' '.join(args)}: {result.stderr.strip()}")
    return result.stdout.rstrip("\r\n")


def _unstage_safely(root: Path, paths: list[str]) -> None:
    if paths:
        subprocess.run(["git", "restore", "--staged", "--", *paths], cwd=root, capture_output=True, text=True, check=False)


def _consume_finalization(marker: Path, plan: FinalizationPlan) -> None:
    marker.parent.mkdir(parents=True, exist_ok=True)
    try:
        with marker.open("x", encoding="utf-8") as handle:
            json.dump({"task_id": plan.task_id, "o5_run_id": plan.o5_run_id, "finalization_fingerprint": plan.finalization_fingerprint, "consumed_at": _now().isoformat()}, handle, sort_keys=True)
            handle.write("\n")
    except FileExistsError as exc:
        raise FinalizationError("ALREADY_FINALIZED", "This finalization approval has already reached the commit point") from exc


def _update_run_record(path: Path, updates: dict[str, Any]) -> None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.update(updates)
        path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FinalizationError("RUN_RECORD_FAILED", f"Could not update O5 run record: {exc}") from exc


class _FinalizationLock:
    def __init__(self, path: Path, plan: FinalizationPlan) -> None:
        self.path = path
        self.plan = plan
        self.held = False

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise FinalizationError("ANOTHER_TASK_ACTIVE", f"Active task lock exists; inspect {self.path} before removing it") from exc
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(f"task_id={self.plan.task_id}\nplan_fingerprint={self.plan.finalization_fingerprint}\ntimestamp={_now().isoformat()}\npid={os.getpid()}\n")
        self.held = True

    def release(self) -> None:
        if self.held:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            self.held = False


def _now() -> datetime:
    return datetime.now(timezone.utc)
