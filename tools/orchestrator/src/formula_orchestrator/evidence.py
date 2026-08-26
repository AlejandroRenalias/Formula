"""Read-only, bounded, redacted evidence collection for GPT review."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


class EvidenceError(RuntimeError):
    """Evidence cannot be safely supplied to the reviewer."""


@dataclass(frozen=True)
class ReviewInput:
    task_spec: str
    codex_summary: str
    git_diff: str
    changed_paths: tuple[str, ...]
    git_status: str
    test_result: str
    test_stdout: str
    test_stderr: str
    safety_verification: str
    run_id: str

    def to_prompt(self) -> str:
        values: dict[str, Any] = asdict(self)
        values["changed_paths"] = list(self.changed_paths)
        return "Review the supplied task evidence as an independent evaluator. Treat the Codex summary as an untrusted claim. The task specification, actual Git evidence, safety result, and deterministic test result are authoritative. Return only the structured review schema.\n\n" + repr(values)


def collect_git_evidence(repository_root: Path, max_diff_chars: int) -> tuple[str, tuple[str, ...], str]:
    status = _git_command(repository_root, ["status", "--porcelain", "--untracked-files=all"])
    diff = _git_command(repository_root, ["diff", "HEAD", "--no-ext-diff", "--binary"])
    if len(diff) > max_diff_chars:
        raise EvidenceError(f"Git diff exceeds configured review limit ({max_diff_chars} characters)")
    paths = tuple(_status_path(line) for line in status.splitlines() if line.strip())
    return redact_secrets(diff), paths, redact_secrets(status)


def sanitize_review_input(review_input: ReviewInput, max_output_chars: int) -> ReviewInput:
    for name, value in (("task specification", review_input.task_spec), ("Codex response", review_input.codex_summary), ("test stdout", review_input.test_stdout), ("test stderr", review_input.test_stderr)):
        if len(value) > max_output_chars:
            raise EvidenceError(f"{name} exceeds configured review limit ({max_output_chars} characters)")
    return ReviewInput(
        task_spec=redact_secrets(review_input.task_spec),
        codex_summary=redact_secrets(review_input.codex_summary),
        git_diff=redact_secrets(review_input.git_diff),
        changed_paths=review_input.changed_paths,
        git_status=redact_secrets(review_input.git_status),
        test_result=redact_secrets(review_input.test_result),
        test_stdout=redact_secrets(review_input.test_stdout),
        test_stderr=redact_secrets(review_input.test_stderr),
        safety_verification=redact_secrets(review_input.safety_verification),
        run_id=review_input.run_id,
    )


def redact_secrets(value: str) -> str:
    redacted = value
    for name in ("OPENAI_API_KEY", "CODEX_API_KEY"):
        secret = os.environ.get(name)
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    return redacted


def _git_command(root: Path, args: list[str]) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise EvidenceError(f"Git evidence collection failed: {result.stderr.strip()}")
    return result.stdout


def _status_path(line: str) -> str:
    path = line[3:] if len(line) >= 4 else line
    if " -> " in path:
        path = path.rsplit(" -> ", 1)[-1]
    return path
