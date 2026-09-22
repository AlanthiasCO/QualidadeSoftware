from __future__ import annotations

import pandas as pd


def build_master(git_metrics: pd.DataFrame, static_metrics: pd.DataFrame) -> pd.DataFrame:
    if static_metrics.empty:
        return static_metrics.copy()
    gm = git_metrics.copy()
    if gm.empty:
        out = static_metrics.copy()
        out[["nmod", "added", "deleted", "churn"]] = 0
        return out
    keep = ["project_id", "year", "file_id", "nmod", "added", "deleted", "churn"]
    out = static_metrics.merge(gm[keep], on=["project_id", "year", "file_id"], how="left")
    for col in ["nmod", "added", "deleted", "churn"]:
        out[col] = out[col].fillna(0).astype(int)
    return out


def add_hotspot_score(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return out
    group = ["project_id", "language", "year"]
    out["r_nmod"] = out.groupby(group)["nmod"].rank(method="average", pct=True)
    out["r_ccn"] = out.groupby(group)["ccn"].rank(method="average", pct=True)
    out["h"] = out[["r_nmod", "r_ccn"]].min(axis=1)
    out["h_geom"] = (out["r_nmod"] * out["r_ccn"]) ** 0.5
    return out
