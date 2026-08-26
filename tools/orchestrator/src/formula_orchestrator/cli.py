"""Command-line skeleton for O0."""

from __future__ import annotations

import argparse

from .config import OrchestratorConfig
from .preflight import PreflightError, run_preflight, validate_repository
from .smoke import run_smoke
from .o2 import run_codex_test_smoke
from .o3 import run_codex_test_review_smoke, run_review_smoke
from .test_runner import FormulaTestRunner


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="formula-orchestrator")
    parser.add_argument("command", choices=("check", "codex-smoke", "test-gate", "codex-test-smoke", "review-smoke", "codex-test-review-smoke"), help="run an orchestrator command")
    args = parser.parse_args(argv)
    if args.command == "check":
        try:
            print(run_preflight(OrchestratorConfig.from_environment()).message)
        except (FileNotFoundError, PreflightError, ValueError) as exc:
            print(f"Formula preflight failed: {exc}")
            return 1
        return 0
    if args.command == "codex-smoke":
        try:
            result = run_smoke(OrchestratorConfig.from_environment())
        except (FileNotFoundError, PreflightError, ValueError) as exc:
            print(f"Codex smoke failed before execution: {exc}")
            return 1
        if result.run_record.final_status != "SUCCESS":
            print(f"Codex smoke failed: {result.run_record.error or result.run_record.final_status}")
            return 1
        print(f"Codex smoke passed; marker: {result.run_record.smoke_marker_path}")
        return 0
    if args.command == "test-gate":
        try:
            config = OrchestratorConfig.from_environment()
            validate_repository(config)
            result = FormulaTestRunner().run(config.repository_root, config.test_command, config.test_timeout_seconds)
        except (FileNotFoundError, PreflightError, ValueError) as exc:
            print(f"Test gate failed before execution: {exc}")
            return 1
        if not result.passed:
            print(f"Test gate FAIL (exit_code={result.exit_code}, timed_out={result.timed_out}): {result.execution_error or 'test command failed'}")
            return 1
        print(f"Test gate PASS (exit_code={result.exit_code}, duration_seconds={result.duration_seconds:.2f})")
        return 0
    if args.command == "codex-test-smoke":
        try:
            result = run_codex_test_smoke(OrchestratorConfig.from_environment())
        except (FileNotFoundError, PreflightError, ValueError) as exc:
            print(f"O2 smoke failed before execution: {exc}")
            return 1
        if result.run_record.final_status != "O2_SUCCESS":
            print(f"O2 smoke failed: {result.run_record.error or result.run_record.final_status}")
            return 1
        print(f"O2 smoke passed; run record: {result.run_record.run_id}")
        return 0
    if args.command == "review-smoke":
        try:
            result = run_review_smoke(OrchestratorConfig.from_environment())
        except (FileNotFoundError, PreflightError, ValueError) as exc:
            print(f"Review smoke failed before execution: {exc}")
            return 1
        if result.run_record.final_status != "SUCCESS":
            print(f"Review smoke failed: {result.run_record.error or result.run_record.final_status}")
            return 1
        print(f"Review smoke passed; run record: {result.run_record.run_id}")
        return 0
    if args.command == "codex-test-review-smoke":
        try:
            result = run_codex_test_review_smoke(OrchestratorConfig.from_environment())
        except (FileNotFoundError, PreflightError, ValueError) as exc:
            print(f"O3 smoke failed before execution: {exc}")
            return 1
        if result.run_record.final_status != "SUCCESS":
            print(f"O3 smoke failed: {result.run_record.error or result.run_record.final_status}")
            return 1
        print(f"O3 smoke passed; run record: {result.run_record.run_id}")
        return 0
    return 2
