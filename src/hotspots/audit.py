from __future__ import annotations

import pandas as pd
from .config import ProjectConfig
from .repository import resolve_freeze_sha
from .filtering import include_path
from .static_metrics import list_files_at
from .utils import run_git


def audit_project(cfg: ProjectConfig) -> pd.DataFrame:
    sha = resolve_freeze_sha(cfg)
    freeze_date = run_git(cfg.repo_path, "show", "-s", "--format=%cI", sha)
    start = f"{cfg.start_year}-01-01T00:00:00"
    commits = run_git(cfg.repo_path, "rev-list", "--count", f"--since={start}", sha)
    authors_text = run_git(cfg.repo_path, "log", f"--since={start}", "--format=%aN", sha)
    authors = len({a.strip() for a in authors_text.splitlines() if a.strip()})
    all_files = list_files_at(cfg.repo_path, sha)
    included = [p for p in all_files if include_path(p, cfg)]
    pct = (100.0 * len(included) / len(all_files)) if all_files else 0.0
    return pd.DataFrame([{
        "project_id": cfg.project_id,
        "name": cfg.name,
        "repo_url": cfg.repo_url,
        "branch": cfg.branch,
        "freeze_sha": sha,
        "freeze_date": freeze_date,
        "commits_since_start_year": int(commits or 0),
        "authors_since_start_year": authors,
        "files_at_freeze": len(all_files),
        "included_first_party_files_at_freeze": len(included),
        "included_file_pct": pct,
        "extensions": ";".join(cfg.extensions),
        "exclude_paths": ";".join(cfg.exclude_paths),
    }])
