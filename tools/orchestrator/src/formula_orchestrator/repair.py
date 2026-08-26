"""Typed repair requests and deterministic bounded repair prompts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .evidence import redact_secrets
from .reviewer import ReviewFinding


class RepairTrigger(str, Enum):
    TEST_FAILURE = "TEST_FAILURE"
    REVIEW_FINDINGS = "REVIEW_FINDINGS"


@dataclass(frozen=True)
class RepairRequest:
    run_id: str
    repair_attempt: int
    trigger: RepairTrigger
    original_task: str
    scope_description: str
    current_changed_paths: tuple[str, ...]
    current_cumulative_diff: str
    current_execution_delta: tuple[str, ...]
    test_command: str | None = None
    test_exit_code: int | None = None
    test_stdout: str = ""
    test_stderr: str = ""
    reviewer_findings: tuple[ReviewFinding, ...] = ()
    constraints: str = ""


def build_repair_prompt(request: RepairRequest, max_chars: int) -> str:
    prompt = f"""You are repairing the current implementation of the original task.

Fix only the demonstrated failure(s).
Preserve behavior that is already correct.
Stay inside the supplied allowed scope.
Do not broaden the task.
Do not commit, stage, push, merge, reset, stash, checkout, switch branches, or deploy.
Do not weaken or delete tests simply to obtain a passing result.
Do not bypass safety checks.
Do not access or print credentials.
Stop after making the required repair and summarize what changed.

Original task:
{request.original_task}

Repair attempt: {request.repair_attempt}
Trigger: {request.trigger.value}
Allowed scope: {request.scope_description}
Changed paths: {', '.join(request.current_changed_paths)}
Current execution delta: {', '.join(request.current_execution_delta)}
Cumulative implementation diff:
{request.current_cumulative_diff}

Test command: {request.test_command or 'not applicable'}
Test exit code: {request.test_exit_code}
Test stdout:
{request.test_stdout}
Test stderr:
{request.test_stderr}

Reviewer findings:
{_findings_text(request.reviewer_findings)}

Additional constraints:
{request.constraints}
"""
    prompt = redact_secrets(prompt)
    if len(prompt) > max_chars:
        raise ValueError(f"Repair input exceeds configured limit ({max_chars} characters)")
    return prompt


def _findings_text(findings: tuple[ReviewFinding, ...]) -> str:
    if not findings:
        return "none"
    return "\n".join(
        f"{finding.finding_id} [{finding.severity.value}] {finding.title}: {finding.description}; evidence={finding.evidence}; required_fix={finding.required_fix}"
        for finding in findings
    )
