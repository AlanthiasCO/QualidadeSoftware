from __future__ import annotations

from pathlib import Path
import hashlib
import json
import pandas as pd

from .config import load_config
from .repository import clone_or_update
from .snapshots import build_snapshots
from .audit import audit_project
from .git_metrics import mine_git_metrics
from .static_metrics import extract_static_metrics
from .scoring import build_master, add_hotspot_score
from .rq1 import analyze_rq1
from .rq2 import analyze_rq2
from .rq3 import analyze_rq3
from .rq4 import build_comparison_pairs, qualitative_template
from .utils import ensure_dir

CACHE_SCHEMA = "v1.4"


def _config_fingerprint(cfg) -> str:
    payload = {
        "schema": CACHE_SCHEMA,
        "project_id": cfg.project_id,
        "repo_url": cfg.repo_url,
        "branch": cfg.branch,
        "freeze_sha": cfg.freeze_sha,
        "start_year": cfg.start_year,
        "end_year": cfg.end_year,
        "extensions": sorted(cfg.extensions),
        "exclude_paths": sorted(cfg.exclude_paths),
        "exclude_tests": cfg.exclude_tests,
        "test_markers": sorted(cfg.test_markers),
        "exclude_migrations": cfg.exclude_migrations,
    }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _read_csv_if(path: Path, resume: bool) -> pd.DataFrame | None:
    if resume and path.exists():
        print(f"[CACHE] output={path}", flush=True)
        return pd.read_csv(path)
    return None


def run_project(
    config_path: str,
    output_root: str = "outputs",
    workers: int | None = None,
    resume: bool = True,
) -> Path:
    cfg = load_config(config_path)
    clone_or_update(cfg)
    out = ensure_dir(Path(output_root) / cfg.project_id)
    current_fp = _config_fingerprint(cfg)
    manifest_path = out / "pipeline_manifest.json"
    if resume and any(out.glob("*.csv")):
        if not manifest_path.exists():
            raise RuntimeError(
                f"Outputs existentes para {cfg.project_id} sem manifesto compatível. "
                "Use --no-resume ou execute o monitor com --clean após confirmar o freeze SHA."
            )
        try:
            old_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"Manifesto inválido em {manifest_path}: {exc}") from exc
        old_fp = old_manifest.get("config_fingerprint")
        if old_fp != current_fp:
            raise RuntimeError(
                f"Configuração/filtro mudou para {cfg.project_id} (fingerprint {old_fp} -> {current_fp}). "
                "Não é seguro reutilizar outputs antigos. Rode com --no-resume ou --clean."
            )
    cache_root = ensure_dir(out / ".cache" / current_fp)

    audit_path = out / "00_audit.csv"
    audit = _read_csv_if(audit_path, resume)
    if audit is None:
        audit = audit_project(cfg)
        audit.to_csv(audit_path, index=False)

    snapshots_path = out / "01_snapshots.csv"
    snapshots = _read_csv_if(snapshots_path, resume)
    if snapshots is None:
        snapshots = build_snapshots(cfg)
        snapshots.to_csv(snapshots_path, index=False)

    git_path = out / "02_git_metrics.csv"
    identity_path = out / "03_file_identity.csv"
    git_metrics = _read_csv_if(git_path, resume)
    identity = _read_csv_if(identity_path, resume)
    if git_metrics is None or identity is None:
        git_metrics, identity = mine_git_metrics(cfg, snapshots, cache_root=cache_root, resume=resume)
        git_metrics.to_csv(git_path, index=False)
        identity.to_csv(identity_path, index=False)

    static_path = out / "04_static_metrics.csv"
    static = _read_csv_if(static_path, resume)
    if static is None:
        static = extract_static_metrics(
            cfg,
            snapshots,
            identity,
            workers=workers,
            cache_root=cache_root,
            resume=resume,
        )
        static.to_csv(static_path, index=False)

    master_path = out / "05_master_hotspots.csv"
    master = _read_csv_if(master_path, resume)
    if master is None:
        master = add_hotspot_score(build_master(git_metrics, static))
        master.to_csv(master_path, index=False)

    rq1_path = out / "06_rq1_gini.csv"
    lorenz_path = out / "06b_rq1_lorenz_points.csv"
    rq1 = _read_csv_if(rq1_path, resume)
    lorenz_points = _read_csv_if(lorenz_path, resume)
    if rq1 is None or lorenz_points is None:
        rq1, lorenz_points = analyze_rq1(master)
        rq1.to_csv(rq1_path, index=False)
        lorenz_points.to_csv(lorenz_path, index=False)

    rq2_path = out / "07_rq2_associations.csv"
    rq2 = _read_csv_if(rq2_path, resume)
    if rq2 is None:
        rq2 = analyze_rq2(master)
        rq2.to_csv(rq2_path, index=False)

    longi_path = out / "08_rq3_longitudinal_files.csv"
    stability_path = out / "09_rq3_ranking_stability.csv"
    longi = _read_csv_if(longi_path, resume)
    stability = _read_csv_if(stability_path, resume)
    if longi is None or stability is None:
        longi, stability = analyze_rq3(master)
        longi.to_csv(longi_path, index=False)
        stability.to_csv(stability_path, index=False)

    pairs_path = out / "10_rq4_comparison_pairs.csv"
    pairs = _read_csv_if(pairs_path, resume)
    if pairs is None:
        pairs = build_comparison_pairs(longi)
        pairs.to_csv(pairs_path, index=False)

    qualitative_path = out / "11_rq4_qualitative_template.csv"
    qualitative = _read_csv_if(qualitative_path, resume)
    if qualitative is None:
        qualitative_template(pairs).to_csv(qualitative_path, index=False)

    manifest = {
        "pipeline_version": "1.4.0",
        "cache_schema": CACHE_SCHEMA,
        "config_fingerprint": current_fp,
        "workers": workers,
        "resume": resume,
    }
    (out / "pipeline_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return out
