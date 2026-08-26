import json
import subprocess
from pathlib import Path

import pytest

from formula_orchestrator.config import OrchestratorConfig
from formula_orchestrator.finalization import (
    FinalizationError,
    build_finalization_plan,
    capture_git_state,
    finalize_task,
    write_finalization_plan,
)
from formula_orchestrator.mutation import capture_baseline
from formula_orchestrator.scope import TaskScope
from .test_preflight import make_repo


def config_for(root):
    return OrchestratorConfig(repository_root=root, run_log_directory=root / "tools" / "orchestrator" / ".run-logs")


def git(root, *args, check=True):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=check)


def make_finalization_case(tmp_path, remote=True, message="Small tooling task"):
    root = make_repo(tmp_path)
    config = config_for(root)
    if remote:
        bare = tmp_path / "origin.git"
        subprocess.run(["git", "init", "--bare", "-q", str(bare)], check=True)
        git(root, "remote", "add", "origin", str(bare))
    (root / "src" / "placeholder.py").write_text("approved\n", encoding="utf-8")
    baseline = capture_baseline(root)
    state = capture_git_state(root, config.review_max_diff_chars)
    scope = TaskScope(root, allowed_paths=("src/placeholder.py",))
    plan = build_finalization_plan(
        task_id="task-one", o5_run_id="o5-run", o4_run_id="o4-run", prepared_plan_fingerprint="prepare-fingerprint",
        baseline_head=baseline.head_sha, branch=baseline.branch, repository_path=str(root), scope=scope, state=state,
        repair_count=1, final_test_result="PASS", final_gpt_verdict="PASS", commit_message=message, prepared_timestamp="now",
    )
    plan_path = write_finalization_plan(config, plan)
    run_path = config.run_log_directory / "o5-o5-run.json"
    run_path.write_text(json.dumps({
        "task_id": "task-one", "final_status": "READY_FOR_HUMAN_REVIEW", "finalization_plan_path": str(plan_path),
    }), encoding="utf-8")
    return root, config, plan, run_path


def test_finalization_requires_separate_token_and_does_not_stage(tmp_path):
    root, config, plan, run_path = make_finalization_case(tmp_path)
    with pytest.raises(FinalizationError) as error:
        finalize_task(run_path, "wrong-token", config)
    assert error.value.status == "APPROVAL_MISMATCH"
    assert not git(root, "diff", "--cached", "--name-only").stdout.strip()


def test_non_successful_run_is_not_finalizable(tmp_path):
    root, config, plan, run_path = make_finalization_case(tmp_path)
    data = json.loads(run_path.read_text(encoding="utf-8")); data["final_status"] = "TECHNICAL_FAILED: REVIEW_FAILED"
    run_path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(FinalizationError) as error:
        finalize_task(run_path, plan.finalization_token, config)
    assert error.value.status == "RUN_NOT_FINALIZABLE"
    assert not git(root, "diff", "--cached", "--name-only").stdout.strip()


def test_exact_approved_path_is_committed_and_pushed(tmp_path):
    root, config, plan, run_path = make_finalization_case(tmp_path)
    outcome = finalize_task(run_path, plan.finalization_token, config)
    assert outcome.status == "FINALIZED" and outcome.push_success and outcome.commit_sha
    assert git(root, "show", "--format=%s", "--no-patch").stdout.strip() == plan.commit_message
    assert git(root, "status", "--porcelain").stdout == ""
    assert git(root, "diff", "--cached", "--name-only").stdout == ""


def test_extra_changed_path_is_rejected_before_staging(tmp_path):
    root, config, plan, run_path = make_finalization_case(tmp_path)
    (root / "README.md").write_text("unapproved\n", encoding="utf-8")
    with pytest.raises(FinalizationError) as error:
        finalize_task(run_path, plan.finalization_token, config)
    assert error.value.status == "FINALIZATION_STALE"
    assert not git(root, "diff", "--cached", "--name-only").stdout.strip()


def test_changed_diff_and_existing_index_are_rejected(tmp_path):
    root, config, plan, run_path = make_finalization_case(tmp_path)
    (root / "src" / "placeholder.py").write_text("tampered\n", encoding="utf-8")
    with pytest.raises(FinalizationError) as error:
        finalize_task(run_path, plan.finalization_token, config)
    assert error.value.status == "FINALIZATION_STALE"
    git(root, "add", "src/placeholder.py")
    with pytest.raises(FinalizationError) as error:
        finalize_task(run_path, plan.finalization_token, config)
    assert error.value.status == "FINALIZATION_STALE"


def test_commit_failure_does_not_push_and_consumes_finalization(tmp_path):
    root, config, plan, run_path = make_finalization_case(tmp_path)
    hook = root / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
    hook.chmod(0o755)
    with pytest.raises(FinalizationError) as error:
        finalize_task(run_path, plan.finalization_token, config)
    assert error.value.status == "COMMIT_FAILED"
    assert not git(root, "diff", "--cached", "--name-only").stdout.strip()
    with pytest.raises(FinalizationError) as replay:
        finalize_task(run_path, plan.finalization_token, config)
    assert replay.value.status == "ALREADY_FINALIZED"


def test_push_failure_preserves_local_commit(tmp_path):
    root, config, plan, run_path = make_finalization_case(tmp_path, remote=False)
    git(root, "remote", "add", "origin", str(tmp_path / "missing.git"))
    with pytest.raises(FinalizationError) as error:
        finalize_task(run_path, plan.finalization_token, config)
    assert error.value.status == "PUSH_FAILED"
    assert git(root, "rev-parse", "HEAD").stdout.strip() != plan.baseline_head
    assert json.loads(run_path.read_text(encoding="utf-8"))["final_status"] == "PUSH_FAILED"


def test_whitespace_check_failure_does_not_commit(tmp_path):
    root, config, plan, run_path = make_finalization_case(tmp_path)
    (root / "src" / "placeholder.py").write_text("bad trailing  \n", encoding="utf-8")
    # Rebuild the approved plan for this exact (but invalid) patch.
    state = capture_git_state(root, config.review_max_diff_chars)
    plan = build_finalization_plan(
        task_id=plan.task_id, o5_run_id=plan.o5_run_id, o4_run_id=plan.o4_run_id, prepared_plan_fingerprint=plan.prepared_plan_fingerprint,
        baseline_head=plan.baseline_head, branch=plan.branch, repository_path=plan.repository_path, scope=TaskScope(root, allowed_paths=("src/placeholder.py",)), state=state,
        repair_count=plan.repair_count, final_test_result=plan.final_test_result, final_gpt_verdict=plan.final_gpt_verdict, commit_message=plan.commit_message, prepared_timestamp=plan.prepared_timestamp,
    )
    plan_path = write_finalization_plan(config, plan)
    run_data = json.loads(run_path.read_text(encoding="utf-8")); run_data["finalization_plan_path"] = str(plan_path); run_path.write_text(json.dumps(run_data), encoding="utf-8")
    with pytest.raises(FinalizationError) as error:
        finalize_task(run_path, plan.finalization_token, config)
    assert error.value.status == "STAGED_CHECK_FAILED"
    assert git(root, "rev-parse", "HEAD").stdout.strip() == plan.baseline_head
