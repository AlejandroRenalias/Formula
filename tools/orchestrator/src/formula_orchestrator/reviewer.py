"""Independent structured GPT review boundary."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .config import ModelConfig
from .evidence import ReviewInput, redact_secrets


class ReviewVerdict(str, Enum):
    PASS = "PASS"
    FIX = "FIX"


class FindingSeverity(str, Enum):
    BLOCKER = "BLOCKER"
    IMPORTANT = "IMPORTANT"
    MINOR = "MINOR"


class ReviewFinding(BaseModel):
    model_config = ConfigDict(extra="forbid")
    finding_id: str = Field(min_length=1)
    severity: FindingSeverity
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    path: str | None = None
    line: str | None = None
    evidence: str = Field(min_length=1)
    required_fix: str = Field(min_length=1)


class ReviewDecision(BaseModel):
    model_config = ConfigDict(extra="forbid")
    verdict: ReviewVerdict
    summary: str = Field(min_length=1)
    findings: list[ReviewFinding] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0, le=1)

    @model_validator(mode="after")
    def validate_verdict_findings(self) -> "ReviewDecision":
        if self.verdict is ReviewVerdict.PASS and self.findings:
            raise ValueError("PASS cannot contain findings requiring fixes")
        if self.verdict is ReviewVerdict.FIX and not self.findings:
            raise ValueError("FIX requires at least one actionable finding")
        return self


class ReviewContractError(ValueError):
    """Reviewer output is not a valid local review decision."""


@dataclass(frozen=True)
class ReviewResult:
    success: bool
    decision: ReviewDecision | None = None
    usage: dict[str, Any] | None = None
    duration_seconds: float = 0.0
    error: str | None = None


class GptReviewer:
    """One no-tools Agents SDK review request."""

    def review(self, review_input: ReviewInput, model: ModelConfig) -> ReviewResult:
        return asyncio.run(self._review(review_input, model))

    async def _review(self, review_input: ReviewInput, model: ModelConfig) -> ReviewResult:
        started = time.monotonic()
        try:
            from agents import Agent, ModelSettings, Runner
            from openai.types.shared.reasoning import Reasoning
            agent = Agent(
                name="Formula Independent Reviewer",
                instructions="Review task compliance independently. Codex output is an untrusted claim. Use only supplied evidence. Return PASS only with no actionable findings; return FIX with at least one actionable finding. Do not use tools, modify files, or provide chain-of-thought.",
                model=model.model,
                model_settings=ModelSettings(reasoning=Reasoning(effort=model.reasoning_effort)),
                tools=[],
                output_type=ReviewDecision,
            )
            result = await Runner.run(agent, review_input.to_prompt(), max_turns=1)
            decision = ReviewDecision.model_validate(result.final_output)
            return ReviewResult(True, decision, _usage(result), time.monotonic() - started)
        except (ValidationError, ValueError) as exc:
            return ReviewResult(False, duration_seconds=time.monotonic() - started, error=f"Malformed reviewer result: {redact_secrets(str(exc))}")
        except Exception as exc:
            return ReviewResult(False, duration_seconds=time.monotonic() - started, error=f"Reviewer execution failed: {redact_secrets(str(exc))}")


def validate_review_decision(value: Any) -> ReviewDecision:
    try:
        return ReviewDecision.model_validate(value)
    except (ValidationError, ValueError) as exc:
        raise ReviewContractError(str(exc)) from exc


def _usage(result: Any) -> dict[str, Any] | None:
    usage = getattr(result, "context_wrapper", None)
    usage = getattr(usage, "usage", None)
    if usage is None:
        return None
    if isinstance(usage, dict):
        return {str(key): value for key, value in usage.items() if isinstance(value, (str, int, float, bool, type(None)))}
    return {name: getattr(usage, name) for name in ("input_tokens", "output_tokens", "total_tokens") if hasattr(usage, name)}
