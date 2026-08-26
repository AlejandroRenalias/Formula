import subprocess
from pathlib import Path

import pytest

from formula_orchestrator.config import OrchestratorConfig
from formula_orchestrator.preflight import PreflightError, run_preflight


def make_repo(tmp_path: Path) -> Path:
    root = tmp_path / "formula"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='formula'\n", encoding="utf-8")
    (root / ".gitignore").write_text("tools/orchestrator/.run-logs/\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=root, check=True)
    (root / "src" / "placeholder.py").write_text("", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(["git", "commit", "-qm", "initial"], cwd=root, check=True)
    return root


def test_clean_working_tree_accepted(tmp_path: Path) -> None:
    report = run_preflight(OrchestratorConfig(repository_root=make_repo(tmp_path)))
    assert report.working_tree_clean is True


def test_dirty_working_tree_rejected(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    (root / "dirty.txt").write_text("change", encoding="utf-8")
    with pytest.raises(PreflightError, match="dirty"):
        run_preflight(OrchestratorConfig(repository_root=root))


def test_missing_repository_rejected(tmp_path: Path) -> None:
    with pytest.raises(PreflightError, match="does not exist"):
        run_preflight(OrchestratorConfig(repository_root=tmp_path / "missing"))


def test_non_git_repository_rejected(tmp_path: Path) -> None:
    root = tmp_path / "formula"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    with pytest.raises(PreflightError, match="not a Git repository"):
        run_preflight(OrchestratorConfig(repository_root=root))
