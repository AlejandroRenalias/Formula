from pathlib import Path

from formula_orchestrator.cli import main
from .test_preflight import make_repo


def test_cli_check_success(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("FORMULA_REPOSITORY_ROOT", str(make_repo(tmp_path)))
    assert main(["check"]) == 0
    assert "preflight passed" in capsys.readouterr().out


def test_cli_check_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("FORMULA_REPOSITORY_ROOT", str(tmp_path / "missing"))
    assert main(["check"]) == 1
    assert "preflight failed" in capsys.readouterr().out

