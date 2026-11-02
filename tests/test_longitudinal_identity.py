import pandas as pd
import pytest

from hotspots.git_metrics import (
    EVENT_COLUMNS,
    _reconstruct_longitudinal_identity,
    _validate_canonical_snapshot_uniqueness,
)
from hotspots.identity import IdentityCollisionError, validate_snapshot_file_id_uniqueness
from hotspots.scoring import build_master
from hotspots.utils import stable_id


def events(*rows):
    return pd.DataFrame(rows, columns=EVENT_COLUMNS)


def rename_event(date, commit, old_path, new_path):
    return {
        "commit": commit,
        "commit_date": date,
        "path": new_path,
        "old_path": old_path,
        "new_path": new_path,
        "added": 1,
        "deleted": 1,
    }


def test_legitimate_rename_keeps_the_same_file_id():
    snapshot_paths = {
        "2020:old": {"src/old.py"},
        "2021:new": {"src/new.py"},
    }
    canonical = _reconstruct_longitudinal_identity(
        events(
            rename_event(
                "2021-01-01T00:00:00Z",
                "a" * 40,
                "src/old.py",
                "src/new.py",
            )
        ),
        snapshot_paths,
    )

    assert canonical["src/old.py"] == canonical["src/new.py"]
    assert stable_id("demo", canonical["src/old.py"]) == stable_id(
        "demo", canonical["src/new.py"]
    )


def test_copy_or_false_rename_with_coexisting_paths_keeps_distinct_ids():
    snapshot_paths = {
        "2021:both": {"src/original.py", "src/copy.py"},
    }
    canonical = _reconstruct_longitudinal_identity(
        events(
            rename_event(
                "2021-01-01T00:00:00Z",
                "b" * 40,
                "src/original.py",
                "src/copy.py",
            )
        ),
        snapshot_paths,
    )

    assert canonical["src/original.py"] != canonical["src/copy.py"]
    assert stable_id("demo", canonical["src/original.py"]) != stable_id(
        "demo", canonical["src/copy.py"]
    )


def test_transitive_component_collision_rejects_the_later_union():
    snapshot_paths = {
        "2020:first": {"src/a.py", "src/c.py"},
        "2021:middle": {"src/b.py"},
    }
    canonical = _reconstruct_longitudinal_identity(
        events(
            rename_event(
                "2020-06-01T00:00:00Z", "a" * 40, "src/a.py", "src/b.py"
            ),
            rename_event(
                "2021-06-01T00:00:00Z", "b" * 40, "src/b.py", "src/c.py"
            ),
        ),
        snapshot_paths,
    )

    assert canonical["src/a.py"] == canonical["src/b.py"]
    assert canonical["src/c.py"] != canonical["src/a.py"]


def test_reconstruction_is_deterministic_for_different_dataframe_orders():
    snapshot_paths = {
        "2020:a": {"src/a.py", "src/c.py"},
        "2021:b": {"src/b.py"},
        "2022:d": {"src/d.py"},
    }
    original = events(
        rename_event("2022-02-01T00:00:00Z", "d" * 40, "src/c.py", "src/d.py"),
        rename_event("2020-02-01T00:00:00Z", "a" * 40, "src/a.py", "src/b.py"),
        rename_event("2021-02-01T00:00:00Z", "b" * 40, "src/b.py", "src/c.py"),
    )
    shuffled = original.sample(frac=1, random_state=42).reset_index(drop=True)

    first = _reconstruct_longitudinal_identity(original, snapshot_paths)
    second = _reconstruct_longitudinal_identity(shuffled, snapshot_paths)

    assert first == second


def test_residual_snapshot_collision_raises_a_clear_error():
    with pytest.raises(IdentityCollisionError, match="snapshot 2026:sha"):
        _validate_canonical_snapshot_uniqueness(
            {"src/a.py": "same", "src/b.py": "same"},
            {"2026:sha": {"src/a.py", "src/b.py"}},
        )


def test_static_and_master_keys_are_unique_for_legitimate_rename():
    file_id = stable_id("demo", "src/old.py")
    static = pd.DataFrame(
        [
            {
                "project_id": "demo",
                "year": 2020,
                "path": "src/old.py",
                "file_id": file_id,
                "language": "Python",
                "nloc": 10,
                "ccn": 1,
            },
            {
                "project_id": "demo",
                "year": 2021,
                "path": "src/new.py",
                "file_id": file_id,
                "language": "Python",
                "nloc": 11,
                "ccn": 2,
            },
        ]
    )
    git = pd.DataFrame(
        [
            {
                "project_id": "demo",
                "year": 2020,
                "file_id": file_id,
                "nmod": 1,
                "added": 1,
                "deleted": 0,
                "churn": 1,
            },
            {
                "project_id": "demo",
                "year": 2021,
                "file_id": file_id,
                "nmod": 1,
                "added": 1,
                "deleted": 1,
                "churn": 2,
            },
        ]
    )

    validate_snapshot_file_id_uniqueness(static, "métricas estáticas")
    master = build_master(git, static)

    assert not static.duplicated(["project_id", "year", "file_id"]).any()
    assert not master.duplicated(["project_id", "year", "file_id"]).any()


def test_static_and_master_reject_two_paths_with_same_snapshot_identity():
    static = pd.DataFrame(
        [
            {
                "project_id": "demo",
                "year": 2026,
                "path": "src/a.py",
                "file_id": "collision",
            },
            {
                "project_id": "demo",
                "year": 2026,
                "path": "src/b.py",
                "file_id": "collision",
            },
        ]
    )

    with pytest.raises(IdentityCollisionError, match="unicidade"):
        validate_snapshot_file_id_uniqueness(static, "métricas estáticas")
    with pytest.raises(IdentityCollisionError, match="unicidade"):
        build_master(pd.DataFrame(), static)
