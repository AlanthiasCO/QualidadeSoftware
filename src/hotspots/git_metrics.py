from __future__ import annotations

from datetime import datetime
from pathlib import Path
import time
import pandas as pd
from pydriller import Repository

from .config import ProjectConfig
from .filtering import include_path
from .identity import IdentityCollisionError, UnionFind
from .static_metrics import list_files_at
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


def _snapshot_paths(
    cfg: ProjectConfig,
    snapshots: pd.DataFrame,
) -> dict[str, set[str]]:
    """Return filtered paths present in each snapshot, keyed deterministically."""
    result: dict[str, set[str]] = {}
    ordered = snapshots.sort_values(["year", "sha"], kind="mergesort")
    for row in ordered.itertuples(index=False):
        key = f"{int(row.year)}:{row.sha}"
        result[key] = {
            path
            for path in list_files_at(cfg.repo_path, str(row.sha))
            if include_path(path, cfg)
        }
    return result


def _path_snapshot_presence(
    snapshot_paths: dict[str, set[str]],
) -> dict[str, set[str]]:
    presence: dict[str, set[str]] = {}
    for snapshot, paths in sorted(snapshot_paths.items()):
        for path in sorted(paths):
            presence.setdefault(path, set()).add(snapshot)
    return presence


def _validate_canonical_snapshot_uniqueness(
    canonical: dict[str, str],
    snapshot_paths: dict[str, set[str]],
) -> None:
    for snapshot, paths in sorted(snapshot_paths.items()):
        seen: dict[str, str] = {}
        for path in sorted(paths):
            identity = canonical.get(path, path)
            previous = seen.get(identity)
            if previous is not None and previous != path:
                raise IdentityCollisionError(
                    "Reconstrução longitudinal ambígua no snapshot "
                    f"{snapshot}: {previous!r} e {path!r} receberam a mesma "
                    f"identidade canônica {identity!r}."
                )
            seen[identity] = path


def _reconstruct_longitudinal_identity(
    events: pd.DataFrame,
    snapshot_paths: dict[str, set[str]],
) -> dict[str, str]:
    """Build conservative identities, rejecting edges between coexisting paths."""
    presence = _path_snapshot_presence(snapshot_paths)
    event_paths: set[str] = set()
    for column in ("path", "old_path", "new_path"):
        if column in events.columns:
            event_paths.update(
                value
                for value in events[column].dropna()
                if isinstance(value, str) and value
            )
    all_paths = event_paths | set(presence)

    uf = UnionFind()
    component_snapshots: dict[str, set[str]] = {}
    for path in sorted(all_paths):
        root = uf.find(path)
        component_snapshots[root] = set(presence.get(path, set()))

    edges = events.copy()
    if not edges.empty:
        edges["_date"] = pd.to_datetime(edges["commit_date"], utc=True)
        for column in ("commit", "old_path", "new_path", "path"):
            if column not in edges.columns:
                edges[column] = ""
            edges[column] = edges[column].fillna("").astype(str)
        edges = edges.sort_values(
            ["_date", "commit", "old_path", "new_path", "path"],
            kind="mergesort",
        )

    for row in edges.itertuples(index=False):
        oldp = row.old_path
        newp = row.new_path
        if not oldp or not newp or oldp == newp:
            continue
        old_root = uf.find(oldp)
        new_root = uf.find(newp)
        if old_root == new_root:
            continue
        old_snapshots = component_snapshots.get(old_root, set())
        new_snapshots = component_snapshots.get(new_root, set())
        if old_snapshots & new_snapshots:
            continue

        merged_snapshots = old_snapshots | new_snapshots
        component_snapshots.pop(old_root, None)
        component_snapshots.pop(new_root, None)
        uf.union(old_root, new_root)
        component_snapshots[uf.find(old_root)] = merged_snapshots

    canonical = {path: uf.find(path) for path in sorted(all_paths)}
    _validate_canonical_snapshot_uniqueness(canonical, snapshot_paths)
    return canonical


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
    ev = (
        pd.concat(nonempty, ignore_index=True)
        if nonempty
        else pd.DataFrame(columns=EVENT_COLUMNS)
    )
    # PyDriller treats the ``since`` boundary as inclusive at second precision.
    # Consequently, a commit that closes one snapshot can also be returned for
    # the following window even though its start is advanced by one microsecond.
    # Keep the scientific windows unchanged and remove only identical events
    # repeated across adjacent checkpoints before aggregating churn.
    ev = ev.drop_duplicates(subset=EVENT_COLUMNS).reset_index(drop=True)
    ev["commit_date"] = pd.to_datetime(ev["commit_date"], utc=True)

    snapshot_paths = _snapshot_paths(cfg, snapshots)
    canonical = _reconstruct_longitudinal_identity(ev, snapshot_paths)
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
