import pandas as pd

from hotspots.identity import complete_identity_map


def test_complete_identity_map_preserves_renames_and_adds_snapshot_only_paths():
    identity = pd.DataFrame(
        [
            {
                "project_id": "demo",
                "path": "src/old_name.py",
                "canonical_path": "src/old_name.py",
                "file_id": "renamed-file-id",
            },
            {
                "project_id": "demo",
                "path": "src/new_name.py",
                "canonical_path": "src/old_name.py",
                "file_id": "renamed-file-id",
            },
        ]
    )

    static_metrics = pd.DataFrame(
        [
            {
                "project_id": "demo",
                "year": 2020,
                "path": "src/new_name.py",
                "file_id": "renamed-file-id",
            },
            {
                "project_id": "demo",
                "year": 2020,
                "path": "src/unchanged.py",
                "file_id": "unchanged-file-id",
            },
        ]
    )

    completed = complete_identity_map(identity, static_metrics)

    assert set(completed["path"]) == {
        "src/old_name.py",
        "src/new_name.py",
        "src/unchanged.py",
    }

    renamed = completed[completed["path"] == "src/new_name.py"].iloc[0]
    assert renamed["canonical_path"] == "src/old_name.py"
    assert renamed["file_id"] == "renamed-file-id"

    unchanged = completed[completed["path"] == "src/unchanged.py"].iloc[0]
    assert unchanged["canonical_path"] == "src/unchanged.py"
    assert unchanged["file_id"] == "unchanged-file-id"
