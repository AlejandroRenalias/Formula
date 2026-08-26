from pathlib import Path

from formula_orchestrator.config import DEFAULT_TEST_COMMAND, OrchestratorConfig, discover_repository_root


def test_repository_root_detection_from_nested_path(tmp_path: Path) -> None:
    root = tmp_path / "formula"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / "pyproject.toml").write_text("[project]\nname='formula'\n", encoding="utf-8")
    assert discover_repository_root(root / "src") == root.resolve()


def test_defaults() -> None:
    config = OrchestratorConfig(repository_root=Path.cwd())
    assert config.max_repair_loops == 2
    assert config.test_command == DEFAULT_TEST_COMMAND


def test_serialization_contains_no_credentials(tmp_path: Path) -> None:
    config = OrchestratorConfig(repository_root=tmp_path)
    serialized = repr(config.to_dict())
    assert "OPENAI_API_KEY" not in serialized
    assert "sk-" not in serialized

