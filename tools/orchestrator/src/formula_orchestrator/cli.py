"""Command-line skeleton for O0."""

from __future__ import annotations

import argparse

from .config import OrchestratorConfig
from .preflight import PreflightError, run_preflight
from .smoke import run_smoke


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="formula-orchestrator")
    parser.add_argument("command", choices=("check", "codex-smoke"), help="run an O0 preflight or one bounded Codex smoke task")
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
    return 2
