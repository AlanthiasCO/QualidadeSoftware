from __future__ import annotations

import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"
DEST = ROOT / "results" / "final" / "v143"
FIGURES = DEST / "figures"
PROJECTS = ["novo_sgp", "sapl", "siga", "sigi", "painel_esus"]
NAMES = {
    "novo_sgp": "Novo SGP", "sapl": "SAPL", "siga": "SIGA",
    "sigi": "SIGI", "painel_esus": "Painel e-SUS APS",
}


def read_all(filename: str) -> pd.DataFrame:
    frames = []
    for project in PROJECTS:
        path = OUTPUTS / project / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        frame = pd.read_csv(path)
        frame["system_name"] = NAMES[project]
        frames.append(frame)
    return pd.concat(frames, ignore_index=True)


def write_csv(frame: pd.DataFrame, filename: str) -> Path:
    path = DEST / filename
    frame.to_csv(path, index=False)
    return path


def case_summary(audit: pd.DataFrame, master: pd.DataFrame) -> pd.DataFrame:
    derived = master.groupby("project_id").agg(
        snapshots=("year", "nunique"), first_snapshot=("year", "min"),
        last_snapshot=("year", "max"), unique_files=("file_id", "nunique"),
        observations=("file_id", "size"),
    ).reset_index()
    columns = [
        "project_id", "name", "branch", "freeze_sha", "freeze_date",
        "commits_since_start_year", "authors_since_start_year", "files_at_freeze",
        "included_first_party_files_at_freeze", "included_file_pct", "extensions",
    ]
    return audit[columns].merge(derived, on="project_id", how="left")


def summaries(rq1: pd.DataFrame, rq2: pd.DataFrame, stability: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    rq1_summary = rq1.groupby(["project_id", "system_name", "metric"])["gini"].agg(
        median="median", minimum="min", maximum="max"
    ).reset_index()
    rq2_summary = rq2.groupby(["project_id", "system_name", "relation"], dropna=False).agg(
        median_spearman=("spearman_rho", "median"),
        median_partial_spearman=("partial_spearman_rho_control_nloc", "median"),
        valid_snapshots=("spearman_rho", "count"),
    ).reset_index()
    rq3_summary = stability.groupby(["project_id", "system_name"]).agg(
        median_rank_spearman=("rank_spearman", "median"),
        minimum_rank_spearman=("rank_spearman", "min"),
        maximum_rank_spearman=("rank_spearman", "max"),
        transitions=("rank_spearman", "count"),
    ).reset_index()
    return rq1_summary, rq2_summary, rq3_summary


def pair_wide(pairs: pd.DataFrame) -> pd.DataFrame:
    index = ["pair_id", "project_id", "system_name", "language", "matched_distance"]
    values = ["file_id", "path", "h_median", "nloc_median", "snapshots"]
    wide = pairs.pivot(index=index, columns="group", values=values).reset_index()
    wide.columns = [
        "_".join(str(part) for part in col if part).strip("_")
        if isinstance(col, tuple) else col for col in wide.columns
    ]
    return wide


def comparison_report(current: dict[str, pd.DataFrame], pairs_wide: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    specs = [
        ("rq1", "consolidado_rq1_detalhe_v141.csv", ["project_id", "year", "metric"], ["gini"]),
        ("rq2", "consolidado_rq2_detalhe_v141.csv", ["project_id", "year", "relation"], ["spearman_rho", "partial_spearman_rho_control_nloc"]),
        ("rq3", "consolidado_rq3_estabilidade_v141.csv", ["project_id", "year_a", "year_b"], ["rank_spearman"]),
    ]
    rows = []
    for label, old_name, keys, metrics in specs:
        old = pd.read_csv(ROOT / "results" / "final" / old_name)
        new = current[label]
        merged = old.merge(new, on=keys, how="outer", suffixes=("_v141", "_v143"), indicator=True)
        for metric in metrics:
            both = merged[merged["_merge"] == "both"].copy()
            delta = pd.to_numeric(both[f"{metric}_v143"], errors="coerce") - pd.to_numeric(
                both[f"{metric}_v141"], errors="coerce"
            )
            changed = (~np.isclose(delta.fillna(0), 0, atol=1e-12)) & ~(both[f"{metric}_v141"].isna() & both[f"{metric}_v143"].isna())
            rows.append({
                "analysis": label, "metric": metric, "old_rows": len(old),
                "new_rows": len(new), "matched_rows": len(both),
                "changed_rows": int(changed.sum()),
                "max_absolute_difference": float(delta.abs().max()) if delta.notna().any() else 0.0,
            })

    old_pairs = pd.read_csv(ROOT / "results" / "final" / "consolidado_rq4_amostra_v141.csv")
    old_set = set(zip(old_pairs["project_id"], old_pairs["high_path"], old_pairs["control_path"]))
    new_set = set(zip(pairs_wide["project_id"], pairs_wide["path_hotspot"], pairs_wide["path_control"]))
    text = "\n".join([
        "# Comparação v1.4.1 × v1.4.3", "",
        "A comparação usa chaves equivalentes e tolerância numérica de 1e-12.", "",
        f"- Pares preservados: {len(old_set & new_set)}/25",
        f"- Pares novos ou alterados: {len(new_set - old_set)}",
        f"- Pares antigos não preservados: {len(old_set - new_set)}",
        "", "Os detalhes numéricos estão em `comparacao_v141_v143.csv`.", "",
    ])
    return pd.DataFrame(rows), text


def figures(rq1: pd.DataFrame, rq2: pd.DataFrame, stability: pd.DataFrame, pairs: pd.DataFrame) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    for metric in ["nmod", "churn", "ccn"]:
        fig, ax = plt.subplots(figsize=(8, 4.5))
        subset = rq1[rq1["metric"] == metric]
        for name, group in subset.groupby("system_name"):
            ax.plot(group["year"], group["gini"], marker="o", label=name)
        ax.set(title=f"Concentração longitudinal — Gini de {metric.upper()}", xlabel="Ano", ylabel="Coeficiente de Gini", ylim=(0, 1))
        ax.legend(fontsize=8, ncol=2)
        fig.tight_layout()
        fig.savefig(FIGURES / f"rq1_gini_{metric}_v143.png", dpi=180)
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    subset = rq2[rq2["relation"] == "nmod_vs_ccn"]
    for name, group in subset.groupby("system_name"):
        ax.plot(group["year"], group["partial_spearman_rho_control_nloc"], marker="o", label=name)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set(title="Associação parcial Nmod × CCN controlando NLOC", xlabel="Ano", ylabel="Spearman parcial", ylim=(-1, 1))
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(FIGURES / "rq2_partial_nmod_ccn_v143.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for name, group in stability.groupby("system_name"):
        ax.plot(group["year_b"], group["rank_spearman"], marker="o", label=name)
    ax.set(title="Estabilidade do ranking H entre snapshots", xlabel="Ano final da transição", ylabel="Spearman", ylim=(-1, 1))
    ax.legend(fontsize=8, ncol=2)
    fig.tight_layout()
    fig.savefig(FIGURES / "rq3_ranking_stability_v143.png", dpi=180)
    plt.close(fig)

    wide = pair_wide(pairs).sort_values(["project_id", "pair_id"])
    fig, ax = plt.subplots(figsize=(9, 7))
    y = np.arange(len(wide))
    for pos, row in enumerate(wide.itertuples(index=False)):
        ax.plot([row.h_median_control, row.h_median_hotspot], [pos, pos], color="#9aa0a6", linewidth=1)
    ax.scatter(wide["h_median_control"], y, label="Controle", s=28)
    ax.scatter(wide["h_median_hotspot"], y, label="Hotspot", s=28)
    ax.set(title="Escore H mediano nos 25 pares", xlabel="H mediano", ylabel="Par", yticks=y, yticklabels=wide["pair_id"], xlim=(0, 1))
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES / "rq4_pairs_h_v143.png", dpi=180)
    plt.close(fig)


def checksums(paths: list[Path]) -> None:
    lines = []
    for path in sorted(paths):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(DEST)}")
    (DEST / "SHA256SUMS").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    audit = read_all("00_audit.csv")
    master = read_all("05_master_hotspots.csv")
    rq1 = read_all("06_rq1_gini.csv")
    rq2 = read_all("07_rq2_associations.csv")
    longitudinal = read_all("08_rq3_longitudinal_files.csv")
    stability = read_all("09_rq3_ranking_stability.csv")
    pairs = read_all("10_rq4_static_analysis_pairs.csv")
    cases = case_summary(audit, master)
    rq1_summary, rq2_summary, rq3_summary = summaries(rq1, rq2, stability)
    pairs_wide = pair_wide(pairs)

    written = [
        write_csv(cases, "consolidado_casos_v143.csv"),
        write_csv(master, "consolidado_master_v143.csv"),
        write_csv(rq1, "consolidado_rq1_detalhe_v143.csv"),
        write_csv(rq1_summary, "consolidado_rq1_resumo_v143.csv"),
        write_csv(rq2, "consolidado_rq2_detalhe_v143.csv"),
        write_csv(rq2_summary, "consolidado_rq2_resumo_v143.csv"),
        write_csv(longitudinal, "consolidado_rq3_longitudinal_v143.csv"),
        write_csv(stability, "consolidado_rq3_estabilidade_v143.csv"),
        write_csv(rq3_summary, "consolidado_rq3_resumo_v143.csv"),
        write_csv(pairs, "consolidado_rq4_pares_long_v143.csv"),
        write_csv(pairs_wide, "consolidado_rq4_pares_v143.csv"),
    ]
    comparison, comparison_text = comparison_report({"rq1": rq1, "rq2": rq2, "rq3": stability}, pairs_wide)
    written.append(write_csv(comparison, "comparacao_v141_v143.csv"))
    comparison_path = DEST / "RELATORIO_COMPARACAO.md"
    comparison_path.write_text(comparison_text, encoding="utf-8")
    written.append(comparison_path)
    figures(rq1, rq2, stability, pairs)
    figure_paths = sorted(FIGURES.glob("*.png"))
    manifest = {
        "pipeline_version": "1.4.3", "projects": PROJECTS,
        "master_observations": len(master), "unique_files": int(master["file_id"].nunique()),
        "pairs": int(pairs["pair_id"].nunique()), "pair_files": len(pairs),
        "generated_files": [str(path.relative_to(DEST)) for path in written + figure_paths],
    }
    manifest_path = DEST / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    checksums(written + figure_paths + [manifest_path])
    print(json.dumps(manifest, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
