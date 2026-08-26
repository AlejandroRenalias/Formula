import pytest
from pydantic import ValidationError

from formula_orchestrator.reviewer import (
    FindingSeverity,
    ReviewContractError,
    ReviewDecision,
    ReviewFinding,
    ReviewVerdict,
    validate_review_decision,
)


def finding():
    return {
        "finding_id": "F-1",
        "severity": "IMPORTANT",
        "title": "Missing requirement",
        "description": "The requested behavior is absent.",
        "path": "src/example.py",
        "line": "10",
        "evidence": "The diff does not add the required behavior.",
        "required_fix": "Implement the missing behavior and add coverage.",
    }


def test_structured_pass_is_accepted():
    decision = validate_review_decision({"verdict": "PASS", "summary": "All supplied requirements are satisfied.", "findings": []})
    assert decision.verdict is ReviewVerdict.PASS


def test_structured_fix_requires_actionable_finding():
    decision = validate_review_decision({"verdict": "FIX", "summary": "A required change remains.", "findings": [finding()]})
    assert decision.verdict is ReviewVerdict.FIX
    assert decision.findings[0].severity is FindingSeverity.IMPORTANT


def test_invalid_fix_is_rejected():
    with pytest.raises(ReviewContractError):
        validate_review_decision({"verdict": "FIX", "summary": "Needs work.", "findings": []})


def test_pass_with_finding_is_rejected():
    with pytest.raises(ReviewContractError):
        validate_review_decision({"verdict": "PASS", "summary": "Mostly good.", "findings": [finding()]})


def test_unsupported_verdict_is_rejected():
    with pytest.raises(ReviewContractError):
        validate_review_decision({"verdict": "MAYBE", "summary": "Unclear.", "findings": []})


def test_extra_finding_fields_are_rejected():
    invalid = finding(); invalid["secret"] = "should not be accepted"
    with pytest.raises(ReviewContractError):
        validate_review_decision({"verdict": "FIX", "summary": "Needs work.", "findings": [invalid]})
