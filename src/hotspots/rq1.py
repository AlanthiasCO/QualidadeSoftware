from __future__ import annotations

import numpy as np
import pandas as pd


def gini(values) -> float:
    x = np.asarray(values, dtype=float)
    x = x[np.isfinite(x)]
    if x.size == 0 or np.allclose(x, 0):
        return 0.0
    x = np.sort(np.maximum(x, 0))
    n = x.size
    return float((2 * np.sum((np.arange(1, n + 1)) * x) / (n * np.sum(x))) - (n + 1) / n)


def lorenz(values) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(values, dtype=float)
    x = np.maximum(x[np.isfinite(x)], 0)
    if x.size == 0:
        return np.array([0.0, 1.0]), np.array([0.0, 1.0])
    x = np.sort(x)
    cum = np.cumsum(x)
    pop = np.arange(1, len(x) + 1) / len(x)
    if cum[-1] == 0:
        share = pop.copy()
    else:
        share = cum / cum[-1]
    return np.r_[0.0, pop], np.r_[0.0, share]


def analyze_rq1(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    gini_rows = []
    curve_rows = []
    for (project, year), g in df.groupby(["project_id", "year"]):
        for metric in ["nmod", "churn", "ccn"]:
            gini_rows.append({"project_id": project, "year": year, "metric": metric, "gini": gini(g[metric])})
            pop, share = lorenz(g[metric])
            for i, (p, s) in enumerate(zip(pop, share)):
                curve_rows.append({"project_id": project, "year": year, "metric": metric, "point": i, "population_share": p, "metric_share": s})
    return pd.DataFrame(gini_rows), pd.DataFrame(curve_rows)
