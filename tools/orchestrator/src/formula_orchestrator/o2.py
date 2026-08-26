"""O2 composition: one O1 Codex smoke, then one deterministic test gate."""

from __future__ import annotations

from dataclasses import dataclass

from .config import OrchestratorConfig
from .preflight import run_preflight
from .run_record import RunRecord
from .smoke import ExecutorProtocol, require_authentication, run_preflighted_smoke, _write_record
from .test_runner import FormulaTestRunner, TestRunResult


@dataclass(frozen=True)
class O2Result:
    run_record: RunRecord
    test_result: TestRunResult | None


def run_codex_test_smoke(config: OrchestratorConfig, executor: ExecutorProtocol | None = None, test_runner: FormulaTestRunner | None = None) -> O2Result:
    """Run the O2 state machine once; no stage is retried."""
    run_preflight(config)
    require_authentication()
    smoke = run_preflighted_smoke(config, executor)
    record = smoke.run_record
    if not smoke.codex_result or not smoke.codex_result.success:
        record.final_status = "O2_CODEX_FAILED"
        _write_record(config, record)
        return O2Result(record, None)
    if not smoke.safety or not smoke.safety.passed:
        record.final_status = "O2_SAFETY_FAILED"
        _write_record(config, record)
        return O2Result(record, None)

    test_result = (test_runner or FormulaTestRunner()).run(config.repository_root, config.test_command, config.test_timeout_seconds)
    record.test_gate_status = test_result.gate_status.value
    record.test_exit_code = test_result.exit_code
    record.test_duration_seconds = test_result.duration_seconds
    record.test_timed_out = test_result.timed_out
    record.test_output = {"stdout": test_result.stdout, "stderr": test_result.stderr}
    if test_result.execution_error:
        record.error = test_result.execution_error
    record.final_status = "O2_SUCCESS" if test_result.passed else "O2_TEST_FAILED"
    _write_record(config, record)
    return O2Result(record, test_result)

