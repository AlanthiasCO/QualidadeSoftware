from __future__ import annotations

import os
import subprocess
from pathlib import Path
from .config import ProjectConfig
from .utils import ensure_dir, run_git


def _git_env() -> dict[str, str]:
    env = os.environ.copy()
    return env


def _enable_long_paths(repo: Path) -> None:
    """Enable long-path handling for a managed Git worktree."""
    if (repo / ".git").exists():
        subprocess.run(
            ["git", "-C", str(repo), "config", "core.longpaths", "true"],
            check=False,
            env=_git_env(),
        )


def clone_or_update(cfg: ProjectConfig) -> Path:
    repo = cfg.repo_path
    if not repo.exists():
        ensure_dir(repo.parent)
        # -c applies before checkout and avoids Windows MAX_PATH failures in
        # repositories containing deeply nested source paths.
        subprocess.run(
            [
                "git", "-c", "core.longpaths=true", "clone",
                "--branch", cfg.branch, cfg.repo_url, str(repo),
            ],
            check=True,
            env=_git_env(),
        )
        _enable_long_paths(repo)
    else:
        _enable_long_paths(repo)
        run_git(repo, "fetch", "--all", "--tags", "--prune")
    return repo


def resolve_freeze_sha(cfg: ProjectConfig) -> str:
    repo = cfg.repo_path
    if cfg.freeze_sha:
        return run_git(repo, "rev-parse", cfg.freeze_sha)
    return run_git(repo, "rev-parse", f"origin/{cfg.branch}" if _has_ref(repo, f"origin/{cfg.branch}") else cfg.branch)


def _has_ref(repo: Path, ref: str) -> bool:
    p = subprocess.run(["git", "-C", str(repo), "show-ref", "--verify", "--quiet", f"refs/remotes/{ref}" if ref.startswith("origin/") else f"refs/heads/{ref}"])
    return p.returncode == 0
