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
    review_verdict: str | None = None
    loop_count: int = 0
    final_status: str = "NOT_STARTED"
    task_type: str = "bootstrap"
    codex_success: bool | None = None
    codex_thread_id: str | None = None
    usage_summary: dict[str, Any] | None = None
    smoke_marker_path: str | None = None
    safety_verification: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        for key in ("started_at", "finished_at"):
            if data[key] is not None:
                data[key] = data[key].isoformat()
        return data
