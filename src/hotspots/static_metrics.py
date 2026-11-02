from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import multiprocessing
import os
import subprocess
import time
import lizard
import pandas as pd

from .config import ProjectConfig
from .filtering import include_path
from .identity import validate_snapshot_file_id_uniqueness
from .utils import run_git, stable_id, ensure_dir


def list_files_at(repo: Path, sha: str) -> list[str]:
    """Return all file paths present at *sha* without checking out the tree.

    This helper is intentionally unfiltered. The audit stage uses it to report
    the total number of files at the frozen revision, then applies include_path
    separately to compute the first-party subset.
    """
    p = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "-z", "--name-only", sha],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return [
        item.decode("utf-8", errors="replace").replace("\\", "/")
        for item in p.stdout.split(b"\x00")
        if item
    ]


def language_of(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else "unknown"
    return {"py": "Python", "java": "Java", "cs": "CSharp", "js": "JavaScript", "ts": "TypeScript", "tsx": "TypeScript", "jsx": "JavaScript", "cpp": "Cpp", "cc": "Cpp", "c": "C", "php": "PHP", "rb": "Ruby", "go": "Go", "rs": "Rust"}.get(ext, ext or "unknown")


def _fmt_eta(seconds: float | None) -> str:
    if seconds is None or seconds < 0 or seconds != seconds:
        return "?"
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{sec:02d}"


def _tree_blobs(repo: Path, sha: str, cfg: ProjectConfig) -> list[tuple[str, str]]:
    p = subprocess.run(
        ["git", "-C", str(repo), "ls-tree", "-r", "-z", "--full-tree", sha],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    jobs: list[tuple[str, str]] = []
    for item in p.stdout.split(b"\x00"):
        if not item:
            continue
        meta, path_b = item.split(b"\t", 1)
        parts = meta.split()
        if len(parts) < 3:
            continue
        obj = parts[2].decode("ascii", errors="replace")
        path = path_b.decode("utf-8", errors="replace").replace("\\", "/")
        if include_path(path, cfg):
            jobs.append((path, obj))
    return jobs


def _cat_blobs(repo: Path, object_ids: list[str]):
    """Yield (object_id, bytes) using one persistent git cat-file process."""
    proc = subprocess.Popen(
        ["git", "-C", str(repo), "cat-file", "--batch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    assert proc.stdin is not None and proc.stdout is not None
    try:
        # Interleave request/response to avoid filling the stdout pipe on large repos.
        for oid in object_ids:
            proc.stdin.write((oid + "\n").encode("ascii"))
            proc.stdin.flush()
            header = proc.stdout.readline()
            if not header:
                raise RuntimeError("git cat-file terminou antes do esperado")
            h = header.decode("utf-8", errors="replace").strip().split()
            if len(h) >= 2 and h[1] == "missing":
                yield oid, None
                continue
            if len(h) < 3:
                raise RuntimeError(f"cabecalho inesperado do git cat-file: {header!r}")
            size = int(h[2])
            data = proc.stdout.read(size)
            proc.stdout.read(1)  # newline after object
            yield oid, data
    finally:
        if proc.stdin and not proc.stdin.closed:
            try:
                proc.stdin.close()
            except Exception:
                pass
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        if proc.stdout and not proc.stdout.closed:
            proc.stdout.close()


def _analyze_job(job: tuple[str, str, str, str, int]) -> dict | None:
    project_id, path, source, file_id, year = job
    try:
        info = lizard.analyze_file.analyze_source_code(path, source)
        ccn = sum(int(fn.cyclomatic_complexity) for fn in info.function_list)
        return {
            "project_id": project_id,
            "year": year,
            "path": path,
            "language": language_of(path),
            "file_id": file_id,
            "nloc": int(info.nloc),
            "ccn": ccn,
        }
    except Exception:
        return None


def _create_executor(workers: int) -> ProcessPoolExecutor | None:
    """Use spawn so workers never inherit the persistent git cat-file pipes."""
    if workers <= 1:
        return None
    return ProcessPoolExecutor(
        max_workers=workers,
        mp_context=multiprocessing.get_context("spawn"),
    )


def _snapshot_cache(cache_dir: Path, year: int, sha: str) -> Path:
    return cache_dir / f"static_{year}_{sha[:12]}.csv"


def _extract_one_snapshot(
    cfg: ProjectConfig,
    year: int,
    sha: str,
    path_to_id: dict[str, str],
    workers: int,
    cache_dir: Path,
    resume: bool,
    overall_done: int,
    grand_total: int,
    started: float,
) -> tuple[pd.DataFrame, int]:
    cache_path = _snapshot_cache(cache_dir, year, sha)
    if resume and cache_path.exists():
        df = pd.read_csv(cache_path)
        print(f"[CACHE] stage=static year={year} file={cache_path}", flush=True)
        return df, overall_done

    tree = _tree_blobs(cfg.repo_path, sha, cfg)
    year_total = len(tree)
    if year_total == 0:
        df = pd.DataFrame(columns=["project_id", "year", "sha", "path", "language", "file_id", "nloc", "ccn"])
        df.to_csv(cache_path, index=False)
        return df, overall_done

    by_oid: dict[str, list[str]] = {}
    for path, oid in tree:
        by_oid.setdefault(oid, []).append(path)

    rows: list[dict] = []
    year_done = 0
    last_report = time.monotonic()

    def handle(result):
        nonlocal year_done, overall_done, last_report
        year_done += 1
        overall_done += 1
        if result is not None:
            result["sha"] = sha
            rows.append(result)
        now = time.monotonic()
        if overall_done == 1 or overall_done % 250 == 0 or (now - last_report) >= 5:
            elapsed = max(now - started, 1e-9)
            rate = overall_done / elapsed
            pct = overall_done / grand_total * 100.0 if grand_total else 100.0
            eta = (grand_total - overall_done) / rate if rate > 0 else None
            ypct = year_done / year_total * 100.0 if year_total else 100.0
            print(
                f"[PROGRESS] stage=static year={year} files={overall_done} total={grand_total} "
                f"pct={pct:.2f} rate={rate:.2f} eta={_fmt_eta(eta)} "
                f"year_files={year_done} year_total={year_total} year_pct={ypct:.2f} workers={workers}",
                flush=True,
            )
            last_report = now

    # Keep only a small batch of source texts in memory at once. This is important
    # for very large snapshots such as Novo SGP.
    batch: list[tuple[str, str, str, str, int]] = []
    executor = _create_executor(workers)
    try:
        for oid, blob in _cat_blobs(cfg.repo_path, list(by_oid)):
            if blob is None:
                continue
            source = blob.decode("utf-8", errors="replace")
            for path in by_oid[oid]:
                file_id = path_to_id.get(path) or stable_id(cfg.project_id, path)
                batch.append((cfg.project_id, path, source, file_id, year))
                if len(batch) >= 256:
                    if executor is None:
                        for job in batch:
                            handle(_analyze_job(job))
                    else:
                        for result in executor.map(_analyze_job, batch, chunksize=32):
                            handle(result)
                    batch.clear()

        if batch:
            if executor is None:
                for job in batch:
                    handle(_analyze_job(job))
            else:
                for result in executor.map(_analyze_job, batch, chunksize=32):
                    handle(result)
    finally:
        if executor is not None:
            executor.shutdown(wait=True)

    df = pd.DataFrame(rows)
    if not df.empty:
        df = df[["project_id", "year", "sha", "path", "language", "file_id", "nloc", "ccn"]]
        df = df.sort_values(["path", "file_id"]).reset_index(drop=True)
    df.to_csv(cache_path, index=False)
    print(f"[CHECKPOINT] stage=static year={year} files={year_done} file={cache_path}", flush=True)
    return df, overall_done


def extract_static_metrics(
    cfg: ProjectConfig,
    snapshots: pd.DataFrame,
    identity: pd.DataFrame | None = None,
    workers: int | None = None,
    cache_root: Path | None = None,
    resume: bool = True,
) -> pd.DataFrame:
    path_to_id = {}
    if identity is not None and not identity.empty:
        path_to_id = dict(zip(identity["path"], identity["file_id"]))

    workers = workers or max(1, min(4, (os.cpu_count() or 2) - 1))
    cache_dir = ensure_dir((cache_root or Path(".cache") / cfg.project_id) / "static")

    snapshot_meta = []
    grand_total = 0
    for _, snap in snapshots.iterrows():
        year = int(snap["year"])
        sha = str(snap["sha"])
        cache_path = _snapshot_cache(cache_dir, year, sha)
        # ls-tree is cheap and gives attempted files, including any that Lizard may skip.
        count = len(_tree_blobs(cfg.repo_path, sha, cfg))
        snapshot_meta.append((year, sha, count, cache_path.exists()))
        grand_total += count

    rows = []
    overall_done = 0
    started = time.monotonic()
    print(f"[PROGRESS] stage=static files=0 total={grand_total} pct=0.00 rate=0.00 eta=? workers={workers}", flush=True)

    for year, sha, count, cached in snapshot_meta:
        if resume and cached:
            overall_done += count
        df, actual_done = _extract_one_snapshot(
            cfg, year, sha, path_to_id, workers, cache_dir, resume,
            overall_done - (count if resume and cached else 0), grand_total, started,
        )
        if not (resume and cached):
            overall_done = actual_done
        rows.append(df)

    result = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if not result.empty:
        result = result.sort_values(["year", "path", "file_id"]).reset_index(drop=True)
        validate_snapshot_file_id_uniqueness(result, "métricas estáticas")
    print(
        f"[PROGRESS] stage=static files={grand_total} total={grand_total} pct=100.00 "
        f"rate=0.00 eta=00:00:00 workers={workers}",
        flush=True,
    )
    return result
