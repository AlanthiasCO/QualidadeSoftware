from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


def analyze_rq3(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    longitudinal = df.groupby(["project_id", "language", "file_id"], as_index=False).agg(
        snapshots=("year", "nunique"),
        first_year=("year", "min"),
        last_year=("year", "max"),
        h_median=("h", "median"),
        h_iqr=("h", lambda x: float(np.percentile(x, 75) - np.percentile(x, 25))),
        h_min=("h", "min"),
        h_max=("h", "max"),
        nloc_median=("nloc", "median"),
    )

    stability = []
    for project, g in df.groupby("project_id"):
        years = sorted(g["year"].unique())
        for a, b in zip(years, years[1:]):
            ga = g[g["year"] == a][["file_id", "h"]].rename(columns={"h": "h_a"})
            gb = g[g["year"] == b][["file_id", "h"]].rename(columns={"h": "h_b"})
            m = ga.merge(gb, on="file_id")
            rho, p = (np.nan, np.nan) if len(m) < 3 else spearmanr(m["h_a"], m["h_b"])
            stability.append({"project_id": project, "year_a": a, "year_b": b, "shared_files": len(m), "rank_spearman": rho, "p_value": p})
    return longitudinal, pd.DataFrame(stability)
