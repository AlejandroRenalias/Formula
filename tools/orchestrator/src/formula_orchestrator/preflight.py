"""Deterministic checks required before a future orchestrated run."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from .config import OrchestratorConfig


class PreflightError(RuntimeError):
    """Raised when the Formula workspace is unsafe or unavailable."""


@dataclass(frozen=True)
class PreflightReport:
    repository_root: Path
    git_repository: bool
    working_tree_clean: bool
    message: str


def run_preflight(config: OrchestratorConfig) -> PreflightReport:
    root = config.repository_root
    if not root.is_dir():
        raise PreflightError(f"Formula repository does not exist: {root}")
    missing = [name for name in ("src", "tests") if not (root / name).is_dir()]
    if missing:
        raise PreflightError(f"Formula repository is missing expected directories: {', '.join(missing)}")
    git_check = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True)
    git_root = Path(git_check.stdout.strip()).resolve() if git_check.returncode == 0 else None
    if git_root != root:
        raise PreflightError(f"Formula repository is not a Git repository: {root}")
    status = subprocess.run(["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True)
    if status.returncode != 0:
        raise PreflightError(f"Unable to inspect Formula Git working tree: {status.stderr.strip()}")
    if status.stdout:
        raise PreflightError("Formula working tree is dirty; refusing to start without human review of existing changes")
    return PreflightReport(root, True, True, f"Formula preflight passed: {root}")
