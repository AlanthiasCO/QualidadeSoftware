import json

import pandas as pd
import pytest

from hotspots.output_validation import (
    OutputValidationError,
    validate_identity_coverage,
    validate_independent_results,
    validate_manifest,
    validate_master,
    validate_project_outputs,
    validate_rq4_candidates,
)


def valid_master():
    return pd.DataFrame(
        [
            {
                "project_id": "demo",
                "year": 2026,
                "file_id": "file-1",
                "added": 7,
                "deleted": 3,
                "nmod": 2,
                "churn": 10,
                "nloc": 100,
                "ccn": 12,
                "h": 0.8,
                "h_geom": 0.85,
            }
        ]
    )


def test_manifest_requires_pipeline_and_cache_version():
    validate_manifest(
        {
            "pipeline_version": "1.4.3",
            "cache_schema": "v1.4.2",
            "status": "completed",
        }
    )

    with pytest.raises(OutputValidationError, match="pipeline_version"):
        validate_manifest(
            {
                "pipeline_version": "1.4.1",
                "cache_schema": "v1.4.2",
                "status": "completed",
            }
        )
    with pytest.raises(OutputValidationError, match="cache_schema"):
        validate_manifest(
            {
                "pipeline_version": "1.4.3",
                "cache_schema": "v1.4",
                "status": "completed",
            }
        )
    with pytest.raises(OutputValidationError, match="status"):
        validate_manifest(
            {
                "pipeline_version": "1.4.3",
                "cache_schema": "v1.4.2",
                "status": "running",
            }
        )


@pytest.mark.parametrize("metric", ["nmod", "churn", "nloc", "ccn", "h", "h_geom"])
def test_master_rejects_null_metrics(metric):
    master = valid_master()
    master.loc[0, metric] = None
    with pytest.raises(OutputValidationError, match="valores nulos"):
        validate_master(master)


def test_master_rejects_invalid_churn_and_duplicate_key():
    master = valid_master()
    master.loc[0, "churn"] = 11
    with pytest.raises(OutputValidationError, match=r"added \+ deleted"):
        validate_master(master)

    duplicated = pd.concat([valid_master(), valid_master()], ignore_index=True)
    with pytest.raises(OutputValidationError, match="duplicação"):
        validate_master(duplicated)


def test_identity_map_must_cover_every_master_file_id():
    identity = pd.DataFrame([{"file_id": "another-file"}])
    with pytest.raises(OutputValidationError, match="ausente"):
        validate_identity_coverage(valid_master(), identity)


def test_rq4_rejects_more_than_three_candidates_and_blank_paths():
    candidates = pd.DataFrame(
        [
            {"project_id": "demo", "file_id": f"f-{index}", "path": f"src/{index}.py"}
            for index in range(4)
        ]
    )
    with pytest.raises(OutputValidationError, match="mais de três"):
        validate_rq4_candidates(candidates)

    candidates = candidates.iloc[:3].copy()
    candidates.loc[0, "path"] = "  "
    with pytest.raises(OutputValidationError, match="caminho vazio"):
        validate_rq4_candidates(candidates)


def test_independent_validation_requires_all_matches():
    details = pd.DataFrame(
        [
            {
                "nmod_match": True,
                "churn_match": False,
                "nloc_match": True,
                "ccn_match": True,
            }
        ]
    )
    with pytest.raises(OutputValidationError, match="churn_match"):
        validate_independent_results(details)


def test_valid_project_writes_complete_summary_data(tmp_path):
    output_dir = tmp_path / "outputs" / "demo"
    validation_dir = tmp_path / "validation" / "demo"
    output_dir.mkdir(parents=True)
    validation_dir.mkdir(parents=True)

    (output_dir / "pipeline_manifest.json").write_text(
        json.dumps(
            {
                "pipeline_version": "1.4.3",
                "cache_schema": "v1.4.2",
                "status": "completed",
            }
        ),
        encoding="utf-8",
    )
    pd.DataFrame([{"project_id": "demo", "freeze_sha": "abc123"}]).to_csv(
        output_dir / "00_audit.csv", index=False
    )
    pd.DataFrame(
        [{"project_id": "demo", "year": 2026, "sha": "abc123"}]
    ).to_csv(output_dir / "01_snapshots.csv", index=False)
    pd.DataFrame([{"project_id": "demo", "file_id": "file-1"}]).to_csv(
        output_dir / "03_file_identity.csv", index=False
    )
    valid_master().to_csv(output_dir / "05_master_hotspots.csv", index=False)
    pd.DataFrame(
        [
            {
                "project_id": "demo",
                "selection_rank": 1,
                "file_id": "file-1",
                "path": "src/example.py",
            }
        ]
    ).to_csv(output_dir / "10_rq4_hotspot_candidates.csv", index=False)
    pd.DataFrame(
        [
            {
                "nmod_match": True,
                "churn_match": True,
                "nloc_match": True,
                "ccn_match": True,
            }
        ]
    ).to_csv(validation_dir / "validation_details.csv", index=False)

    summary = validate_project_outputs("demo", output_dir, validation_dir)

    assert "Projeto: demo" in summary
    assert "Versão da pipeline: 1.4.3" in summary
    assert "Freeze SHA: abc123" in summary
    assert "Snapshots: 1" in summary
    assert "Observações do mestre: 1" in summary
    assert "Identidades: 1" in summary
    assert "Candidatos da RQ4: 1" in summary
    assert "Status final: SUCESSO" in summary
