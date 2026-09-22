from __future__ import annotations

import argparse
from .pipeline import run_project
from .config import load_config
from .repository import clone_or_update
from .audit import audit_project


def main() -> None:
    parser = argparse.ArgumentParser(prog="hotspots")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Executa pipeline completa de um projeto")
    run.add_argument("--config", required=True)
    run.add_argument("--output", default="outputs")
    run.add_argument("--workers", type=int, default=None, help="Processos para NLOC/CCN; padrao: ate 4")
    run.add_argument("--no-resume", action="store_true", help="Ignora outputs/checkpoints existentes e recalcula")

    audit = sub.add_parser("audit", help="Audita repositorio e configuracao sem executar metricas")
    audit.add_argument("--config", required=True)
    args = parser.parse_args()

    if args.command == "run":
        out = run_project(args.config, args.output, workers=args.workers, resume=not args.no_resume)
        print(f"Pipeline concluida. Resultados em: {out}")
    elif args.command == "audit":
        cfg = load_config(args.config)
        clone_or_update(cfg)
        print(audit_project(cfg).to_string(index=False))


if __name__ == "__main__":
    main()
