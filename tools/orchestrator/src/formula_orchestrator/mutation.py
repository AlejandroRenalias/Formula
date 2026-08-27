"""Baseline and per-execution mutation checks for real Codex edits."""

from __future__ import annotations

import hashlib
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .scope import TaskScope


class MutationSafetyError(RuntimeError):
    """The workspace changed outside the controller's safe contract."""


@dataclass(frozen=True)
class BaselineSnapshot:
    head_sha: str
    branch: str
    status: str
    filesystem: dict[str, tuple[int, int, str]]


@dataclass(frozen=True)
class ExecutionSnapshot:
    head_sha: str
    branch: str
    status: str
    changed_paths: tuple[str, ...]
    staged_paths: tuple[str, ...]
    filesystem: dict[str, tuple[int, int, str]]


@dataclass(frozen=True)
class MutationCheck:
    passed: bool
    changed_paths: tuple[str, ...]
    delta_paths: tuple[str, ...]
    violations: tuple[str, ...] = ()
    message: str = ""


def capture_baseline(repository_root: Path) -> BaselineSnapshot:
    head = _git(repository_root, ["rev-parse", "HEAD"])
    branch = _git(repository_root, ["symbolic-ref", "--short", "-q", "HEAD"]) or "DETACHED"
    status = _git(repository_root, ["status", "--porcelain", "--untracked-files=all"], preserve_whitespace=True)
    return BaselineSnapshot(head, branch, status, _filesystem_snapshot(repository_root))


def capture_execution_snapshot(repository_root: Path) -> ExecutionSnapshot:
    status = _git(repository_root, ["status", "--porcelain", "--untracked-files=all"], preserve_whitespace=True)
    return ExecutionSnapshot(
        _git(repository_root, ["rev-parse", "HEAD"]),
        _git(repository_root, ["symbolic-ref", "--short", "-q", "HEAD"]) or "DETACHED",
        status,
        _status_paths(status),
        _staged_paths(status),
        _filesystem_snapshot(repository_root),
    )


def verify_mutation(baseline: BaselineSnapshot, before: ExecutionSnapshot, after: ExecutionSnapshot, scope: TaskScope) -> MutationCheck:
    """Check resulting workspace state after an execution against baseline and scope."""
    filesystem_delta = _filesystem_delta(before.filesystem, after.filesystem)
    changed = tuple(sorted(set(after.changed_paths) | set(filesystem_delta)))
    delta = tuple(sorted((set(after.changed_paths) - set(before.changed_paths)) | set(filesystem_delta)))
    violations = list(scope.violations(changed))
    if after.head_sha != baseline.head_sha:
        violations.append("HEAD changed")
    if after.branch != baseline.branch:
        violations.append("branch/ref changed")
    if after.staged_paths:
        violations.extend(f"staged path: {path}" for path in after.staged_paths)
    if violations:
        unique = tuple(dict.fromkeys(violations))
        return MutationCheck(False, changed, delta, unique, f"Mutation safety failed: {'; '.join(unique)}")
    return MutationCheck(True, changed, delta, (), "Mutation safety passed within supplied task scope")


def _git(root: Path, args: list[str], preserve_whitespace: bool = False) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise MutationSafetyError(f"Git inspection failed: {result.stderr.strip()}")
    return result.stdout.rstrip() if preserve_whitespace else result.stdout.strip()


def _status_paths(status: str) -> tuple[str, ...]:
    return tuple(_status_path(line) for line in status.splitlines() if line.strip())


def _staged_paths(status: str) -> tuple[str, ...]:
    return tuple(_status_path(line) for line in status.splitlines() if line and line[0] not in (" ", "?") and line.strip())


def _status_path(line: str) -> str:
    path = line[3:] if len(line) >= 4 else line
    return path.rsplit(" -> ", 1)[-1]


def _filesystem_snapshot(root: Path) -> dict[str, tuple[int, int, str]]:
    result: dict[str, tuple[int, int, str]] = {}
    for current, directories, files in os.walk(root):
        directories[:] = [
            directory for directory in directories
            if directory not in {".git", ".venv", ".pytest_cache", ".uv-cache", "__pycache__"}
            and not directory.startswith(".pytest-tmp")
        ]
        current_path = Path(current)
        for filename in files:
            path = current_path / filename
            try:
                stat = path.stat()
                digest = ""
                relative = path.relative_to(root).as_posix()
                if relative.startswith(".env") or relative.startswith("tools/orchestrator"):
                    digest = hashlib.sha256(path.read_bytes()).hexdigest()
                result[relative] = (stat.st_size, stat.st_mtime_ns, digest)
            except OSError:
                continue
    return result


def _filesystem_delta(before: dict[str, tuple[int, int, str]], after: dict[str, tuple[int, int, str]]) -> tuple[str, ...]:
    return tuple(sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path)))
