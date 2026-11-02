from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd


EXPECTED_PIPELINE_VERSION = "1.4.3"
EXPECTED_CACHE_SCHEMA = "v1.4.2"
MASTER_METRICS = ["nmod", "churn", "nloc", "ccn", "h", "h_geom"]
INDEPENDENT_CHECKS = ["nmod_match", "churn_match", "nloc_match", "ccn_match"]


class OutputValidationError(RuntimeError):
    """Raised when a generated pipeline artifact violates an invariant."""


def _require_columns(df: pd.DataFrame, columns: list[str], label: str) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise OutputValidationError(
            f"{label} não possui as colunas obrigatórias: {', '.join(missing)}"
        )


def validate_manifest(
    manifest: dict,
    expected_version: str = EXPECTED_PIPELINE_VERSION,
    expected_schema: str = EXPECTED_CACHE_SCHEMA,
) -> None:
    version = manifest.get("pipeline_version")
    schema = manifest.get("cache_schema")
    if version != expected_version:
        raise OutputValidationError(
            f"pipeline_version inválida: esperado {expected_version}, encontrado {version!r}"
        )
    if schema != expected_schema:
        raise OutputValidationError(
            f"cache_schema inválido: esperado {expected_schema}, encontrado {schema!r}"
        )
    if manifest.get("status") != "completed":
        raise OutputValidationError(
            "status do manifesto inválido para validação final: "
            f"esperado 'completed', encontrado {manifest.get('status')!r}"
        )


def validate_master(master: pd.DataFrame) -> None:
    required = [
        "project_id",
        "year",
        "file_id",
        "added",
        "deleted",
        *MASTER_METRICS,
    ]
    _require_columns(master, required, "05_master_hotspots.csv")

    null_counts = master[MASTER_METRICS].isna().sum()
    invalid_nulls = null_counts[null_counts > 0]
    if not invalid_nulls.empty:
        details = ", ".join(
            f"{column}={int(count)}" for column, count in invalid_nulls.items()
        )
        raise OutputValidationError(f"métricas com valores nulos: {details}")

    expected_churn = master["added"] + master["deleted"]
    mismatch = ~master["churn"].eq(expected_churn)
    if mismatch.any():
        raise OutputValidationError(
            f"churn diferente de added + deleted em {int(mismatch.sum())} observação(ões)"
        )

    duplicate = master.duplicated(
        subset=["project_id", "year", "file_id"], keep=False
    )
    if duplicate.any():
        raise OutputValidationError(
            "duplicação de project_id, year e file_id em "
            f"{int(duplicate.sum())} observação(ões)"
        )


def validate_identity_coverage(master: pd.DataFrame, identity: pd.DataFrame) -> None:
    _require_columns(master, ["file_id"], "05_master_hotspots.csv")
    _require_columns(identity, ["file_id"], "03_file_identity.csv")
    master_ids = set(master["file_id"].dropna().astype(str))
    identity_ids = set(identity["file_id"].dropna().astype(str))
    missing = sorted(master_ids - identity_ids)
    if missing:
        preview = ", ".join(missing[:5])
        suffix = "..." if len(missing) > 5 else ""
        raise OutputValidationError(
            f"{len(missing)} file_id do mestre ausente(s) no mapa de identidades: "
            f"{preview}{suffix}"
        )


def validate_rq4_candidates(candidates: pd.DataFrame) -> None:
    _require_columns(
        candidates,
        ["project_id", "file_id", "path"],
        "10_rq4_hotspot_candidates.csv",
    )
    if candidates.empty:
        return

    counts = candidates.groupby("project_id", dropna=False).size()
    over_limit = counts[counts > 3]
    if not over_limit.empty:
        details = ", ".join(
            f"{project}={int(count)}" for project, count in over_limit.items()
        )
        raise OutputValidationError(
            f"mais de três candidatos da RQ4 por projeto: {details}"
        )

    blank_path = candidates["path"].isna() | candidates["path"].astype(str).str.strip().eq("")
    if blank_path.any():
        raise OutputValidationError(
            f"caminho vazio em {int(blank_path.sum())} candidato(s) da RQ4"
        )


def validate_independent_results(details: pd.DataFrame) -> dict[str, tuple[int, int]]:
    _require_columns(details, INDEPENDENT_CHECKS, "validation_details.csv")
    if details.empty:
        raise OutputValidationError("a validação independente não produziu amostras")

    results: dict[str, tuple[int, int]] = {}
    total = len(details)
    for column in INDEPENDENT_CHECKS:
        matched = int(details[column].fillna(False).astype(bool).sum())
        results[column] = (matched, total)
        if matched != total:
            raise OutputValidationError(
                f"validação independente falhou em {column}: {matched}/{total} coincidências"
            )
    return results


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.is_file():
        raise OutputValidationError(f"arquivo obrigatório ausente: {path}")
    try:
        return pd.read_csv(path)
    except Exception as exc:
        raise OutputValidationError(f"não foi possível ler {path}: {exc}") from exc


def validate_project_outputs(
    project_id: str,
    output_dir: Path,
    validation_dir: Path,
) -> str:
    manifest_path = output_dir / "pipeline_manifest.json"
    if not manifest_path.is_file():
        raise OutputValidationError(f"arquivo obrigatório ausente: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise OutputValidationError(f"manifesto inválido em {manifest_path}: {exc}") from exc

    validate_manifest(manifest)

    audit = _read_csv(output_dir / "00_audit.csv")
    snapshots = _read_csv(output_dir / "01_snapshots.csv")
    identity = _read_csv(output_dir / "03_file_identity.csv")
    master = _read_csv(output_dir / "05_master_hotspots.csv")
    candidates = _read_csv(output_dir / "10_rq4_hotspot_candidates.csv")
    validation_details = _read_csv(validation_dir / "validation_details.csv")

    _require_columns(audit, ["project_id", "freeze_sha"], "00_audit.csv")
    _require_columns(snapshots, ["project_id", "year", "sha"], "01_snapshots.csv")
    if audit.empty:
        raise OutputValidationError("00_audit.csv está vazio")
    if snapshots.empty:
        raise OutputValidationError("01_snapshots.csv está vazio")

    observed_projects = set(master.get("project_id", pd.Series(dtype=str)).dropna().astype(str))
    if observed_projects != {project_id}:
        raise OutputValidationError(
            f"project_id do mestre não corresponde a {project_id!r}: {sorted(observed_projects)}"
        )

    validate_master(master)
    validate_identity_coverage(master, identity)
    validate_rq4_candidates(candidates)
    independent = validate_independent_results(validation_details)

    freeze_sha = str(audit.iloc[0]["freeze_sha"])
    snapshot_lines = [
        f"  - {int(row.year)}: {row.sha}"
        for row in snapshots.sort_values("year").itertuples(index=False)
    ]
    independent_lines = [
        f"  - {column}: {matched}/{total}"
        for column, (matched, total) in independent.items()
    ]
    candidate_lines = [
        f"  - {row.project_id}: rank {getattr(row, 'selection_rank', '?')}, "
        f"file_id={row.file_id}, path={row.path}"
        for row in candidates.itertuples(index=False)
    ] or ["  - nenhum candidato elegível"]

    summary = "\n".join(
        [
            "EXECUÇÃO VALIDADA DA PIPELINE",
            "=" * 72,
            f"Projeto: {project_id}",
            f"Versão da pipeline: {manifest['pipeline_version']}",
            f"Cache schema: {manifest['cache_schema']}",
            f"Freeze SHA: {freeze_sha}",
            f"Snapshots: {len(snapshots)}",
            *snapshot_lines,
            f"Observações do mestre: {len(master)}",
            f"Identidades: {identity['file_id'].nunique()}",
            "Validação independente:",
            *independent_lines,
            f"Candidatos da RQ4: {len(candidates)}",
            *candidate_lines,
            "Status final: SUCESSO",
            "",
        ]
    )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida invariantes dos artefatos gerados pela pipeline."
    )
    parser.add_argument("--project", required=True)
    parser.add_argument("--outputs", required=True, type=Path)
    parser.add_argument("--validation", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()

    try:
        summary = validate_project_outputs(
            args.project,
            args.outputs / args.project,
            args.validation / args.project,
        )
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(summary, encoding="utf-8")
    except OutputValidationError as exc:
        print(f"ERRO DE VALIDAÇÃO: {exc}")
        return 1

    print(summary, end="")
    print(f"Resumo salvo em: {args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
