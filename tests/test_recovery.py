import json

import pandas as pd
import pytest

from hotspots.pipeline import _config_fingerprint
from hotspots.config import load_config
from hotspots.recovery import RECOVERY_FILES, RecoveryError, create_recovery_manifest


def write_config(tmp_path):
    config_path = tmp_path / "demo.yml"
    config_path.write_text(
        "\n".join(
            [
                "project_id: demo",
                "name: Demo",
                "repo_url: https://example.invalid/demo.git",
                "local_path: repos/demo",
                "branch: main",
                f"freeze_sha: {'a' * 40}",
                "start_year: 2020",
                "end_year: 2026",
                "extensions: [.py]",
                "exclude_paths: [vendor]",
                "exclude_tests: true",
                "test_markers: [test, tests]",
                "exclude_migrations: false",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return config_path


def prepare_valid_partial_run(tmp_path):
    config_path = write_config(tmp_path)
    output_dir = tmp_path / "outputs" / "demo"
    output_dir.mkdir(parents=True)
    for filename in RECOVERY_FILES:
        pd.DataFrame([{"valid": 1}]).to_csv(output_dir / filename, index=False)
    return config_path, output_dir


def test_recovery_creates_expected_running_manifest(tmp_path):
    config_path, output_dir = prepare_valid_partial_run(tmp_path)

    manifest_path = create_recovery_manifest(config_path, tmp_path / "outputs", workers=4)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest == {
        "pipeline_version": "1.4.3",
        "cache_schema": "v1.4.2",
        "config_fingerprint": _config_fingerprint(load_config(config_path)),
        "workers": 4,
        "resume": True,
        "status": "running",
    }
    assert manifest_path == output_dir / "pipeline_manifest.json"


@pytest.mark.parametrize("missing_filename", RECOVERY_FILES)
def test_recovery_requires_every_initial_csv(tmp_path, missing_filename):
    config_path, output_dir = prepare_valid_partial_run(tmp_path)
    (output_dir / missing_filename).unlink()

    with pytest.raises(RecoveryError, match="ausente"):
        create_recovery_manifest(config_path, tmp_path / "outputs")

    assert not (output_dir / "pipeline_manifest.json").exists()


def test_recovery_rejects_unreadable_csv_without_creating_manifest(tmp_path):
    config_path, output_dir = prepare_valid_partial_run(tmp_path)
    (output_dir / "02_git_metrics.csv").write_bytes(b"\xff\xfe\x00")

    with pytest.raises(RecoveryError, match="CSV inválido"):
        create_recovery_manifest(config_path, tmp_path / "outputs")

    assert not (output_dir / "pipeline_manifest.json").exists()


def test_recovery_never_overwrites_existing_manifest(tmp_path):
    config_path, output_dir = prepare_valid_partial_run(tmp_path)
    manifest_path = output_dir / "pipeline_manifest.json"
    manifest_path.write_text('{"sentinel": true}', encoding="utf-8")

    with pytest.raises(RecoveryError, match="não será sobrescrito"):
        create_recovery_manifest(config_path, tmp_path / "outputs")

    assert json.loads(manifest_path.read_text(encoding="utf-8")) == {"sentinel": True}
