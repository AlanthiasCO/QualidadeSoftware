import pandas as pd

from hotspots.rq4 import qualitative_template, select_qualitative_hotspots


def make_row(project, number, h, snapshots=7):
    return {
        "project_id": project,
        "language": "Python",
        "file_id": f"{project}-{number}",
        "path": f"src/{project}_{number}.py",
        "snapshots": snapshots,
        "first_year": 2020,
        "last_year": 2026,
        "h_median": h,
        "h_iqr": 0.1,
        "h_min": h - 0.1,
        "h_max": h + 0.01,
        "nloc_median": 100 + number,
    }


def test_selects_at_most_three_hotspots_per_project():
    rows = [
        make_row("alpha", 1, 0.99),
        make_row("alpha", 2, 0.95),
        make_row("alpha", 3, 0.90),
        make_row("alpha", 4, 0.85),
        make_row("alpha", 5, 1.00, snapshots=1),
        make_row("beta", 1, 0.98),
        make_row("beta", 2, 0.80),
    ]
    longitudinal = pd.DataFrame(rows)

    selected = select_qualitative_hotspots(
        longitudinal,
        max_per_project=3,
        high_quantile=0.0,
        min_snapshots=2,
    )

    counts = selected.groupby("project_id").size().to_dict()
    assert counts == {"alpha": 3, "beta": 2}

    alpha = selected[selected["project_id"] == "alpha"]
    assert alpha["file_id"].tolist() == [
        "alpha-1",
        "alpha-2",
        "alpha-3",
    ]
    assert alpha["selection_rank"].tolist() == [1, 2, 3]
    assert "src/alpha_1.py" in alpha["path"].tolist()

    template = qualitative_template(selected)
    assert len(template) == len(selected)
    assert "pair_role" not in template.columns
    assert "path" in template.columns
    assert "nloc_median" in template.columns
    assert "reviewer_1_class" in template.columns
