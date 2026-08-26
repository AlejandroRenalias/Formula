"""One bounded Codex smoke task and authoritative post-run safety checks."""

from __future__ import annotations

import asyncio
import json
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol

from .codex_executor import CodexExecutionResult, CodexExecutor
from .config import OrchestratorConfig
from .preflight import PreflightError, run_preflight
from .run_record import RunRecord


class ExecutorProtocol(Protocol):
    async def execute(self, repository_root: Path, task_text: str, model, run_id: str) -> CodexExecutionResult: ...


@dataclass(frozen=True)
class SafetyVerification:
    passed: bool
    unexpected_paths: tuple[str, ...] = ()
    marker_exists: bool = False
    message: str = ""


@dataclass(frozen=True)
class SmokeResult:
    run_record: RunRecord
    codex_result: CodexExecutionResult | None
    safety: SafetyVerification | None


def smoke_task(marker_path: Path, run_id: str) -> str:
    return f"""Inspect the Formula workspace at the supplied working directory and identify it as the Formula F1 strategy project. Read only a small number of relevant project files. Create exactly one harmless JSON marker at {marker_path} containing only: run_id={run_id}, task_type=codex-smoke, and a short project identification summary. Do not include credentials, API keys, environment values, or file contents. Do not modify src/, tests/, project configuration, Git state, or any path outside the configured run-log directory. Do not create any other files. Return a concise structured summary."""


def run_smoke(config: OrchestratorConfig, executor: ExecutorProtocol | None = None) -> SmokeResult:
    run_preflight(config)
    _require_authentication()
    result = run_preflighted_smoke(config, executor)
    _write_record(config, result.run_record)
    return result


def run_preflighted_smoke(config: OrchestratorConfig, executor: ExecutorProtocol | None = None) -> SmokeResult:
    """Run the O1 portion after the caller has completed preflight/auth checks."""
    run_id = uuid.uuid4().hex
    marker_path = config.run_log_directory / f"codex-smoke-{run_id}.json"
    marker_path.parent.mkdir(parents=True, exist_ok=True)
    record = RunRecord(run_id=run_id, task_id=run_id, stage="codex-smoke", task_type="codex-smoke", started_at=datetime.now(timezone.utc), smoke_marker_path=str(marker_path))
    executor = executor or CodexExecutor()
    try:
        codex_result = asyncio.run(executor.execute(config.repository_root, smoke_task(marker_path, run_id), config.codex, run_id))
    except Exception as exc:
        codex_result = CodexExecutionResult(success=False, error=f"Codex boundary error: {exc}")
    record.codex_success = codex_result.success
    record.codex_thread_id = codex_result.thread_id
    record.usage_summary = codex_result.usage
    if not codex_result.success:
        record.final_status = "CODEX_FAILED"
        record.error = codex_result.error or "Codex returned failure"
        record.finished_at = datetime.now(timezone.utc)
        return SmokeResult(record, codex_result, None)
    safety = verify_smoke_safety(config, marker_path)
    record.safety_verification = safety.message
    record.finished_at = datetime.now(timezone.utc)
    if safety.passed:
        record.final_status = "SUCCESS"
    else:
        record.final_status = "SAFETY_FAILED"
        record.error = safety.message
    return SmokeResult(record, codex_result, safety)


def require_authentication() -> None:
    if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("CODEX_API_KEY")):
        raise PreflightError("Required OpenAI authentication is missing; set OPENAI_API_KEY before codex-smoke")


_require_authentication = require_authentication


def verify_smoke_safety(config: OrchestratorConfig, marker_path: Path) -> SafetyVerification:
    status = _git_status(config.repository_root)
    unexpected = tuple(line.strip() for line in status.splitlines() if line.strip())
    marker_ok, marker_message = _validate_marker(marker_path)
    if unexpected:
        return SafetyVerification(False, unexpected, marker_ok, f"Unexpected Git changes after Codex: {'; '.join(unexpected)}")
    if not marker_ok:
        return SafetyVerification(False, (), False, marker_message)
    return SafetyVerification(True, (), True, "Smoke marker present and Git working tree has no unexpected changes")


def _git_status(root: Path) -> str:
    import subprocess
    result = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"], cwd=root, capture_output=True, text=True)
    return result.stdout if result.returncode == 0 else f"git status failed: {result.stderr.strip()}"


def _validate_marker(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, f"Expected smoke marker is missing: {path}"
    if path.stat().st_size > 16_384:
        return False, "Smoke marker is unexpectedly large"
    marker_text = path.read_text(encoding="utf-8")
    if re.search(r"OPENAI_API_KEY|CODEX_API_KEY|sk-[A-Za-z0-9]", marker_text, re.IGNORECASE):
        return False, "Smoke marker contains a credential-like value"
    try:
        value = json.loads(marker_text)
    except json.JSONDecodeError as exc:
        return False, f"Smoke marker is not valid JSON: {exc.msg}"
    if not isinstance(value, dict) or value.get("task_type") != "codex-smoke":
        return False, "Smoke marker has malformed task metadata"
    return True, ""


def _write_record(config: OrchestratorConfig, record: RunRecord) -> None:
    path = config.run_log_directory / f"{record.run_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
