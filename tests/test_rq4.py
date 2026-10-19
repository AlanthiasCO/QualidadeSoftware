import pandas as pd

from hotspots.rq4 import select_static_analysis_pairs


def make_row(project, number, h, nloc, snapshots=7, language="Python"):
    return {
        "project_id": project, "language": language,
        "file_id": f"{project}-{number}", "path": f"src/{project}_{number}.py",
        "snapshots": snapshots, "first_year": 2020 + number % 2,
        "last_year": 2026, "h_median": h, "h_iqr": 0.1,
        "h_min": h - 0.1, "h_max": h + 0.01, "nloc_median": nloc,
    }


def test_selects_deterministic_unique_pairs():
    rows = [
        make_row("alpha", 1, 0.99, 110), make_row("alpha", 2, 0.95, 210),
        make_row("alpha", 3, 0.70, 100), make_row("alpha", 4, 0.60, 200),
        make_row("alpha", 5, 0.10, 300),
        make_row("alpha", 6, 1.00, 400, snapshots=1),
    ]
    pairs = select_static_analysis_pairs(
        pd.DataFrame(rows), max_pairs_per_project=2,
        high_quantile=0.70, low_quantile=0.50, min_snapshots=2,
    )
    assert len(pairs) == 4
    assert pairs.groupby("pair_id").size().eq(2).all()
    assert set(pairs["group"]) == {"hotspot", "control"}
    assert pairs[pairs["group"] == "control"]["file_id"].is_unique
    assert "alpha-6" not in set(pairs["file_id"])


def test_empty_input_has_stable_schema():
    pairs = select_static_analysis_pairs(pd.DataFrame())
    assert pairs.empty
    assert {"pair_id", "group", "path", "matched_distance"}.issubset(pairs.columns)


def test_pair_limit_is_per_project_not_per_language():
    rows = []
    for language in ["Python", "JavaScript", "TypeScript"]:
        rows.extend(
            make_row("multi", number, h, 100 + number, language=language)
            for number, h in [(1, 0.99), (2, 0.95), (3, 0.40), (4, 0.10)]
        )
    pairs = select_static_analysis_pairs(
        pd.DataFrame(rows), max_pairs_per_project=5,
        high_quantile=0.50, low_quantile=0.50,
    )
    assert pairs["pair_id"].nunique() == 5
    assert len(pairs) == 10
