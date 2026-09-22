from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Iterable


def run_git(repo: Path, *args: str) -> str:
    p = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return p.stdout.strip()


def stable_id(project: str, canonical_path: str) -> str:
    raw = f"{project}:{canonical_path}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:16]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def is_excluded(path: str, excluded_prefixes: Iterable[str]) -> bool:
    norm = path.replace("\\", "/").lstrip("./")
    return any(norm == p.rstrip("/") or norm.startswith(p.rstrip("/") + "/") for p in excluded_prefixes)
