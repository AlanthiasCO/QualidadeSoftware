from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd
import numpy as np

FILES = [
    "02_git_metrics.csv", "03_file_identity.csv", "04_static_metrics.csv",
    "05_master_hotspots.csv", "06_rq1_gini.csv", "06b_rq1_lorenz_points.csv",
    "07_rq2_associations.csv", "08_rq3_longitudinal_files.csv",
    "09_rq3_ranking_stability.csv", "10_rq4_hotspot_candidates.csv",
]


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    cols = sorted(df.columns)
    df = df[cols].copy()
    sort_cols = [c for c in cols if not pd.api.types.is_numeric_dtype(df[c])]
    sort_cols += [c for c in cols if c not in sort_cols]
    try:
        df = df.sort_values(sort_cols, kind="mergesort", na_position="last")
    except Exception:
        pass
    return df.reset_index(drop=True)


def compare_csv(a: Path, b: Path, atol: float) -> tuple[bool, str]:
    if not a.exists() or not b.exists():
        return False, "arquivo ausente"
    da, db = normalize(pd.read_csv(a)), normalize(pd.read_csv(b))
    if list(da.columns) != list(db.columns):
        return False, "colunas diferentes"
    if da.shape != db.shape:
        return False, f"shape diferente {da.shape} vs {db.shape}"
    for c in da.columns:
        if pd.api.types.is_numeric_dtype(da[c]) and pd.api.types.is_numeric_dtype(db[c]):
            xa = pd.to_numeric(da[c], errors="coerce").to_numpy(float)
            xb = pd.to_numeric(db[c], errors="coerce").to_numpy(float)
            if not np.allclose(xa, xb, equal_nan=True, atol=atol, rtol=0):
                idx = np.where(~np.isclose(xa, xb, equal_nan=True, atol=atol, rtol=0))[0][0]
                return False, f"dif numerica em {c}, linha {idx}: {xa[idx]} vs {xb[idx]}"
        else:
            xa = da[c].fillna("<NA>").astype(str).to_numpy()
            xb = db[c].fillna("<NA>").astype(str).to_numpy()
            if not np.array_equal(xa, xb):
                idx = np.where(xa != xb)[0][0]
                return False, f"dif textual em {c}, linha {idx}: {xa[idx]!r} vs {xb[idx]!r}"
    return True, "identico"


def main():
    ap = argparse.ArgumentParser(description="Compara outputs baseline e v1.3 sem depender da ordem das linhas.")
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--atol", type=float, default=1e-12)
    args = ap.parse_args()

    base, cand = Path(args.baseline), Path(args.candidate)
    ok_all = True
    print("COMPARACAO DE REPRODUTIBILIDADE")
    print("=" * 72)
    for name in FILES:
        ok, msg = compare_csv(base / name, cand / name, args.atol)
        ok_all &= ok
        print(f"[{'OK' if ok else 'DIF'}] {name}: {msg}")
    raise SystemExit(0 if ok_all else 2)


if __name__ == "__main__":
    main()
