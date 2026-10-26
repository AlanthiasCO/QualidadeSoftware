from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[1]

OLD_RESULTS = (
    ROOT
    / "results"
    / "final"
    / "v143"
    / "consolidado_rq3_estabilidade_v143.csv"
)
VLIBRAS_RESULTS = (
    ROOT
    / "outputs"
    / "vlibras_web_browsers"
    / "09_rq3_ranking_stability.csv"
)
OUTPUT_DIR = ROOT / "results" / "analise_sem_esus" / "rq1"

PROJECT_NAMES = {
    "novo_sgp": "Novo SGP",
    "sapl": "SAPL",
    "siga": "SIGA",
    "sigi": "SIGI",
    "vlibras_web_browsers": "VLibras Web Browsers",
}
EXPECTED_PROJECTS = set(PROJECT_NAMES)


def main() -> None:
    if not OLD_RESULTS.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {OLD_RESULTS}")
    if not VLIBRAS_RESULTS.is_file():
        raise FileNotFoundError(f"Arquivo não encontrado: {VLIBRAS_RESULTS}")

    # Mantém os quatro sistemas do estudo anterior e exclui o e-SUS.
    old = pd.read_csv(OLD_RESULTS)
    old = old[old["project_id"].isin({"novo_sgp", "sapl", "siga", "sigi"})].copy()

    # Inclui as transições calculadas para o VLibras.
    vlibras = pd.read_csv(VLIBRAS_RESULTS)
    vlibras["system_name"] = PROJECT_NAMES["vlibras_web_browsers"]

    data = pd.concat([old, vlibras], ignore_index=True)

    required_columns = {
        "project_id",
        "system_name",
        "year_a",
        "year_b",
        "shared_files",
        "rank_spearman",
    }
    missing_columns = required_columns - set(data.columns)
    if missing_columns:
        raise ValueError(f"Colunas ausentes nos CSVs: {sorted(missing_columns)}")

    found_projects = set(data["project_id"].dropna().astype(str))
    if found_projects != EXPECTED_PROJECTS:
        raise ValueError(
            "Conjunto de sistemas inesperado. "
            f"Esperado: {sorted(EXPECTED_PROJECTS)}; "
            f"encontrado: {sorted(found_projects)}"
        )

    if "painel_esus" in found_projects:
        raise ValueError("O e-SUS ainda está nos dados.")

    data["year_a"] = pd.to_numeric(data["year_a"], errors="raise").astype(int)
    data["year_b"] = pd.to_numeric(data["year_b"], errors="raise").astype(int)
    data["shared_files"] = pd.to_numeric(
        data["shared_files"], errors="raise"
    ).astype(int)
    data["rank_spearman"] = pd.to_numeric(
        data["rank_spearman"], errors="raise"
    )

    duplicate_keys = data.duplicated(
        subset=["project_id", "year_a", "year_b"], keep=False
    )
    if duplicate_keys.any():
        raise ValueError(
            "Há mais de uma linha para o mesmo sistema e transição anual."
        )

    data = data.sort_values(["project_id", "year_a", "year_b"]).copy()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    data_path = OUTPUT_DIR / "estabilidade_rq1_sem_esus.csv"
    data.to_csv(data_path, index=False, encoding="utf-8-sig")

    summary = (
        data.groupby(["project_id", "system_name"], as_index=False)
        .agg(
            transicoes=("rank_spearman", "count"),
            mediana_spearman=("rank_spearman", "median"),
            menor_spearman=("rank_spearman", "min"),
            maior_spearman=("rank_spearman", "max"),
            mediana_arquivos_compartilhados=("shared_files", "median"),
        )
        .sort_values("project_id")
    )

    summary_path = OUTPUT_DIR / "resumo_rq1_sem_esus.csv"
    summary.to_csv(summary_path, index=False, encoding="utf-8-sig")

    transitions = sorted(
        set(zip(data["year_a"].astype(int), data["year_b"].astype(int)))
    )
    x_position = {transition: index for index, transition in enumerate(transitions)}
    x_labels = [f"{year_a}–{year_b}" for year_a, year_b in transitions]

    fig, ax = plt.subplots(figsize=(12, 6))

    for system_name, group in data.groupby("system_name"):
        group = group.sort_values(["year_a", "year_b"])
        x_values = [
            x_position[(int(row.year_a), int(row.year_b))]
            for row in group.itertuples(index=False)
        ]
        y_values = group["rank_spearman"].tolist()

        ax.plot(x_values, y_values, marker="o", linewidth=1.8, label=system_name)

        # O rótulo n informa quantos arquivos aparecem nos dois snapshots.
        for x, row in zip(x_values, group.itertuples(index=False)):
            ax.annotate(
                f"n={int(row.shared_files)}",
                (x, row.rank_spearman),
                xytext=(0, 7),
                textcoords="offset points",
                ha="center",
                fontsize=7,
            )

    ax.set_xticks(range(len(transitions)))
    ax.set_xticklabels(x_labels, rotation=45, ha="right")
    ax.set_ylim(-1.05, 1.05)
    ax.set_xlabel("Transição entre snapshots")
    ax.set_ylabel("Spearman dos rankings H")
    ax.set_title("Estabilidade da prioridade H — escopo sem e-SUS")
    ax.grid(axis="y", alpha=0.3)
    ax.legend(title="Sistema")
    fig.tight_layout()

    figure_path = OUTPUT_DIR / "rq1_estabilidade_H_sem_esus.png"
    fig.savefig(figure_path, dpi=200)
    plt.close(fig)

          # Mapa de calor: estabilidade por sistema e transição anual.
    data["transicao"] = data.apply(
        lambda row: f"{int(row.year_a)}–{int(row.year_b)}",
        axis=1,
    )

    ordem_sistemas = [
        PROJECT_NAMES[project_id]
        for project_id in [
            "novo_sgp",
            "sapl",
            "siga",
            "sigi",
            "vlibras_web_browsers",
        ]
    ]
    ordem_transicoes = [
        f"{ano}–{ano + 1}" for ano in range(2020, 2026)
    ]

    tabela = data.pivot(
        index="system_name",
        columns="transicao",
        values="rank_spearman",
    ).reindex(index=ordem_sistemas, columns=ordem_transicoes)

    tamanhos = data.pivot(
        index="system_name",
        columns="transicao",
        values="shared_files",
    ).reindex(index=ordem_sistemas, columns=ordem_transicoes)

    valores = np.ma.masked_invalid(tabela.to_numpy(dtype=float))

    fig, ax = plt.subplots(figsize=(11, 5.5))
    imagem = ax.imshow(
        valores,
        cmap="RdYlGn",
        vmin=-1,
        vmax=1,
        aspect="auto",
    )

    ax.set_xticks(range(len(ordem_transicoes)))
    ax.set_xticklabels(ordem_transicoes)
    ax.set_yticks(range(len(ordem_sistemas)))
    ax.set_yticklabels(ordem_sistemas)
    ax.set_xlabel("Transição entre snapshots")
    ax.set_title("Estabilidade da prioridade H por sistema e transição")

    for linha in range(len(ordem_sistemas)):
        for coluna in range(len(ordem_transicoes)):
            valor = tabela.iloc[linha, coluna]
            n = tamanhos.iloc[linha, coluna]

            if pd.notna(valor):
                ax.text(
                    coluna,
                    linha,
                    f"ρ={valor:.2f}\nn={int(n)}",
                    ha="center",
                    va="center",
                    fontsize=8,
                )

    barra = fig.colorbar(imagem, ax=ax)
    barra.set_label("Correlação de Spearman (ρ)")

    fig.tight_layout()
    heatmap_path = OUTPUT_DIR / "rq1_heatmap_estabilidade_H_sem_esus.png"
    fig.savefig(heatmap_path, dpi=200)
    plt.close(fig)

    print(f"- {heatmap_path}")


    print("Arquivos gerados:")
    print(f"- {data_path}")
    print(f"- {summary_path}")
    print(f"- {figure_path}")
    print()
    print("Resumo por sistema:")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
  