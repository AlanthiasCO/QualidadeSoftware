from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import threading
import time
from datetime import timedelta
from pathlib import Path

EXPECTED = [
    ("00_audit.csv", "Auditoria do repositório"),
    ("01_snapshots.csv", "Construção dos snapshots anuais"),
    ("02_git_metrics.csv", "Mineração Git: Nmod e churn"),
    ("03_file_identity.csv", "Reconstrução de identidade/renomes"),
    ("04_static_metrics.csv", "Métricas estáticas: NLOC e CCN"),
    ("05_master_hotspots.csv", "Cálculo do ranking de hotspots"),
    ("06_rq1_gini.csv", "RQ1: concentração / Gini"),
    ("06b_rq1_lorenz_points.csv", "RQ1: curvas de Lorenz"),
    ("07_rq2_associations.csv", "RQ2: associações / Spearman"),
    ("08_rq3_longitudinal_files.csv", "RQ3: persistência longitudinal"),
    ("09_rq3_ranking_stability.csv", "RQ3: estabilidade entre snapshots"),
    ("10_rq4_comparison_pairs.csv", "RQ4: pareamento hotspot-controle"),
    ("11_rq4_qualitative_template.csv", "RQ4: template qualitativo"),
]

PROGRESS_RE = re.compile(r"^\[PROGRESS\]\s+(.*)$")


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def fmt_seconds(seconds: float) -> str:
    return str(timedelta(seconds=int(seconds)))


def infer_project_id(config: Path) -> str:
    try:
        for line in config.read_text(encoding="utf-8", errors="replace").splitlines():
            s = line.strip()
            if s.startswith("project_id:"):
                value = s.split(":", 1)[1].strip().strip('"\'')
                if value:
                    return value
    except Exception:
        pass
    return config.stem


def stage_state(out_dir: Path):
    existing = {p.name for p in out_dir.glob("*.csv")}
    completed = 0
    for name, _ in EXPECTED:
        if name in existing:
            completed += 1
        else:
            break
    current = "Concluído" if completed >= len(EXPECTED) else EXPECTED[completed][1]
    return existing, completed, current


def latest_file(out_dir: Path):
    files = list(out_dir.glob("*.csv"))
    return max(files, key=lambda p: p.stat().st_mtime) if files else None


def parse_progress(line: str):
    m = PROGRESS_RE.match(line.strip())
    if not m:
        return None
    data = {}
    for part in m.group(1).split():
        if "=" in part:
            k, v = part.split("=", 1)
            data[k] = v
    return data


def progress_bar(pct: float, width: int = 42) -> str:
    pct = max(0.0, min(100.0, pct))
    done = int(round(width * pct / 100.0))
    return "#" * done + "-" * (width - done)


def render(project: str, out_dir: Path, start: float, proc: subprocess.Popen, log_path: Path, inner_progress: dict):
    existing, completed, current = stage_state(out_dir)
    clear_screen()
    width = 84
    pct = completed / len(EXPECTED) * 100.0

    print("=" * width)
    print(" PIPELINE DE HOTSPOTS - MONITOR DE EXECUÇÃO v1.3")
    print("=" * width)
    print(f"Projeto       : {project}")
    print(f"Status        : {'RODANDO' if proc.poll() is None else 'FINALIZADO'}")
    print(f"Etapa atual   : {current}")
    print(f"Tempo total   : {fmt_seconds(time.time() - start)}")
    print(f"Etapas        : [{progress_bar(pct)}] {completed}/{len(EXPECTED)} ({pct:.1f}%)")
    print(f"Saída         : {out_dir}")
    print(f"Log           : {log_path}")

    if inner_progress:
        stage = inner_progress.get("stage", "")
        try:
            ipct = float(inner_progress.get("pct", "0"))
        except ValueError:
            ipct = 0.0
        print("\nPROGRESSO INTERNO")
        print("-" * width)
        print(f"Subetapa      : {stage}")
        print(f"Progresso     : [{progress_bar(ipct)}] {ipct:.2f}%")
        if stage == "git":
            print(f"Commits       : {inner_progress.get('commits','?')} / {inner_progress.get('total','?')}")
            print(f"Ano corrente  : {inner_progress.get('year','?')}")
            print(f"Eventos úteis : {inner_progress.get('events','?')}")
            print(f"Velocidade    : {inner_progress.get('rate','?')} commits/s")
            print(f"ETA estimado  : {inner_progress.get('eta','?')}")
        elif stage == "static":
            print(f"Arquivos      : {inner_progress.get('files','?')} / {inner_progress.get('total','?')}")
            print(f"Snapshot/ano  : {inner_progress.get('year','?')}")
            if "year_files" in inner_progress:
                print(f"No ano        : {inner_progress.get('year_files','?')} / {inner_progress.get('year_total','?')} ({inner_progress.get('year_pct','?')}%)")
            print(f"Velocidade    : {inner_progress.get('rate','?')} arquivos/s")
            print(f"ETA estimado  : {inner_progress.get('eta','?')}")

    print()
    lf = latest_file(out_dir)
    if lf:
        st = lf.stat()
        print(f"Último arquivo: {lf.name} ({st.st_size:,} bytes)")
        print(f"Atualizado em : {time.strftime('%H:%M:%S', time.localtime(st.st_mtime))}")
    else:
        print("Último arquivo: nenhum CSV concluído ainda")

    print("\nETAPAS")
    print("-" * width)
    for i, (name, desc) in enumerate(EXPECTED, 1):
        if name in existing:
            mark = "OK"
        elif i == completed + 1 and proc.poll() is None:
            mark = ">>"
        else:
            mark = ".."
        print(f"[{mark}] {i:02d}. {desc:<45} {name}")

    print("\n" + "-" * width)
    print("Ctrl+C interrompe a execução. O log permanece salvo.")


def stream_pipe(pipe, logf, tail_buffer, lock, inner_progress):
    try:
        for line in iter(pipe.readline, ""):
            if not line:
                break
            parsed = parse_progress(line)
            with lock:
                logf.write(line)
                logf.flush()
                if parsed:
                    inner_progress.clear()
                    inner_progress.update(parsed)
                else:
                    tail_buffer.append(line.rstrip("\n"))
                    if len(tail_buffer) > 40:
                        del tail_buffer[:-40]
    finally:
        try:
            pipe.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser(description="Executa 'hotspots run' com progresso interno e ETA.")
    ap.add_argument("--config", required=True, help="Ex.: configs/novo_sgp.yml")
    ap.add_argument("--output", default="outputs", help="Diretório base de saída")
    ap.add_argument("--clean", action="store_true", help="Apaga a pasta de saída do projeto antes de iniciar")
    ap.add_argument("--refresh", type=float, default=2.0, help="Intervalo de atualização em segundos")
    ap.add_argument("--workers", type=int, default=None, help="Processos paralelos para NLOC/CCN")
    ap.add_argument("--no-resume", action="store_true", help="Ignora cache/checkpoints e recalcula")
    args = ap.parse_args()

    config = Path(args.config)
    if not config.exists():
        print(f"ERRO: configuração não encontrada: {config}")
        return 2

    project = infer_project_id(config)
    out_dir = Path(args.output) / project
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.clean and out_dir.exists():
        shutil.rmtree(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    log_path = logs_dir / f"{project}_{stamp}.log"

    cmd = ["hotspots", "run", "--config", str(config), "--output", args.output]
    if args.workers is not None:
        cmd += ["--workers", str(args.workers)]
    if args.no_resume:
        cmd += ["--no-resume"]
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0

    start = time.time()
    tail_buffer = []
    inner_progress = {}
    lock = threading.Lock()

    with log_path.open("w", encoding="utf-8", errors="replace") as logf:
        logf.write("COMMAND: " + " ".join(cmd) + "\n\n")
        logf.flush()

        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=creationflags,
        )

        t1 = threading.Thread(target=stream_pipe, args=(proc.stdout, logf, tail_buffer, lock, inner_progress), daemon=True)
        t2 = threading.Thread(target=stream_pipe, args=(proc.stderr, logf, tail_buffer, lock, inner_progress), daemon=True)
        t1.start(); t2.start()

        try:
            while proc.poll() is None:
                with lock:
                    ip = dict(inner_progress)
                    recent = tail_buffer[-6:]
                render(project, out_dir, start, proc, log_path, ip)
                if recent:
                    print("\nÚLTIMAS MENSAGENS")
                    print("-" * 84)
                    for line in recent:
                        print(line[:220])
                time.sleep(max(args.refresh, 0.5))
        except KeyboardInterrupt:
            print("\nInterrompendo pipeline...")
            try:
                proc.terminate()
                proc.wait(timeout=10)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
            print(f"Execução interrompida. Log salvo em: {log_path}")
            return 130

        t1.join(timeout=2); t2.join(timeout=2)
        with lock:
            ip = dict(inner_progress)
        render(project, out_dir, start, proc, log_path, ip)

        rc = proc.returncode
        if rc == 0:
            print("\nPIPELINE CONCLUÍDA COM SUCESSO.")
        else:
            print(f"\nPIPELINE TERMINOU COM ERRO (código {rc}).")
            with lock:
                recent = tail_buffer[-15:]
            if recent:
                print("\nÚltimas mensagens:")
                for line in recent:
                    print(line)
        print(f"Log completo: {log_path}")
        return rc


if __name__ == "__main__":
    raise SystemExit(main())
