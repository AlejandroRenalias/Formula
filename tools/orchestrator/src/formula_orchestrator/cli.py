"""Command-line skeleton for O0."""

from __future__ import annotations

import argparse

from .config import OrchestratorConfig
from .preflight import PreflightError, run_preflight


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="formula-orchestrator")
    parser.add_argument("command", choices=("check",), help="run an O0 repository preflight")
    args = parser.parse_args(argv)
    if args.command == "check":
        try:
            print(run_preflight(OrchestratorConfig.from_environment()).message)
        except (FileNotFoundError, PreflightError, ValueError) as exc:
            print(f"Formula preflight failed: {exc}")
            return 1
        return 0
    return 2

