from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time
import pandas as pd
from pydriller import Repository

from .config import ProjectConfig
from .filtering import include_path
from .identity import UnionFind
from .utils import stable_id, run_git, ensure_dir

EVENT_COLUMNS = ["commit", "commit_date", "path", "old_path", "new_path", "added", "deleted"]


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def _fmt_eta(seconds: float | None) -> str:
    if seconds is None or seconds < 0 or seconds != seconds:
        return "?"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"


def _commit_total(cfg: ProjectConfig, since: pd.Timestamp, to: pd.Timestamp) -> int:
    try:
        out = run_git(
            cfg.repo_path,
            "rev-list",
            "--count",
            f"--since={since.isoformat()}",
            f"--until={to.isoformat()}",
            cfg.branch,
        )
        return int(out.strip())
    except Exception:
        return 0


def _cache_file(cache_dir: Path, year: int, sha: str) -> Path:
    return cache_dir / f"events_{year}_{sha[:12]}.csv"


def _load_or_mine_window(
    cfg: ProjectConfig,
    year: int,
    sha: str,
    start: pd.Timestamp,
    end: pd.Timestamp,
    cache_dir: Path,
    resume: bool,
    global_done: int,
    global_total: int,
    started: float,
) -> tuple[pd.DataFrame, int]:
    cache_path = _cache_file(cache_dir, year, sha)
    if resume and cache_path.exists():
        ev = pd.read_csv(cache_path)
        if ev.empty:
            ev = pd.DataFrame(columns=EVENT_COLUMNS)
        print(f"[CACHE] stage=git year={year} file={cache_path}", flush=True)
        return ev, global_done

    total = _commit_total(cfg, start, end)
    events: list[dict] = []
    processed = 0
    last_report = time.monotonic()

    print(
        f"[PROGRESS] stage=git year={year} commits={global_done} total={global_total} "
        f"window_commits=0 window_total={total} pct={(global_done / global_total * 100.0 if global_total else 0.0):.2f} "
        f"rate=0.00 eta=? events=0",
        flush=True,
    )

    repo = Repository(
        str(cfg.repo_path),
        since=start.to_pydatetime(),
        to=end.to_pydatetime(),
        only_in_branch=cfg.branch,
        include_deleted_files=True,
    )

    for commit in repo.traverse_commits():
        processed += 1
        global_done += 1
        for m in commit.modified_files:
            oldp = (m.old_path or "").replace("\\", "/")
            newp = (m.new_path or "").replace("\\", "/")
            path = newp or oldp
            if not path or not include_path(path, cfg):
                continue
            events.append({
                "commit": commit.hash,
                "commit_date": commit.committer_date.isoformat(),
                "path": path,
                "old_path": oldp or None,
                "new_path": newp or None,
                "added": int(m.added_lines or 0),
                "deleted": int(m.deleted_lines or 0),
            })

        now = time.monotonic()
        if processed == 1 or processed % 100 == 0 or (now - last_report) >= 5:
            elapsed = max(now - started, 1e-9)
            rate = global_done / elapsed
            pct = global_done / global_total * 100.0 if global_total else 0.0
            eta = (global_total - global_done) / rate if global_total and rate > 0 else None
            print(
                f"[PROGRESS] stage=git year={year} commits={global_done} total={global_total} "
                f"window_commits={processed} window_total={total} pct={pct:.2f} "
                f"rate={rate:.2f} eta={_fmt_eta(eta)} events={len(events)}",
                flush=True,
            )
            last_report = now

    ev = pd.DataFrame(events, columns=EVENT_COLUMNS)
    ev.to_csv(cache_path, index=False)
    print(f"[CHECKPOINT] stage=git year={year} commits={processed} file={cache_path}", flush=True)
    return ev, global_done


def mine_git_metrics(
    cfg: ProjectConfig,
    snapshots: pd.DataFrame,
    cache_root: Path | None = None,
    resume: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Mine Nmod/churn with annual checkpoints.

    The scientific window remains (previous_snapshot, current_snapshot], except the
    first year which starts at Jan 1 of start_year. Checkpoints only change execution,
    not the events or aggregation rules.
    """
    if snapshots.empty:
        return pd.DataFrame(), pd.DataFrame()

    cache_dir = ensure_dir((cache_root or Path(".cache") / cfg.project_id) / "git")

    windows: list[tuple[int, str, pd.Timestamp, pd.Timestamp]] = []
    prev = pd.Timestamp(f"{cfg.start_year}-01-01T00:00:00Z")
    for _, snap in snapshots.iterrows():
        end = pd.to_datetime(snap["snapshot_date"], utc=True)
        year = int(snap["year"])
        sha = str(snap["sha"])
        windows.append((year, sha, prev, end))
        prev = end + pd.Timedelta(microseconds=1)

    totals = [_commit_total(cfg, start, end) for _, _, start, end in windows]
    global_total = sum(totals)
    global_done = 0
    started = time.monotonic()
    chunks: list[pd.DataFrame] = []

    for (year, sha, start, end), estimated in zip(windows, totals):
        cache_path = _cache_file(cache_dir, year, sha)
        if resume and cache_path.exists():
            # For ETA/progress, cached windows count as complete.
            global_done += estimated
        ev, actual_done = _load_or_mine_window(
            cfg, year, sha, start, end, cache_dir, resume,
            global_done - (estimated if resume and cache_path.exists() else 0),
            global_total, started,
        )
        if not (resume and cache_path.exists()):
            global_done = actual_done
        chunks.append(ev)

    nonempty = [x for x in chunks if not x.empty]
    if not nonempty:
        return pd.DataFrame(), pd.DataFrame()

    ev = pd.concat(nonempty, ignore_index=True)
    ev["commit_date"] = pd.to_datetime(ev["commit_date"], utc=True)

    # Reconstruct longitudinal identity globally, preserving baseline behavior.
    uf = UnionFind()
    for row in ev.itertuples(index=False):
        oldp = row.old_path if isinstance(row.old_path, str) else ""
        newp = row.new_path if isinstance(row.new_path, str) else ""
        if oldp and newp and oldp != newp:
            uf.union(oldp, newp)

    all_paths = set(ev["path"].dropna()) | set(ev["old_path"].dropna()) | set(ev["new_path"].dropna())
    canonical = {p: uf.find(p) for p in all_paths if isinstance(p, str) and p}
    ev["canonical_path"] = ev["path"].map(lambda p: canonical.get(p, p))
    ev["file_id"] = ev["canonical_path"].map(lambda p: stable_id(cfg.project_id, p))

    rows = []
    prev = pd.Timestamp(f"{cfg.start_year}-01-01T00:00:00Z")
    for _, snap in snapshots.iterrows():
        end = pd.to_datetime(snap["snapshot_date"], utc=True)
        window = ev[(ev["commit_date"] >= prev) & (ev["commit_date"] <= end)]
        if not window.empty:
            grouped = window.groupby(["file_id", "canonical_path"], as_index=False).agg(
                nmod=("commit", "nunique"),
                added=("added", "sum"),
                deleted=("deleted", "sum"),
            )
            grouped["churn"] = grouped["added"] + grouped["deleted"]
            grouped.insert(0, "year", int(snap["year"]))
            grouped.insert(0, "project_id", cfg.project_id)
            rows.append(grouped)
        prev = end + pd.Timedelta(microseconds=1)

    metrics = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if not metrics.empty:
        metrics = metrics.sort_values(["year", "canonical_path", "file_id"]).reset_index(drop=True)

    identity = pd.DataFrame([
        {"project_id": cfg.project_id, "path": p, "canonical_path": c, "file_id": stable_id(cfg.project_id, c)}
        for p, c in sorted(canonical.items())
    ])
    print(
        f"[PROGRESS] stage=git commits={global_total or global_done} total={global_total or global_done} "
        f"pct=100.00 rate=0.00 eta=00:00:00 events={len(ev)}",
        flush=True,
    )
    return metrics, identity
