"""Minimal run-record contract for later orchestration stages."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class RunRecord:
    run_id: str
    task_id: str
    stage: str = "bootstrap"
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: datetime | None = None
    test_result: str | None = None
    loop_count: int = 0
    final_status: str = "NOT_STARTED"
    task_type: str = "bootstrap"
    codex_success: bool | None = None
    codex_thread_id: str | None = None
    usage_summary: dict[str, Any] | None = None
    smoke_marker_path: str | None = None
    safety_verification: str | None = None
    error: str | None = None
    test_gate_status: str | None = None
    test_exit_code: int | None = None
    test_duration_seconds: float | None = None
    test_timed_out: bool | None = None
    test_output: dict[str, str] | None = None
    reviewer_model: str | None = None
    review_verdict: str | None = None
    review_summary: str | None = None
    review_findings: list[dict[str, Any]] | None = None
    review_duration_seconds: float | None = None
    review_usage: dict[str, Any] | None = None
    review_error: str | None = None
    baseline: dict[str, Any] | None = None
    cycles: list[dict[str, Any]] = field(default_factory=list)
    repair_count: int = 0
    last_failure: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("started_at", "finished_at"):
            if data[key] is not None:
                data[key] = data[key].isoformat()
        return data
