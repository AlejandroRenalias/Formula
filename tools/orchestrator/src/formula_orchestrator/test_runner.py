"""Bounded, credential-sanitized execution of the trusted Formula test command."""

from __future__ import annotations

import os
import shlex
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping


MAX_PERSISTED_OUTPUT = 12_000
SENSITIVE_ENVIRONMENT_NAMES = frozenset({"OPENAI_API_KEY", "CODEX_API_KEY"})


class TestGateStatus(str, Enum):
    __test__ = False
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass(frozen=True)
class TestRunResult:
    __test__ = False
    argv: tuple[str, ...]
    exit_code: int | None
    passed: bool
    stdout: str
    stderr: str
    duration_seconds: float
    timed_out: bool
    execution_error: str | None = None

    @property
    def gate_status(self) -> TestGateStatus:
        return TestGateStatus.PASS if self.passed else TestGateStatus.FAIL


def is_repairable_test_failure(result: TestRunResult) -> bool:
    """Only a completed process with exit code 1 is eligible for repair."""
    return (
        not result.passed
        and not result.timed_out
        and result.execution_error is None
        and result.exit_code == 1
    )


class FormulaTestRunner:
    def __init__(self, output_limit: int = MAX_PERSISTED_OUTPUT) -> None:
        if output_limit <= 0:
            raise ValueError("output_limit must be positive")
        self.output_limit = output_limit

    def run(self, repository_root: Path, command: str, timeout_seconds: float) -> TestRunResult:
        try:
            argv = tuple(shlex.split(command, posix=True))
        except ValueError as exc:
            return TestRunResult((), None, False, "", "", 0.0, False, f"Invalid test command: {exc}")
        if not argv:
            return TestRunResult((), None, False, "", "", 0.0, False, "Test command is empty")
        if timeout_seconds <= 0:
            return TestRunResult(argv, None, False, "", "", 0.0, False, "Test timeout must be positive")

        environment, secrets = _test_environment()
        started = time.monotonic()
        try:
            completed = subprocess.run(
                list(argv),
                cwd=repository_root,
                env=environment,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
                shell=False,
            )
            duration = time.monotonic() - started
            return TestRunResult(
                argv, completed.returncode, completed.returncode == 0,
                _bounded_and_redacted(completed.stdout, secrets, self.output_limit),
                _bounded_and_redacted(completed.stderr, secrets, self.output_limit),
                duration, False,
            )
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - started
            return TestRunResult(
                argv, None, False,
                _bounded_and_redacted(_as_text(exc.stdout), secrets, self.output_limit),
                _bounded_and_redacted(_as_text(exc.stderr), secrets, self.output_limit),
                duration, True, "Test command timed out",
            )
        except OSError as exc:
            return TestRunResult(argv, None, False, "", "", time.monotonic() - started, False, f"Test command could not execute: {exc}")


def _test_environment() -> tuple[dict[str, str], dict[str, str]]:
    original = dict(os.environ)
    sanitized = {key: value for key, value in original.items() if key not in SENSITIVE_ENVIRONMENT_NAMES}
    secrets = {key: value for key, value in original.items() if key in SENSITIVE_ENVIRONMENT_NAMES and value}
    return sanitized, secrets


def _as_text(value: str | bytes | None) -> str:
    if value is None:
        return ""
    return value.decode(errors="replace") if isinstance(value, bytes) else value


def _bounded_and_redacted(value: str, secrets: Mapping[str, str], limit: int) -> str:
    redacted = value
    for name in SENSITIVE_ENVIRONMENT_NAMES:
        secret = secrets.get(name)
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    if len(redacted) <= limit:
        return redacted
    head = limit // 2
    tail = limit - head
    return f"{redacted[:head]}\n...[OUTPUT TRUNCATED]...\n{redacted[-tail:]}"
