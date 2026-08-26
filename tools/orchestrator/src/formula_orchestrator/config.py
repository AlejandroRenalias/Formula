"""Typed, credential-free configuration for the orchestrator bootstrap."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from pathlib import Path

DEFAULT_TEST_COMMAND = "uv run --with pytest python -m pytest tests/ -q"


def discover_repository_root(start: Path | None = None) -> Path:
    """Find the nearest Formula checkout by looking for its project markers."""
    current = (start or Path(__file__)).resolve()
    if current.is_file():
        current = current.parent
    for candidate in (current, *current.parents):
        # The package itself has the same generic markers as Formula; skip it
        # when discovery is running from an installed/in-repository package.
        if (candidate / "src" / "formula_orchestrator").is_dir():
            continue
        if (candidate / "pyproject.toml").is_file() and (candidate / "src").is_dir() and (candidate / "tests").is_dir():
            return candidate
    raise FileNotFoundError("Could not discover a Formula repository root from the package location")


@dataclass(frozen=True)
class ModelConfig:
    """Non-secret model selection; credentials remain in the process environment."""

    model: str = "gpt-5.4"
    provider: str = "openai"


@dataclass(frozen=True)
class OrchestratorConfig:
    repository_root: Path = field(default_factory=discover_repository_root)
    coordinator: ModelConfig = field(default_factory=ModelConfig)
    codex: ModelConfig = field(default_factory=lambda: ModelConfig(model="gpt-5.4"))
    max_repair_loops: int = 2
    test_command: str = DEFAULT_TEST_COMMAND
    run_log_directory: Path | None = None

    def __post_init__(self) -> None:
        root = Path(self.repository_root).expanduser().resolve()
        object.__setattr__(self, "repository_root", root)
        if self.run_log_directory is None:
            object.__setattr__(self, "run_log_directory", root / "tools" / "orchestrator" / ".run-logs")
        else:
            object.__setattr__(self, "run_log_directory", Path(self.run_log_directory).expanduser().resolve())
        if self.max_repair_loops < 0:
            raise ValueError("max_repair_loops must be non-negative")
        if not self.coordinator.model.strip() or not self.codex.model.strip():
            raise ValueError("coordinator and codex model names must be non-empty")
        if not self.test_command.strip():
            raise ValueError("test_command must be non-empty")
        try:
            self.run_log_directory.relative_to(root)
        except ValueError as exc:
            raise ValueError("run_log_directory must remain inside the Formula repository") from exc

    @classmethod
    def from_environment(cls) -> "OrchestratorConfig":
        root_value = os.environ.get("FORMULA_REPOSITORY_ROOT")
        return cls(repository_root=Path(root_value) if root_value else discover_repository_root())

    def to_dict(self) -> dict[str, object]:
        """Serialize only safe settings; no credential fields are modeled or emitted."""
        data = asdict(self)
        data["repository_root"] = str(self.repository_root)
        data["run_log_directory"] = str(self.run_log_directory)
        return data
