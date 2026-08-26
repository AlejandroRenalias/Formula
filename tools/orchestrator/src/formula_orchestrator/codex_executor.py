"""Small boundary around the experimental OpenAI Agents SDK Codex tool."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import ModelConfig


@dataclass(frozen=True)
class CodexExecutionResult:
    success: bool
    response_text: str = ""
    thread_id: str | None = None
    usage: dict[str, Any] | None = None
    error: str | None = None


class CodexExecutor:
    """Execute exactly one bounded Codex task through the official SDK."""

    async def execute(
        self,
        repository_root: Path,
        task_text: str,
        model: ModelConfig,
        run_id: str,
    ) -> CodexExecutionResult:
        try:
            from agents import Agent, Runner
            from agents.extensions.experimental.codex import (
                ThreadOptions,
                TurnOptions,
                codex_tool,
            )
        except Exception as exc:  # SDK import/configuration failures are failures.
            return CodexExecutionResult(success=False, error=f"Agents SDK Codex integration unavailable: {exc}")

        del run_id  # The task text carries the safe, caller-assigned run context.
        thread_id: str | None = None
        usage: dict[str, Any] | None = None

        async def on_stream(payload: Any) -> None:
            nonlocal thread_id, usage
            event = payload.event
            if hasattr(event, "thread_id"):
                thread_id = str(event.thread_id)
            if hasattr(event, "usage") and event.usage is not None:
                usage = _safe_usage(event.usage)

        try:
            tool = codex_tool(
                sandbox_mode="workspace-write",
                working_directory=str(repository_root),
                default_thread_options=ThreadOptions(
                    model=model.model,
                    model_reasoning_effort="low",
                    approval_policy="never",
                    network_access_enabled=False,
                    web_search_enabled=False,
                ),
                default_turn_options=TurnOptions(idle_timeout_seconds=120),
                on_stream=on_stream,
            )
            agent = Agent(
                name="Formula O1 Codex Smoke",
                instructions="Use the codex tool exactly once to perform the supplied bounded smoke task, then summarize the result.",
                model=model.model,
                tools=[tool],
            )
            result = await Runner.run(agent, task_text, max_turns=2)
            response = str(result.final_output or "")
            return CodexExecutionResult(
                success=True,
                response_text=response,
                thread_id=thread_id,
                usage=usage,
            )
        except Exception as exc:
            return CodexExecutionResult(
                success=False,
                thread_id=thread_id,
                usage=usage,
                error=f"Codex execution failed: {exc}",
            )


def _safe_usage(value: Any) -> dict[str, Any]:
    """Keep usage machine-readable without retaining arbitrary SDK objects."""
    if isinstance(value, dict):
        return {str(key): _safe_value(item) for key, item in value.items()}
    result: dict[str, Any] = {}
    for name in ("input_tokens", "output_tokens", "total_tokens"):
        if hasattr(value, name):
            result[name] = _safe_value(getattr(value, name))
    return result


def _safe_value(value: Any) -> Any:
    return value if isinstance(value, (str, int, float, bool, type(None))) else str(value)

