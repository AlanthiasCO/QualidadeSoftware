from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import yaml


@dataclass
class ProjectConfig:
    project_id: str
    name: str
    repo_url: str
    local_path: str
    branch: str
    freeze_sha: str | None = None
    start_year: int = 2020
    end_year: int = 2026
    extensions: list[str] = field(default_factory=list)
    exclude_paths: list[str] = field(default_factory=list)
    exclude_tests: bool = True
    test_markers: list[str] = field(default_factory=lambda: ["test", "tests", "teste", "testes", "spec", "specs"])
    exclude_migrations: bool = False

    @property
    def repo_path(self) -> Path:
        return Path(self.local_path)


def load_config(path: str | Path) -> ProjectConfig:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return ProjectConfig(**data)
