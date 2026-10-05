from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from . import __version__
from .config import load_config
from .pipeline import CACHE_SCHEMA, _config_fingerprint


RECOVERY_FILES = (
    "00_audit.csv",
    "01_snapshots.csv",
    "02_git_metrics.csv",
    "03_file_identity.csv",
)


class RecoveryError(RuntimeError):
    """Raised when a legacy interrupted run cannot be recovered safely."""


def create_recovery_manifest(
    config_path: str | Path,
    output_root: str | Path = "outputs",
    workers: int = 4,
) -> Path:
    """Create a running manifest for a validated legacy partial execution.

    The manifest is created exclusively and never replaces an existing file.
    """
    if __version__ != "1.4.3" or CACHE_SCHEMA != "v1.4.2":
        raise RecoveryError(
            "recuperação exige pipeline 1.4.3 e cache_schema v1.4.2; "
            f"encontrado {__version__!r}/{CACHE_SCHEMA!r}"
        )

    cfg = load_config(config_path)
    output_dir = Path(output_root) / cfg.project_id
    manifest_path = output_dir / "pipeline_manifest.json"
    if manifest_path.exists():
        raise RecoveryError(
            f"manifesto já existe e não será sobrescrito: {manifest_path}; "
            "use --resume para uma execução já manifestada"
        )
    if not output_dir.is_dir():
        raise RecoveryError(f"diretório de outputs não encontrado: {output_dir}")

    for filename in RECOVERY_FILES:
        path = output_dir / filename
        if not path.is_file():
            raise RecoveryError(f"CSV obrigatório para recuperação ausente: {path}")
        try:
            pd.read_csv(path)
        except Exception as exc:
            raise RecoveryError(f"CSV inválido para recuperação: {path}: {exc}") from exc

    manifest = {
        "pipeline_version": __version__,
        "cache_schema": CACHE_SCHEMA,
        "config_fingerprint": _config_fingerprint(cfg),
        "workers": workers,
        "resume": True,
        "status": "running",
    }
    try:
        with manifest_path.open("x", encoding="utf-8") as stream:
            json.dump(manifest, stream, indent=2)
    except FileExistsError as exc:
        raise RecoveryError(
            f"manifesto surgiu durante a recuperação e não foi sobrescrito: {manifest_path}"
        ) from exc
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cria com segurança o manifesto de uma execução antiga interrompida."
    )
    parser.add_argument("--config", required=True)
    parser.add_argument("--outputs", default="outputs")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    try:
        path = create_recovery_manifest(args.config, args.outputs, args.workers)
    except RecoveryError as exc:
        print(f"ERRO DE RECUPERAÇÃO: {exc}")
        return 1
    print(f"Manifesto de recuperação criado: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
