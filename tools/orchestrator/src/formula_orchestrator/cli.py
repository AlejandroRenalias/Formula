"""Command-line skeleton for O0."""

from __future__ import annotations

import argparse
from pathlib import Path

from .config import OrchestratorConfig
from .preflight import PreflightError, run_preflight, validate_repository
from .smoke import run_smoke
from .o2 import run_codex_test_smoke
from .o3 import run_codex_test_review_smoke, run_review_smoke
from .o4 import BoundedRepairController, run_repair_smoke
from .o5 import O5Error, prepare_task, run_task
from .finalization import FinalizationError, finalize_task
from .test_runner import FormulaTestRunner
from .commander import run_commander


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="formula-orchestrator")
    parser.add_argument("command", choices=("commander", "check", "codex-smoke", "test-gate", "codex-test-smoke", "review-smoke", "codex-test-review-smoke", "repair-smoke", "task-prepare", "task-run", "task-finalize"), help="run an orchestrator command")
    parser.add_argument("--task-file", type=Path, help="structured O5 task request JSON")
    parser.add_argument("--plan-file", type=Path, help="prepared O5 plan JSON")
    parser.add_argument("--run-file", type=Path, help="O5 run record for finalization")
    parser.add_argument("--approve", help="explicit O5 approval token")
    args = parser.parse_args(argv)
    if args.command == "commander":
        return run_commander(OrchestratorConfig.from_environment())
    if args.command == "task-prepare":
        if args.task_file is None:
            parser.error("task-prepare requires --task-file")
        try:
            prepared = prepare_task(args.task_file, OrchestratorConfig.from_environment())
        except (O5Error, FileNotFoundError, PreflightError, ValueError) as exc:
            status = exc.status if isinstance(exc, O5Error) else "TASK_PREPARE_FAILED"
            print(f"{status}: {exc}")
            return 1
        print("TASK PREPARED")
        print(f"\nTask: {prepared.plan.task_id}")
        print(f"Baseline HEAD: {prepared.plan.baseline_head_sha}")
        print(f"Baseline tests: {prepared.plan.baseline_test_status}")
        print(f"Scope risk: {prepared.plan.scope_risk}")
        print("Allowed paths:")
        for path in prepared.plan.allowed_paths:
            print(f"- {path}")
        print("Allowed roots:")
        for path in prepared.plan.allowed_roots:
            print(f"- {path}")
        print(f"Repair budget: {prepared.plan.approved_repair_limit}")
        print(f"Codex model: {prepared.plan.codex_model}")
        print(f"Codex reasoning: {prepared.plan.codex_reasoning_effort}")
        print(f"Reviewer model: {prepared.plan.coordinator_model}")
        print(f"Reviewer reasoning: {prepared.plan.coordinator_reasoning_effort}")
        print(f"\nPlan file: {prepared.plan_path}")
        print(f"Approval token:\n{prepared.approval_token}")
        print("\nNo Codex execution has occurred.")
        print(f"\nTo execute this exact plan:\nformula-orchestrator task-run --plan-file \"{prepared.plan_path}\" --approve {prepared.approval_token}")
        return 0
    if args.command == "task-run":
        if args.plan_file is None or not args.approve:
            parser.error("task-run requires --plan-file and --approve")
        try:
            result = run_task(args.plan_file, args.approve, OrchestratorConfig.from_environment())
        except (O5Error, FileNotFoundError, PreflightError, ValueError) as exc:
            status = exc.status if isinstance(exc, O5Error) else "TASK_RUN_FAILED"
            print(f"{status}: {exc}")
            return 1
        print(f"O5 status: {result.run_record.final_status}")
        if result.run_record.final_status == "READY_FOR_HUMAN_REVIEW":
            print("READY FOR HUMAN REVIEW")
            print("\nChanged paths:")
            for path in (getattr(result.run_record, "final_evidence", None) or {}).get("changed_paths", []):
                print(f"- {path}")
            print(f"Tests: {getattr(result.run_record, 'fresh_baseline_test_status', 'UNKNOWN')}")
            print(f"Repairs used: {getattr(result.run_record, 'repair_count', 0)}")
            print("No commit, push, merge, or deployment was performed.")
            print("Review: git status; git diff --check; git diff")
            print(f"\nIf you accept this exact result:\nformula-orchestrator task-finalize --run-file \"{getattr(result.run_record, 'run_file_path', '')}\" --approve {getattr(result.run_record, 'finalization_token', '')}")
            return 0
        print(f"Technical result: {result.run_record.error or result.run_record.final_status}")
        return 1
    if args.command == "task-finalize":
        if args.run_file is None or not args.approve:
            parser.error("task-finalize requires --run-file and --approve")
        try:
            result = finalize_task(args.run_file, args.approve, OrchestratorConfig.from_environment())
        except (FinalizationError, FileNotFoundError, PreflightError, ValueError) as exc:
            status = exc.status if isinstance(exc, FinalizationError) else "FINALIZATION_FAILED"
            print(f"{status}: {exc}")
            return 1
        print("FINALIZED")
        print(f"Commit: {result.commit_sha}")
        print(f"Push: {'SUCCESS' if result.push_success else 'FAILED'}")
        return 0
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
    if args.command == "repair-smoke":
        try:
            result = run_repair_smoke(OrchestratorConfig.from_environment())
        except (FileNotFoundError, PreflightError, ValueError) as exc:
            print(f"Repair smoke failed before execution: {exc}")
            return 1
        if result.run_record.final_status != "SUCCESS":
            print(f"Repair smoke failed: {result.run_record.error or result.run_record.final_status}")
            return 1
        print(f"Repair smoke passed; run record: {result.run_record.run_id}")
        return 0
    return 2
