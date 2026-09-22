from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, pearsonr, rankdata


def _is_constant(values) -> bool:
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    return len(a) == 0 or np.unique(a).size < 2


def _partial_spearman(x, y, z):
    x, y, z = map(lambda a: np.asarray(a, dtype=float), (x, y, z))
    mask = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    x, y, z = x[mask], y[mask], z[mask]
    if len(x) < 4 or _is_constant(x) or _is_constant(y):
        return np.nan, np.nan
    xr, yr, zr = rankdata(x), rankdata(y), rankdata(z)
    Z = np.column_stack([np.ones(len(zr)), zr])
    bx = np.linalg.lstsq(Z, xr, rcond=None)[0]
    by = np.linalg.lstsq(Z, yr, rcond=None)[0]
    rx = xr - Z @ bx
    ry = yr - Z @ by
    if _is_constant(rx) or _is_constant(ry):
        return np.nan, np.nan
    return pearsonr(rx, ry)


def analyze_rq2(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (project, year), g in df.groupby(["project_id", "year"]):
        for xcol in ["nmod", "churn"]:
            if len(g) < 3:
                continue
            x_constant = _is_constant(g[xcol])
            ccn_constant = _is_constant(g["ccn"])
            if x_constant or ccn_constant:
                rho, p = np.nan, np.nan
                reason = "constant_input:" + (xcol if x_constant else "ccn")
            else:
                rho, p = spearmanr(g[xcol], g["ccn"], nan_policy="omit")
                reason = "ok"
            prho, pp = _partial_spearman(g[xcol], g["ccn"], g["nloc"])
            rows.append({
                "project_id": project,
                "year": year,
                "relation": f"{xcol}_vs_ccn",
                "spearman_rho": rho,
                "spearman_p": p,
                "partial_spearman_rho_control_nloc": prho,
                "partial_spearman_p": pp,
                "n_files": len(g),
                "status": reason,
            })
    return pd.DataFrame(rows)
