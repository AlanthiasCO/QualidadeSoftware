from types import SimpleNamespace

import pandas as pd

import hotspots.git_metrics as git_metrics


def test_identical_event_at_annual_boundary_is_not_counted_twice(
    monkeypatch,
    tmp_path,
):
    """Um evento repetido em duas janelas deve contribuir uma única vez."""

    snapshots = pd.DataFrame(
        [
            {
                "year": 2020,
                "sha": "a" * 40,
                "snapshot_date": "2020-12-31T23:59:59Z",
            },
            {
                "year": 2021,
                "sha": "b" * 40,
                "snapshot_date": "2021-12-31T23:59:59Z",
            },
        ]
    )

    duplicated_event = {
        "commit": "c" * 40,
        "commit_date": "2020-12-31T23:59:59+00:00",
        "path": "src/example.py",
        "old_path": "src/example.py",
        "new_path": "src/example.py",
        "added": 10,
        "deleted": 4,
    }

    monkeypatch.setattr(
        git_metrics,
        "_commit_total",
        lambda cfg, start, end: 1,
    )

    def fake_load_or_mine_window(
        cfg,
        year,
        sha,
        start,
        end,
        cache_dir,
        resume,
        global_done,
        global_total,
        started,
    ):
        events = pd.DataFrame(
            [duplicated_event],
            columns=git_metrics.EVENT_COLUMNS,
        )
        return events, global_done + 1

    monkeypatch.setattr(
        git_metrics,
        "_load_or_mine_window",
        fake_load_or_mine_window,
    )

    cfg = SimpleNamespace(
        project_id="test-project",
        start_year=2020,
    )

    metrics, _ = git_metrics.mine_git_metrics(
        cfg,
        snapshots,
        cache_root=tmp_path,
        resume=False,
    )

    assert len(metrics) == 1

    row = metrics.iloc[0]
    assert row["year"] == 2020
    assert row["nmod"] == 1
    assert row["added"] == 10
    assert row["deleted"] == 4
    assert row["churn"] == 14
