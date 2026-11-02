from __future__ import annotations

import pandas as pd


CANDIDATE_COLUMNS = [
    "project_id",
    "selection_rank",
    "language",
    "file_id",
    "path",
    "snapshots",
    "first_year",
    "last_year",
    "h_median",
    "h_iqr",
    "h_min",
    "h_max",
    "nloc_median",
    "selection_rule",
]


def select_qualitative_hotspots(
    longitudinal: pd.DataFrame,
    max_per_project: int = 3,
    high_quantile: float = 0.90,
    min_snapshots: int = 2,
) -> pd.DataFrame:
    """Select up to three persistent hotspots per project for RQ4."""

    if longitudinal.empty:
        return pd.DataFrame(columns=CANDIDATE_COLUMNS)

    eligible = longitudinal[
        longitudinal["snapshots"] >= min_snapshots
    ].copy()

    if eligible.empty:
        return pd.DataFrame(columns=CANDIDATE_COLUMNS)

    eligible["high_cut"] = eligible.groupby(
        ["project_id", "language"]
    )["h_median"].transform(
        lambda values: values.quantile(high_quantile)
    )

    candidates = eligible[
        eligible["h_median"] >= eligible["high_cut"]
    ].copy()

    candidates = candidates.sort_values(
        [
            "project_id",
            "h_median",
            "h_max",
            "snapshots",
            "file_id",
        ],
        ascending=[True, False, False, False, True],
    )

    selected = candidates.groupby(
        "project_id",
        group_keys=False,
    ).head(max_per_project).copy()

    selected["selection_rank"] = (
        selected.groupby("project_id").cumcount() + 1
    )

    percentile = round((1.0 - high_quantile) * 100)
    selected["selection_rule"] = (
        f"top {percentile}% de H mediano por projeto e linguagem; "
        f"mínimo de {min_snapshots} snapshots; "
        f"máximo de {max_per_project} casos por projeto"
    )

    return selected[CANDIDATE_COLUMNS].reset_index(drop=True)


def qualitative_template(candidates: pd.DataFrame) -> pd.DataFrame:
    columns = CANDIDATE_COLUMNS + [
        "artifact_type",
        "artifact_reference",
        "evidence_excerpt_or_summary",
        "context_notes",
        "reviewer_1_class",
        "reviewer_2_class",
        "agreement",
        "consensus_class",
    ]

    if candidates.empty:
        return pd.DataFrame(columns=columns)

    result = candidates.copy()
    for column in columns[len(CANDIDATE_COLUMNS):]:
        result[column] = ""

    return result[columns]
