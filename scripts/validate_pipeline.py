from __future__ import annotations

import argparse
import csv
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

import lizard
import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and p.returncode != 0:
        raise RuntimeError(f"Comando falhou ({p.returncode}): {' '.join(cmd)}\n{p.stderr.strip()}")
    return p


def git(repo: Path, *args: str, check: bool = True) -> str:
    return run(["git", "-C", str(repo), *args], check=check).stdout.strip()


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def ensure_columns(df: pd.DataFrame, cols: list[str], file: Path) -> None:
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise RuntimeError(f"{file} nao possui as colunas esperadas: {missing}")


def parse_git_log_numstat(text: str) -> tuple[int, int, int]:
    commits: set[str] = set()
    added = 0
    deleted = 0
    current_commit: str | None = None
    for line in text.splitlines():
        if line.startswith("@@COMMIT@@"):
            current_commit = line.replace("@@COMMIT@@", "", 1).strip() or None
            continue
        parts = line.split("\t")
        if len(parts) >= 3 and current_commit is not None:
            a, d = parts[0], parts[1]
            # Binary entries use non-numeric markers (normally "-") and do not
            # provide line churn. Only a numeric numstat line proves that the
            # sampled identity was modified by this commit.
            if a.isdigit() and d.isdigit():
                commits.add(current_commit)
                added += int(a)
                deleted += int(d)
    return len(commits), added, deleted


def identity_aliases(
    identity: pd.DataFrame,
    file_id: str,
    current_path: str,
) -> list[str]:
    """Return deterministic aliases approved by the conservative identity map."""
    aliases: set[str] = set()
    if not identity.empty and {"file_id", "path"}.issubset(identity.columns):
        matched = identity[identity["file_id"].astype(str) == str(file_id)]
        aliases.update(
            path.strip()
            for path in matched["path"].dropna().astype(str)
            if path.strip()
        )
    if not aliases:
        aliases.add(current_path)
    return sorted(aliases)


def recompute_git_metrics(
    repo: Path,
    paths: list[str],
    start_iso: str,
    end_iso: str,
    freeze_sha: str,
) -> tuple[int, int, int, int]:
    aliases = sorted({path for path in paths if path})
    if not aliases:
        raise ValueError("A consulta Git exige pelo menos um caminho de identidade")
    out = git(
        repo,
        "log",
        freeze_sha,
        "--full-history",
        f"--since={start_iso}",
        f"--until={end_iso}",
        "--format=@@COMMIT@@%H",
        "--numstat",
        "--",
        *aliases,
    )
    nmod, added, deleted = parse_git_log_numstat(out)
    return nmod, added, deleted, added + deleted


def read_file_at(repo: Path, sha: str, path: str) -> str | None:
    p = subprocess.run(
        ["git", "-C", str(repo), "show", f"{sha}:{path}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    if p.returncode != 0:
        return None
    try:
        return p.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return p.stdout.decode("utf-8", errors="replace")


def recompute_static(repo: Path, sha: str, path: str) -> tuple[int | None, int | None]:
    source = read_file_at(repo, sha, path)
    if source is None:
        return None, None
    try:
        info = lizard.analyze_file.analyze_source_code(path, source)
        ccn = sum(int(fn.cyclomatic_complexity) for fn in info.function_list)
        nloc = int(info.nloc)
        return nloc, ccn
    except Exception:
        return None, None


def sample_rows(master: pd.DataFrame, years: list[int], per_year: int = 3) -> pd.DataFrame:
    picked: list[pd.DataFrame] = []
    available_years = sorted(master["year"].dropna().astype(int).unique())
    selected_years = [y for y in years if y in available_years]
    if not selected_years:
        if len(available_years) <= 3:
            selected_years = available_years
        else:
            selected_years = [available_years[1], available_years[len(available_years)//2], available_years[-2]]

    for year in selected_years:
        g = master[master["year"] == year].copy()
        if g.empty:
            continue
        active = g[g["nmod"] > 0].copy()
        base = active if len(active) >= per_year else g
        base = base.sort_values("h")
        if len(base) == 1:
            sel = base.iloc[[0]]
        elif len(base) == 2:
            sel = base.iloc[[0, 1]]
        else:
            idxs = [0, len(base)//2, len(base)-1]
            sel = base.iloc[idxs[:per_year]]
        picked.append(sel)
    if not picked:
        return master.head(0).copy()
    return pd.concat(picked, ignore_index=True).drop_duplicates(subset=["year", "file_id"])


def previous_window_start(snapshots: pd.DataFrame, year: int, start_year: int) -> str:
    snaps = snapshots.sort_values("year").reset_index(drop=True)
    pos = snaps.index[snaps["year"].astype(int) == int(year)]
    if len(pos) == 0:
        return f"{start_year}-01-01T00:00:00+00:00"
    i = int(pos[0])
    if i == 0:
        return f"{start_year}-01-01T00:00:00+00:00"
    prev = pd.to_datetime(snaps.iloc[i - 1]["snapshot_date"], utc=True) + pd.Timedelta(seconds=1)
    return prev.isoformat()


def validate_rows(
    master: pd.DataFrame,
    snapshots: pd.DataFrame,
    identity: pd.DataFrame,
    repo: Path,
    freeze_sha: str,
    start_year: int,
    sample_years: list[int],
) -> pd.DataFrame:
    sample = sample_rows(master, sample_years, per_year=3)
    rows: list[dict[str, Any]] = []
    snap_by_year = snapshots.set_index(snapshots["year"].astype(int))

    for _, r in sample.iterrows():
        year = int(r["year"])
        if year not in snap_by_year.index:
            continue
        snap = snap_by_year.loc[year]
        sha = str(snap["sha"])
        end_iso = pd.to_datetime(snap["snapshot_date"], utc=True).isoformat()
        start_iso = previous_window_start(snapshots, year, start_year)
        path = str(r["path"])
        aliases = identity_aliases(identity, str(r["file_id"]), path)

        try:
            gnmod, gadd, gdel, gchurn = recompute_git_metrics(
                repo,
                aliases,
                start_iso,
                end_iso,
                freeze_sha,
            )
            git_error = ""
        except Exception as e:
            gnmod = gadd = gdel = gchurn = None
            git_error = str(e)

        lnloc, lccn = recompute_static(repo, sha, path)

        pnmod = int(r["nmod"])
        padd = int(r.get("added", 0))
        pdel = int(r.get("deleted", 0))
        pchurn = int(r["churn"])
        pnloc = int(r["nloc"])
        pccn = int(r["ccn"])

        rows.append({
            "year": year,
            "file_id": r["file_id"],
            "path": path,
            "git_paths": ";".join(aliases),
            "h": float(r["h"]),
            "window_start": start_iso,
            "window_end": end_iso,
            "pipeline_nmod": pnmod,
            "git_nmod": gnmod,
            "nmod_match": (gnmod == pnmod) if gnmod is not None else False,
            "pipeline_added": padd,
            "git_added": gadd,
            "added_match": (gadd == padd) if gadd is not None else False,
            "pipeline_deleted": pdel,
            "git_deleted": gdel,
            "deleted_match": (gdel == pdel) if gdel is not None else False,
            "pipeline_churn": pchurn,
            "git_churn": gchurn,
            "churn_match": (gchurn == pchurn) if gchurn is not None else False,
            "pipeline_nloc": pnloc,
            "lizard_nloc": lnloc,
            "nloc_match": (lnloc == pnloc) if lnloc is not None else False,
            "pipeline_ccn": pccn,
            "lizard_ccn": lccn,
            "ccn_match": (lccn == pccn) if lccn is not None else False,
            "git_error": git_error,
        })
    return pd.DataFrame(rows)


def sensitivity(master: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    df = master.copy()
    all_rows = []
    rankings = []
    for (project, language, year), g in df.groupby(["project_id", "language", "year"]):
        g = g.copy()
        active = g[g["nmod"] > 0].copy()
        if active.empty:
            continue
        active["r_nmod_active"] = active["nmod"].rank(method="average", pct=True)
        active["r_ccn_active"] = active["ccn"].rank(method="average", pct=True)
        active["h_active"] = active[["r_nmod_active", "r_ccn_active"]].min(axis=1)
        common = g.merge(active[["file_id", "h_active"]], on="file_id", how="inner", suffixes=("", "_x"))
        if len(common) >= 2:
            rho = spearmanr(common["h"], common["h_active"]).statistic
        else:
            rho = np.nan
        top_n = max(1, math.ceil(len(active) * 0.10))
        top_all = set(common.nlargest(top_n, "h")["file_id"])
        top_active = set(common.nlargest(top_n, "h_active")["file_id"])
        overlap = len(top_all & top_active) / max(1, len(top_all | top_active))
        all_rows.append({
            "project_id": project,
            "language": language,
            "year": int(year),
            "files_all": len(g),
            "files_active": len(active),
            "active_pct": len(active) / len(g) if len(g) else np.nan,
            "spearman_h_all_vs_active": rho,
            "top10_jaccard": overlap,
        })
        tmp = common[["project_id", "language", "year", "file_id", "path", "nmod", "ccn", "h", "h_active"]].copy()
        rankings.append(tmp)
    summary = pd.DataFrame(all_rows)
    detail = pd.concat(rankings, ignore_index=True) if rankings else pd.DataFrame()
    return summary, detail


def write_summary(path: Path, project: str, details: pd.DataFrame, sens: pd.DataFrame, repo: Path, freeze_sha: str) -> None:
    checks = ["nmod_match", "churn_match", "nloc_match", "ccn_match"]
    lines = [
        f"VALIDACAO DA PIPELINE - {project}",
        "=" * 72,
        f"Repositorio: {repo}",
        f"Freeze SHA: {freeze_sha}",
        f"Amostras auditadas: {len(details)}",
        "",
        "CHECAGENS INDEPENDENTES",
    ]
    for c in checks:
        if c in details.columns and len(details):
            n = int(details[c].fillna(False).sum())
            lines.append(f"- {c}: {n}/{len(details)} ({(100*n/len(details)):.1f}%)")
    if len(details):
        exact_all = details[checks].fillna(False).all(axis=1)
        lines.append(f"- linhas com Nmod+churn+NLOC+CCN todos coincidentes: {int(exact_all.sum())}/{len(details)}")
    lines += ["", "SENSIBILIDADE: TODOS OS ARQUIVOS vs SOMENTE Nmod>0"]
    if sens.empty:
        lines.append("- Sem dados suficientes.")
    else:
        for _, r in sens.sort_values("year").iterrows():
            rho = r["spearman_h_all_vs_active"]
            rho_txt = "NA" if pd.isna(rho) else f"{rho:.4f}"
            lines.append(
                f"- {int(r['year'])}: ativos {int(r['files_active'])}/{int(r['files_all'])} "
                f"({100*r['active_pct']:.1f}%), Spearman={rho_txt}, top10 Jaccard={r['top10_jaccard']:.4f}"
            )
    lines += [
        "",
        "INTERPRETACAO",
        "- As janelas historicas usam inicio exclusivo e fim inclusivo: (snapshot anterior, snapshot atual].",
        "- O commit que forma o snapshot anterior nao e recontado na janela seguinte.",
        "- A validacao Git consulta o historico completo (--full-history) dos aliases explicitos aprovados pelo mapa conservador de identidades, sem usar --follow.",
        "- NLOC/CCN devem coincidir exatamente, pois sao recalculados no mesmo SHA com Lizard.",
        "- A analise de sensibilidade nao substitui o cenario principal; ela testa se a massa de Nmod=0 altera o ranking.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Valida independentemente a pipeline de hotspots e gera analise de sensibilidade.")
    ap.add_argument("--project", default="sapl", help="ID do projeto (padrao: sapl)")
    ap.add_argument("--config", default=None, help="YAML; padrao configs/<project>.yml")
    ap.add_argument("--outputs", default="outputs", help="Raiz dos outputs (padrao: outputs)")
    ap.add_argument("--validation", default="validation", help="Raiz dos relatorios de validacao")
    ap.add_argument("--years", nargs="*", type=int, default=[2021, 2023, 2025], help="Anos amostrados")
    args = ap.parse_args()

    root = Path.cwd()
    config_path = root / (args.config or f"configs/{args.project}.yml")
    cfg = load_yaml(config_path)
    project_id = cfg["project_id"]
    repo = root / cfg["local_path"]
    out = root / args.outputs / project_id
    val = root / args.validation / project_id
    val.mkdir(parents=True, exist_ok=True)

    master_file = out / "05_master_hotspots.csv"
    snap_file = out / "01_snapshots.csv"
    audit_file = out / "00_audit.csv"
    identity_file = out / "03_file_identity.csv"
    for f in [master_file, snap_file, audit_file, identity_file]:
        if not f.exists():
            raise SystemExit(f"Arquivo necessario nao encontrado: {f}")
    if not repo.exists():
        raise SystemExit(f"Repositorio local nao encontrado: {repo}")

    master = pd.read_csv(master_file)
    snapshots = pd.read_csv(snap_file)
    audit = pd.read_csv(audit_file)
    identity = pd.read_csv(identity_file)
    ensure_columns(master, ["project_id", "year", "file_id", "path", "language", "nmod", "churn", "nloc", "ccn", "h"], master_file)
    ensure_columns(snapshots, ["year", "sha", "snapshot_date"], snap_file)
    ensure_columns(identity, ["project_id", "path", "file_id"], identity_file)

    freeze_sha = str(audit.iloc[0].get("freeze_sha", "")).strip() if not audit.empty else ""
    if not freeze_sha or freeze_sha.lower() == "nan":
        freeze_sha = str(cfg.get("freeze_sha") or "")
    if not freeze_sha:
        freeze_sha = git(repo, "rev-parse", f"origin/{cfg['branch']}")

    print(f"[1/4] Validando amostra Git e Lizard para {project_id}...")
    details = validate_rows(
        master,
        snapshots,
        identity,
        repo,
        freeze_sha,
        int(cfg.get("start_year", 2020)),
        args.years,
    )
    details.to_csv(val / "validation_details.csv", index=False, encoding="utf-8-sig")

    print("[2/4] Calculando sensibilidade H(all files) vs H(active files)...")
    sens, sens_detail = sensitivity(master)
    sens.to_csv(val / "sensitivity_summary.csv", index=False, encoding="utf-8-sig")
    sens_detail.to_csv(val / "sensitivity_rankings.csv", index=False, encoding="utf-8-sig")

    print("[3/4] Gerando resumo...")
    write_summary(val / "validation_summary.txt", project_id, details, sens, repo, freeze_sha)

    print("[4/4] Concluido.")
    print(f"Relatorios: {val}")
    print(f"- {val / 'validation_summary.txt'}")
    print(f"- {val / 'validation_details.csv'}")
    print(f"- {val / 'sensitivity_summary.csv'}")
    print(f"- {val / 'sensitivity_rankings.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
