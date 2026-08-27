"""Interactive, human-gated Formula coordinator for the local O5 lifecycle."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import uuid
from pathlib import Path
from typing import Any

from openai import APIStatusError

from .config import OrchestratorConfig
from .evidence import redact_secrets
from .finalization import FinalizationError, FinalizationPlan, finalize_task
from .o5 import O5Error, PreparedTaskPlan, TaskRequest, prepare_task, run_task
from .preflight import PreflightError
from .smoke import require_authentication


INSTRUCTIONS = """You are Formula Commander, the engineering coordinator, not the implementer.
Existing deterministic O5 machinery owns execution safety. Tool outputs are authoritative for
repository and task state; conversational memory is not. Inspect current state before any
state-dependent decision. Never claim an action happened unless its tool confirms it. Never
bypass O5 or a human approval interruption. Prefer narrow task scopes and never exceed repair_limit
2. Never expose credentials, ask for OPENAI_API_KEY, execute shell/Git commands, or invent roadmap
progress. The available tools are the only way to inspect or change the Formula lifecycle. For v1,
"continue" means continue a concrete lifecycle represented by current tool/session state; do not
invent the next Formula milestone (that is reserved for C2)."""


def _git(root: Path, args: tuple[str, ...]) -> str:
    """Run one of the fixed, read-only inspection commands."""
    allowed = {
        ("rev-parse", "HEAD"),
        ("symbolic-ref", "--short", "-q", "HEAD"),
        ("status", "--porcelain", "--untracked-files=all"),
    }
    if args not in allowed:
        raise ValueError("unsupported Git inspection")
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "Git inspection failed")
    return result.stdout.rstrip("\r\n")


def inspect_project_state(config: OrchestratorConfig) -> dict[str, Any]:
    status = _git(config.repository_root, ("status", "--porcelain", "--untracked-files=all"))
    changed = [line[3:] if len(line) >= 4 else line for line in status.splitlines() if line.strip()]
    return {
        "repository_path": str(config.repository_root),
        "head": _git(config.repository_root, ("rev-parse", "HEAD")),
        "branch": _git(config.repository_root, ("symbolic-ref", "--short", "-q", "HEAD")) or "DETACHED",
        "clean": not bool(status),
        "changed_paths": sorted(path.rsplit(" -> ", 1)[-1] for path in changed),
        "coordinator": {"model": config.coordinator.model, "reasoning_effort": config.coordinator.reasoning_effort},
        "codex": {"model": config.codex.model, "reasoning_effort": config.codex.reasoning_effort},
        "repair_limit": config.max_repair_loops,
        "latest_local_o5": _latest_records(config),
    }


def _latest_records(config: OrchestratorConfig) -> dict[str, Any] | None:
    records = sorted(config.run_log_directory.glob("o5-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not records:
        return None
    try:
        data = json.loads(records[0].read_text(encoding="utf-8"))
        return {key: data.get(key) for key in ("run_id", "task_id", "final_status", "run_file_path", "finalization_plan_path")}
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {"status": "UNREADABLE_LATEST_RECORD"}


def prepare_formula_task(
    config: OrchestratorConfig,
    task_id: str,
    title: str,
    objective: str,
    acceptance_criteria: list[str],
    allowed_paths: list[str] | None = None,
    allowed_roots: list[str] | None = None,
    repair_limit: int = 2,
    commit_message: str | None = None,
) -> dict[str, Any]:
    request = TaskRequest(
        task_id=task_id, title=title, objective=objective,
        acceptance_criteria=acceptance_criteria, allowed_paths=allowed_paths or [],
        allowed_roots=allowed_roots or [], repair_limit=repair_limit, commit_message=commit_message,
    )
    task_dir = config.run_log_directory / "commander" / "tasks"
    task_dir.mkdir(parents=True, exist_ok=True)
    task_file = task_dir / f"{request.task_id}-{uuid.uuid4().hex}.json"
    task_file.write_text(json.dumps(request.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    prepared = prepare_task(task_file, config)
    plan = prepared.plan
    return {
        "task_id": plan.task_id, "title": plan.title, "baseline_head": plan.baseline_head_sha,
        "baseline_tests": plan.baseline_test_status, "scope_risk": plan.scope_risk,
        "allowed_paths": plan.allowed_paths, "allowed_roots": plan.allowed_roots,
        "repair_budget": plan.approved_repair_limit, "codex_model": plan.codex_model,
        "codex_reasoning": plan.codex_reasoning_effort, "reviewer_model": plan.coordinator_model,
        "reviewer_reasoning": plan.coordinator_reasoning_effort, "plan_path": str(prepared.plan_path),
        "approval_token": prepared.approval_token,
    }


def run_prepared_task(config: OrchestratorConfig, plan_path: str, approval_token: str) -> dict[str, Any]:
    result = run_task(_inside_run_logs(config, plan_path), approval_token, config)
    record = result.run_record
    evidence = record.final_evidence or {}
    final_technical_test_status = None
    if record.finalization_plan_path:
        finalization_path = _inside_run_logs(config, record.finalization_plan_path)
        try:
            finalization_plan = FinalizationPlan.model_validate_json(finalization_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise ValueError(f"invalid finalization plan: {exc}") from exc
        final_technical_test_status = finalization_plan.final_test_result
    return {"o5_status": record.final_status, "task_id": record.task_id,
            "changed_paths": evidence.get("changed_paths", []),
            "fresh_baseline_test_status": record.fresh_baseline_test_status,
            "final_technical_test_status": final_technical_test_status,
            "repairs_used": record.repair_count, "run_file_path": record.run_file_path,
            "finalization_token": record.finalization_token if record.final_status == "READY_FOR_HUMAN_REVIEW" else None,
            "error": record.error}


def inspect_o5_run(config: OrchestratorConfig, run_path: str) -> dict[str, Any]:
    path = _inside_run_logs(config, run_path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid O5 run record: {exc}") from exc
    return {key: data.get(key) for key in ("run_id", "task_id", "final_status", "error", "final_evidence",
                                            "repair_count", "run_file_path", "finalization_plan_path", "finalization_token")}


def finalize_ready_task(config: OrchestratorConfig, run_path: str, approval_token: str) -> dict[str, Any]:
    outcome = finalize_task(_inside_run_logs(config, run_path), approval_token, config)
    return {"final_status": outcome.status, "commit_sha": outcome.commit_sha, "push_success": outcome.push_success}


def _inside_run_logs(config: OrchestratorConfig, value: str) -> Path:
    root = config.run_log_directory.resolve()
    path = Path(value).expanduser().resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("O5 paths must be inside the configured run-log directory") from exc
    if not path.is_file():
        raise ValueError("O5 record does not exist or is not a file")
    return path


def render_run_approval(config: OrchestratorConfig, plan_path: str) -> str:
    path = _inside_run_logs(config, plan_path)
    try:
        plan = PreparedTaskPlan.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"invalid prepared plan: {exc}") from exc
    fields = (("Task", plan.task_id), ("Title", plan.title), ("Baseline", plan.baseline_head_sha),
              ("Baseline tests", plan.baseline_test_status), ("Allowed paths", ", ".join(plan.allowed_paths)),
              ("Allowed roots", ", ".join(plan.allowed_roots)), ("Repair budget", plan.approved_repair_limit),
              ("Codex model/reasoning", f"{plan.codex_model} / {plan.codex_reasoning_effort}"),
              ("Reviewer model/reasoning", f"{plan.coordinator_model} / {plan.coordinator_reasoning_effort}"))
    return "ACTION: RUN FORMULA TASK\n" + "\n".join(f"{key}: {value}" for key, value in fields) + "\nApprove? [y/N]"


def render_finalization_approval(config: OrchestratorConfig, run_path: str) -> str:
    run = inspect_o5_run(config, run_path)
    plan_value = run.get("finalization_plan_path")
    if not isinstance(plan_value, str):
        raise ValueError("run has no finalization plan")
    plan_path = _inside_run_logs(config, plan_value)
    try:
        plan = FinalizationPlan.model_validate_json(plan_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"invalid finalization plan: {exc}") from exc
    return ("ACTION: FINALIZE FORMULA TASK\n" f"Task: {plan.task_id}\n" f"Changed paths: {', '.join(plan.final_changed_paths)}\n"
            f"Diff size: {plan.final_diff_char_count}\nTests: {plan.final_test_result}\nGPT review: {plan.final_gpt_verdict}\n"
            f"Repairs: {plan.repair_count}\nCommit message: {plan.commit_message}\nPush target: {plan.push_remote}/{plan.push_branch}\n"
            "Approve commit + push? [y/N]")


def build_commander_agent(config: OrchestratorConfig) -> Any:
    from agents import Agent, ModelSettings, function_tool
    from openai.types.shared.reasoning import Reasoning

    @function_tool(name_override="inspect_project_state")
    def state() -> dict[str, Any]:
        """Inspect current Formula repository state (read-only)."""
        return inspect_project_state(config)

    @function_tool(name_override="prepare_formula_task")
    def prepare(task_id: str, title: str, objective: str, acceptance_criteria: list[str], allowed_paths: list[str] = [], allowed_roots: list[str] = [], repair_limit: int = 2, commit_message: str | None = None) -> dict[str, Any]:
        """Validate and prepare one bounded Formula task; does not execute it."""
        return prepare_formula_task(config, task_id, title, objective, acceptance_criteria, allowed_paths, allowed_roots, repair_limit, commit_message)

    @function_tool(name_override="run_prepared_task", needs_approval=True)
    def run(plan_path: str, approval_token: str) -> dict[str, Any]:
        """Run an exact prepared O5 plan after human approval."""
        return run_prepared_task(config, plan_path, approval_token)

    @function_tool(name_override="inspect_o5_run")
    def inspect_run(run_path: str) -> dict[str, Any]:
        """Inspect a known local O5 run record."""
        return inspect_o5_run(config, run_path)

    @function_tool(name_override="finalize_ready_task", needs_approval=True)
    def finalize(run_path: str, approval_token: str) -> dict[str, Any]:
        """Finalize one READY_FOR_HUMAN_REVIEW O5 run after human approval."""
        return finalize_ready_task(config, run_path, approval_token)

    return Agent(name="Formula Commander", instructions=INSTRUCTIONS, model=config.coordinator.model,
                 model_settings=ModelSettings(reasoning=Reasoning(effort=config.coordinator.reasoning_effort)),
                 tools=[state, prepare, run, inspect_run, finalize])


def _approval_details(config: OrchestratorConfig, item: Any) -> str:
    raw = getattr(item, "raw_item", item)
    arguments = getattr(raw, "arguments", "{}")
    try:
        args = json.loads(arguments) if isinstance(arguments, str) else arguments
    except json.JSONDecodeError as exc:
        raise ValueError("malformed approval arguments") from exc
    if item.tool_name == "run_prepared_task":
        return render_run_approval(config, args["plan_path"])
    if item.tool_name == "finalize_ready_task":
        return render_finalization_approval(config, args["run_path"])
    raise ValueError(f"unexpected approval tool: {item.tool_name}")


async def _run_turn(agent: Any, session: Any, prompt: str, config: OrchestratorConfig) -> Any:
    from agents import Runner
    result = await Runner.run(agent, prompt, session=session, max_turns=10)
    while result.interruptions:
        state = result.to_state()
        for item in result.interruptions:
            print(_approval_details(config, item))
            answer = input().strip().lower()
            if answer in {"y", "yes"}:
                state.approve(item)
            else:
                state.reject(item, rejection_message="Human rejected this action.")
        result = await Runner.run(agent, state, session=session, max_turns=10)
    return result


def _api_error_recovery(config: OrchestratorConfig) -> str:
    """Render only deterministic local state after an uncertain API outcome."""
    try:
        state = inspect_project_state(config)
    except Exception as exc:
        return f"Commander recovery inspection failed: {redact_secrets(str(exc))}"
    latest = state["latest_local_o5"]
    latest_text = json.dumps(latest, sort_keys=True) if latest is not None else "none"
    changed_paths = ", ".join(state["changed_paths"]) or "none"
    return ("Commander recovery state (read-only):\n"
            f"Branch: {state['branch']}\nHEAD: {state['head']}\nClean: {state['clean']}\n"
            f"Changed paths: {changed_paths}\nLatest local O5: {latest_text}\n"
            "Do not retry any approved action until this state has been checked.")


def run_commander(config: OrchestratorConfig) -> int:
    require_authentication()
    from agents import SQLiteSession
    agent = build_commander_agent(config)
    db_path = config.run_log_directory / "commander" / "commander.sqlite"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    session = SQLiteSession("formula-main", db_path=str(db_path))
    print("Formula Commander")
    print(f"Model: {config.coordinator.model} / {config.coordinator.reasoning_effort}")
    print("Type 'exit' to quit.")
    try:
        while True:
            try:
                prompt = input("Formula Commander> ")
            except EOFError:
                break
            if prompt.strip().lower() in {"exit", "quit"}:
                break
            if not prompt.strip():
                continue
            try:
                result = asyncio.run(_run_turn(agent, session, prompt, config))
            except APIStatusError as exc:
                error = getattr(exc, "body", {}).get("error", {}) if isinstance(getattr(exc, "body", None), dict) else {}
                message = error.get("message") if isinstance(error, dict) else None
                detail = redact_secrets(str(message or "The OpenAI API rejected the request."))
                print(f"Commander API error ({getattr(exc, 'status_code', 'unknown')}): {detail}")
                print(_api_error_recovery(config))
                continue
            print(str(result.final_output or ""))
    except KeyboardInterrupt:
        print()
    return 0
