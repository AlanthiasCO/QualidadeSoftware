from __future__ import annotations

import numpy as np
import pandas as pd


def build_comparison_pairs(longitudinal: pd.DataFrame, high_quantile: float = 0.90, low_quantile: float = 0.50) -> pd.DataFrame:
    pairs = []
    for (project, language), g in longitudinal.groupby(["project_id", "language"]):
        eligible = g[g["snapshots"] > 1].copy()
        if len(eligible) < 4:
            continue
        hi_cut = eligible["h_median"].quantile(high_quantile)
        lo_cut = eligible["h_median"].quantile(low_quantile)
        high = eligible[eligible["h_median"] >= hi_cut].copy()
        low = eligible[eligible["h_median"] <= lo_cut].copy()
        if low.empty:
            continue
        for col in ["nloc_median", "first_year"]:
            sd = low[col].std(ddof=0) or 1.0
            low[f"z_{col}"] = (low[col] - low[col].mean()) / sd
            high[f"z_{col}"] = (high[col] - low[col].mean()) / sd
        used = set()
        for _, h in high.sort_values("h_median", ascending=False).iterrows():
            candidates = low[~low["file_id"].isin(used)].copy()
            if candidates.empty:
                break
            d = np.sqrt((candidates["z_nloc_median"] - h["z_nloc_median"])**2 + (candidates["z_first_year"] - h["z_first_year"])**2)
            idx = d.idxmin()
            c = candidates.loc[idx]
            used.add(c["file_id"])
            pairs.append({
                "project_id": project,
                "language": language,
                "high_file_id": h["file_id"],
                "high_h_median": h["h_median"],
                "control_file_id": c["file_id"],
                "control_h_median": c["h_median"],
                "distance": float(d.loc[idx]),
            })
    return pd.DataFrame(pairs)


def qualitative_template(pairs: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, r in pairs.iterrows():
        for role, file_col in [("high", "high_file_id"), ("control", "control_file_id")]:
            rows.append({
                "project_id": r["project_id"],
                "language": r.get("language", ""),
                "pair_role": role,
                "file_id": r[file_col],
                "artifact_type": "",
                "artifact_reference": "",
                "evidence_excerpt_or_summary": "",
                "context_notes": "",
                "reviewer_1_class": "",
                "reviewer_2_class": "",
                "agreement": "",
                "consensus_class": "",
            })
    return pd.DataFrame(rows)
