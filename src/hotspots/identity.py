from __future__ import annotations

import pandas as pd

IDENTITY_COLUMNS = ["project_id", "path", "canonical_path", "file_id"]


class UnionFind:
    def __init__(self) -> None:
        self.parent: dict[str, str] = {}

    def find(self, x: str) -> str:
        if x not in self.parent:
            self.parent[x] = x
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            canonical = min(ra, rb)
            other = rb if canonical == ra else ra
            self.parent[other] = canonical


def complete_identity_map(
    identity: pd.DataFrame | None,
    static_metrics: pd.DataFrame | None,
) -> pd.DataFrame:
    """Add snapshot-only paths without changing identities reconstructed from Git."""

    if identity is None or identity.empty:
        base = pd.DataFrame(columns=IDENTITY_COLUMNS)
    else:
        base = identity[IDENTITY_COLUMNS].copy()

    if static_metrics is None or static_metrics.empty:
        return base.sort_values(["path", "file_id"]).reset_index(drop=True)

    snapshot = static_metrics[
        ["project_id", "path", "file_id"]
    ].drop_duplicates().copy()

    canonical_by_path = dict(zip(base["path"], base["canonical_path"]))
    snapshot["canonical_path"] = snapshot["path"].map(
        lambda path: canonical_by_path.get(path, path)
    )
    snapshot = snapshot[IDENTITY_COLUMNS]

    completed = pd.concat([base, snapshot], ignore_index=True)
    completed = completed.drop_duplicates(
        subset=["project_id", "path"],
        keep="first",
    )
    return completed.sort_values(["path", "file_id"]).reset_index(drop=True)
