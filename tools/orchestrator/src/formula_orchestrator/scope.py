"""Typed path scope for bounded Codex mutations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TaskScope:
    repository_root: Path
    allowed_paths: tuple[str, ...] = ()
    allowed_roots: tuple[str, ...] = ()
    forbidden_paths: tuple[str, ...] = (".git", ".env", ".env.*", ".env.example", ".gitignore", "pyproject.toml", "uv.lock", "tools/orchestrator/src", "tools/orchestrator/tests", "tools/orchestrator/pyproject.toml", "tools/orchestrator/uv.lock", "tools/orchestrator/.env.example")

    def __post_init__(self) -> None:
        object.__setattr__(self, "repository_root", Path(self.repository_root).resolve())

    def allows(self, path: str | Path) -> bool:
        relative = Path(path).as_posix().lstrip("./")
        if self._matches(relative, self.forbidden_paths):
            return False
        return self._matches(relative, self.allowed_paths, exact=True) or self._matches(relative, self.allowed_roots)

    def violations(self, paths: tuple[str, ...] | list[str]) -> tuple[str, ...]:
        return tuple(path for path in paths if not self.allows(path))

    @staticmethod
    def _matches(path: str, patterns: tuple[str, ...], exact: bool = False) -> bool:
        for pattern in patterns:
            normalized = Path(pattern).as_posix().strip("/")
            if normalized.endswith(".*"):
                prefix = normalized[:-2]
                if path == prefix or path.startswith(prefix + "."):
                    return True
                continue
            if exact and path == normalized:
                return True
            if not exact and (path == normalized or path.startswith(normalized + "/")):
                return True
        return False
