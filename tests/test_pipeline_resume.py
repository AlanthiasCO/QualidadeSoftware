import json
from types import SimpleNamespace

import pandas as pd
import pytest

import hotspots.pipeline as pipeline


class StageInterrupted(RuntimeError):
    pass


def make_config(tmp_path):
    return SimpleNamespace(
        project_id="demo",
        name="Demo",
        repo_url="https://example.invalid/demo.git",
        local_path=str(tmp_path / "repo"),
        repo_path=tmp_path / "repo",
        branch="main",
        freeze_sha="a" * 40,
        start_year=2020,
        end_year=2026,
        extensions=[".py"],
        exclude_paths=["vendor"],
        exclude_tests=True,
        test_markers=["test", "tests"],
        exclude_migrations=False,
    )


def patch_config_and_repository(monkeypatch, cfg):
    monkeypatch.setattr(pipeline, "load_config", lambda path: cfg)
    monkeypatch.setattr(pipeline, "clone_or_update", lambda config: config.repo_path)


def test_running_manifest_is_written_before_pipeline_stages(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    monkeypatch.setattr(pipeline, "load_config", lambda path: cfg)

    def interrupt_repository_stage(config):
        manifest_path = tmp_path / "outputs" / "demo" / "pipeline_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["status"] == "running"
        raise StageInterrupted("interrupção simulada")

    monkeypatch.setattr(pipeline, "clone_or_update", interrupt_repository_stage)

    with pytest.raises(StageInterrupted):
        pipeline.run_project("unused.yml", tmp_path / "outputs", workers=4, resume=False)

    manifest = json.loads(
        (tmp_path / "outputs" / "demo" / "pipeline_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest == {
        "pipeline_version": "1.4.3",
        "cache_schema": "v1.4.2",
        "config_fingerprint": pipeline._config_fingerprint(cfg),
        "workers": 4,
        "resume": False,
        "status": "running",
    }


def test_manifest_is_completed_only_after_all_stages(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    patch_config_and_repository(monkeypatch, cfg)

    audit = pd.DataFrame([{"project_id": "demo"}])
    snapshots = pd.DataFrame(
        [
            {
                "project_id": "demo",
                "year": 2026,
                "sha": "a" * 40,
                "snapshot_date": "2026-01-01T00:00:00Z",
            }
        ]
    )
    git_metrics = pd.DataFrame([{"project_id": "demo", "file_id": "f1"}])
    identity = pd.DataFrame(
        [
            {
                "project_id": "demo",
                "path": "src/a.py",
                "canonical_path": "src/a.py",
                "file_id": "f1",
            }
        ]
    )
    static = pd.DataFrame(
        [{"project_id": "demo", "year": 2026, "path": "src/a.py", "file_id": "f1"}]
    )
    master = pd.DataFrame([{"project_id": "demo", "year": 2026, "file_id": "f1"}])
    longitudinal = pd.DataFrame([{"project_id": "demo", "file_id": "f1"}])
    candidates = pd.DataFrame([{"project_id": "demo", "file_id": "f1"}])

    monkeypatch.setattr(pipeline, "audit_project", lambda config: audit)
    monkeypatch.setattr(pipeline, "build_snapshots", lambda config: snapshots)
    monkeypatch.setattr(
        pipeline,
        "mine_git_metrics",
        lambda *args, **kwargs: (git_metrics, identity),
    )
    monkeypatch.setattr(pipeline, "extract_static_metrics", lambda *args, **kwargs: static)
    monkeypatch.setattr(pipeline, "complete_identity_map", lambda old, current: old)
    monkeypatch.setattr(pipeline, "build_master", lambda git, current: master)
    monkeypatch.setattr(pipeline, "add_hotspot_score", lambda current: current)
    monkeypatch.setattr(
        pipeline,
        "analyze_rq1",
        lambda current: (pd.DataFrame([{"ok": 1}]), pd.DataFrame([{"ok": 1}])),
    )
    monkeypatch.setattr(pipeline, "analyze_rq2", lambda current: pd.DataFrame([{"ok": 1}]))
    monkeypatch.setattr(
        pipeline,
        "analyze_rq3",
        lambda current: (longitudinal, pd.DataFrame([{"ok": 1}])),
    )
    monkeypatch.setattr(pipeline, "select_qualitative_hotspots", lambda current: candidates)
    monkeypatch.setattr(pipeline, "qualitative_template", lambda current: current)

    pipeline.run_project("unused.yml", tmp_path / "outputs", workers=4, resume=False)

    manifest = json.loads(
        (tmp_path / "outputs" / "demo" / "pipeline_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["status"] == "completed"
    assert manifest["pipeline_version"] == "1.4.3"
    assert manifest["cache_schema"] == "v1.4.2"


def test_resume_accepts_running_manifest_with_compatible_fingerprint(
    monkeypatch, tmp_path
):
    cfg = make_config(tmp_path)
    patch_config_and_repository(monkeypatch, cfg)
    output_dir = tmp_path / "outputs" / "demo"
    output_dir.mkdir(parents=True)
    pd.DataFrame([{"project_id": "demo"}]).to_csv(
        output_dir / "00_audit.csv", index=False
    )
    (output_dir / "pipeline_manifest.json").write_text(
        json.dumps(
            {
                "pipeline_version": "1.4.2",
                "cache_schema": "v1.4.2",
                "config_fingerprint": pipeline._config_fingerprint(cfg),
                "workers": 4,
                "resume": True,
                "status": "running",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        pipeline,
        "build_snapshots",
        lambda config: (_ for _ in ()).throw(StageInterrupted("accepted")),
    )

    with pytest.raises(StageInterrupted, match="accepted"):
        pipeline.run_project("unused.yml", tmp_path / "outputs", workers=4, resume=True)

    manifest = json.loads(
        (output_dir / "pipeline_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["status"] == "running"
    assert manifest["pipeline_version"] == "1.4.3"


def test_resume_rejects_incompatible_fingerprint(monkeypatch, tmp_path):
    cfg = make_config(tmp_path)
    patch_config_and_repository(monkeypatch, cfg)
    output_dir = tmp_path / "outputs" / "demo"
    output_dir.mkdir(parents=True)
    pd.DataFrame([{"project_id": "demo"}]).to_csv(
        output_dir / "00_audit.csv", index=False
    )
    original = {
        "pipeline_version": "1.4.2",
        "cache_schema": "v1.4.2",
        "config_fingerprint": "incompatível",
        "workers": 4,
        "resume": True,
        "status": "running",
    }
    manifest_path = output_dir / "pipeline_manifest.json"
    manifest_path.write_text(json.dumps(original), encoding="utf-8")

    with pytest.raises(RuntimeError, match="fingerprint"):
        pipeline.run_project("unused.yml", tmp_path / "outputs", workers=4, resume=True)

    assert json.loads(manifest_path.read_text(encoding="utf-8")) == original
