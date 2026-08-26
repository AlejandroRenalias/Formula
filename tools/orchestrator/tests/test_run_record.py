from datetime import datetime

from formula_orchestrator.run_record import RunRecord


def test_run_record_construction_and_safe_serialization() -> None:
    record = RunRecord(run_id="run-1", task_id="task-1")
    data = record.to_dict()
    assert data["run_id"] == "run-1"
    assert data["task_id"] == "task-1"
    assert data["stage"] == "bootstrap"
    assert data["final_status"] == "NOT_STARTED"
    assert isinstance(datetime.fromisoformat(data["started_at"]), datetime)
    assert "OPENAI_API_KEY" not in repr(data)

