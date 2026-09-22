from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import pandas as pd

from .config import ProjectConfig
from .repository import resolve_freeze_sha
from .utils import run_git


def build_snapshots(cfg: ProjectConfig) -> pd.DataFrame:
    repo = cfg.repo_path
    freeze_sha = resolve_freeze_sha(cfg)
    freeze_date = run_git(repo, "show", "-s", "--format=%cI", freeze_sha)
    freeze_dt = datetime.fromisoformat(freeze_date.replace("Z", "+00:00"))

    rows = []
    for year in range(cfg.start_year, cfg.end_year + 1):
        if year > freeze_dt.year:
            break
        if year == freeze_dt.year:
            sha = freeze_sha
        else:
            before = f"{year}-12-31T23:59:59+00:00"
            try:
                sha = run_git(repo, "rev-list", "-1", f"--before={before}", freeze_sha)
            except Exception:
                sha = ""
        if not sha:
            continue
        date = run_git(repo, "show", "-s", "--format=%cI", sha)
        rows.append({"project_id": cfg.project_id, "year": year, "sha": sha, "snapshot_date": date})

    return pd.DataFrame(rows).drop_duplicates(subset=["sha"]).sort_values("year").reset_index(drop=True)
