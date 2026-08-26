"""Read-only, bounded, redacted evidence collection for GPT review."""

from __future__ import annotations

import ast
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
    tracked_diff = _git_command(repository_root, ["diff", "HEAD", "--no-ext-diff", "--binary"])
    untracked_diff = _untracked_file_evidence(repository_root, status)
    diff = tracked_diff + untracked_diff
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
    try:
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    except (OSError, UnicodeError) as exc:
        raise EvidenceError(f"Git evidence collection failed: {exc}") from exc
    if result.returncode != 0:
        raise EvidenceError(f"Git evidence collection failed: {result.stderr.strip()}")
    return result.stdout


def _status_path(line: str) -> str:
    path = line[3:] if len(line) >= 4 else line
    if " -> " in path:
        path = path.rsplit(" -> ", 1)[-1]
    return _decode_git_path(path)


def _untracked_file_evidence(root: Path, status: str) -> str:
    sections: list[tuple[str, str]] = []
    repository = root.resolve(strict=True)
    for line in status.splitlines():
        if not line.startswith("?? "):
            continue
        status_path = _status_path(line)
        relative_path = Path(status_path)
        if relative_path.is_absolute():
            raise EvidenceError(f"Untracked path is outside the repository: {status_path}")
        raw_candidate = root / relative_path
        candidate = raw_candidate.resolve(strict=False)
        try:
            display_path = candidate.relative_to(repository).as_posix()
        except ValueError as exc:
            raise EvidenceError(f"Untracked path is outside the repository: {status_path}") from exc
        if raw_candidate.is_symlink() or not candidate.is_file():
            raise EvidenceError(f"Untracked path is not an ordinary file: {status_path}")
        try:
            content = candidate.read_bytes().decode("utf-8")
        except (OSError, UnicodeError) as exc:
            raise EvidenceError(f"Unable to read untracked UTF-8 file: {status_path}") from exc
        if "\x00" in content:
            raise EvidenceError(f"Untracked file is binary: {status_path}")
        sections.append((display_path, _format_untracked_diff(display_path, content)))
    return "".join(section for _, section in sorted(sections))


def _format_untracked_diff(path: str, content: str) -> str:
    lines = content.splitlines()
    body = "".join(f"+{line}\n" for line in lines)
    if not lines:
        body = ""
    return (
        f"diff --git a/{path} b/{path}\n"
        "new file mode 100644\n"
        "--- /dev/null\n"
        f"+++ b/{path}\n"
        f"@@ -0,0 +1,{len(lines)} @@\n"
        f"{body}"
    )


def _decode_git_path(path: str) -> str:
    if len(path) >= 2 and path[0] == '"' and path[-1] == '"':
        try:
            decoded = ast.literal_eval(path)
        except (SyntaxError, ValueError) as exc:
            raise EvidenceError(f"Unable to decode Git path: {path}") from exc
        if not isinstance(decoded, str):
            raise EvidenceError(f"Unable to decode Git path: {path}")
        return decoded
    return path
