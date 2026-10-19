from __future__ import annotations

import numpy as np
import pandas as pd


PAIR_COLUMNS = [
    "pair_id", "project_id", "language", "matched_distance", "group",
    "file_id", "path", "snapshots", "first_year", "last_year",
    "h_median", "nloc_median", "selection_rule",
]


def select_static_analysis_pairs(
    longitudinal: pd.DataFrame,
    max_pairs_per_project: int = 5,
    high_quantile: float = 0.90,
    low_quantile: float = 0.50,
    min_snapshots: int = 2,
) -> pd.DataFrame:
    """Select deterministic hotspot-control pairs for automated analysis."""
    if longitudinal.empty:
        return pd.DataFrame(columns=PAIR_COLUMNS)

    rows: list[dict] = []
    for project, project_rows in longitudinal.groupby("project_id", sort=True):
        hotspot_frames: list[pd.DataFrame] = []
        control_pools: dict[str, pd.DataFrame] = {}
        for language, group in project_rows.groupby("language", sort=True):
            eligible = group[group["snapshots"] >= min_snapshots].copy()
            if len(eligible) < 2:
                continue
            high_cut = eligible["h_median"].quantile(high_quantile)
            low_cut = eligible["h_median"].quantile(low_quantile)
            hotspots = eligible[eligible["h_median"] >= high_cut].copy()
            controls = eligible[eligible["h_median"] <= low_cut].copy()
            if hotspots.empty or controls.empty:
                continue
            for column in ["nloc_median", "first_year"]:
                scale = float(controls[column].std(ddof=0))
                if not np.isfinite(scale) or scale == 0:
                    scale = 1.0
                center = float(controls[column].mean())
                controls[f"z_{column}"] = (controls[column] - center) / scale
                hotspots[f"z_{column}"] = (hotspots[column] - center) / scale
            hotspot_frames.append(hotspots)
            control_pools[str(language)] = controls

        if not hotspot_frames:
            continue
        project_hotspots = pd.concat(hotspot_frames, ignore_index=True).sort_values(
            ["h_median", "nloc_median", "file_id"],
            ascending=[False, False, True],
        )
        used_controls: dict[str, set[str]] = {
            language: set() for language in control_pools
        }
        pair_number = 0

        for _, hotspot in project_hotspots.iterrows():
            if pair_number >= max_pairs_per_project:
                break
            language = str(hotspot["language"])
            controls = control_pools[language]
            available = controls[
                ~controls["file_id"].isin(used_controls[language])
            ].copy()
            if available.empty:
                continue
            distance = np.sqrt(
                (available["z_nloc_median"] - hotspot["z_nloc_median"]) ** 2
                + (available["z_first_year"] - hotspot["z_first_year"]) ** 2
            )
            control = available.assign(_distance=distance).sort_values(
                ["_distance", "file_id"], ascending=[True, True]
            ).iloc[0]
            used_controls[language].add(str(control["file_id"]))
            pair_number += 1
            pair_id = f"{project}-P{pair_number:02d}"
            rule = (
                f"hotspot no quantil >= {high_quantile:.2f}; controle no quantil "
                f"<= {low_quantile:.2f}; pareamento por NLOC mediano e primeiro ano"
            )
            for label, item in [("hotspot", hotspot), ("control", control)]:
                rows.append({
                    "pair_id": pair_id,
                    "project_id": project,
                    "language": language,
                    "matched_distance": float(control["_distance"]),
                    "group": label,
                    "file_id": item["file_id"],
                    "path": item["path"],
                    "snapshots": int(item["snapshots"]),
                    "first_year": int(item["first_year"]),
                    "last_year": int(item["last_year"]),
                    "h_median": float(item["h_median"]),
                    "nloc_median": float(item["nloc_median"]),
                    "selection_rule": rule,
                })

    return pd.DataFrame(rows, columns=PAIR_COLUMNS)
