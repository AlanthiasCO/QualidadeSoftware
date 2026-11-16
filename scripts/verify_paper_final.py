from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINAL = ROOT / "results" / "paper_final"
EXPECTED = {
    "novo_sgp": (0.8220012088179401, 6),
    "sapl": (0.9269016349852861, 6),
    "siga": (0.910400847822073, 5),
    "sigi": (0.9289005044257124, 6),
    "vlibras_web_browsers": (0.8535852484575346, 5),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    manifest = json.loads((FINAL / "manifest.json").read_text(encoding="utf-8"))
    require(manifest["pipeline_version"] == "1.4.3", "pipeline diferente de 1.4.3")
    require(set(manifest["corpus"]) == set(EXPECTED), "corpus final incorreto")
    require("painel_esus" not in manifest["corpus"], "Painel e-SUS no corpus final")

    paper = (ROOT / "paper_reference" / "paper.tex").read_text(encoding="utf-8")
    paper_claims = [
        "Longitudinal Analysis of Hotspots in Brazilian Public Software",
        "v1.4.3",
        "7 dos 25 arquivos de alta prioridade",
        "3 dos 25 controles",
        "p=0{,}289",
        "em cinco pares, o arquivo de alta prioridade",
        "em dez, a maior densidade",
        "cinco pares resultaram em empate",
        "p=0{,}302",
    ]
    for claim in paper_claims:
        require(claim in paper, f"afirmação não encontrada no paper: {claim}")

    source_stability = {
        row["project_id"]: row
        for row in read_csv(
            ROOT / "results" / "analise_sem_esus" / "rq1" / "resumo_rq1_sem_esus.csv"
        )
    }
    final_stability = {
        row["project_id"]: row for row in read_csv(FINAL / "rq2_stability_final.csv")
    }
    require(set(source_stability) == set(EXPECTED), "fonte de estabilidade com corpus incorreto")
    require(set(final_stability) == set(EXPECTED), "consolidado de estabilidade incompleto")
    for project, (expected_median, expected_transitions) in EXPECTED.items():
        source = source_stability[project]
        final = final_stability[project]
        require(abs(float(source["mediana_spearman"]) - expected_median) < 1e-12, f"mediana divergente: {project}")
        require(int(source["transicoes"]) == expected_transitions, f"transições divergentes: {project}")
        require(abs(float(final["median_spearman"]) - expected_median) < 1e-12, f"mediana final divergente: {project}")

    sample = read_csv(
        ROOT / "results" / "analise_sem_esus" / "rq4" / "amostra_pares_congelada.csv"
    )
    require(len(sample) == 50, "amostra final não contém 50 arquivos")
    pairs: dict[str, set[str]] = {}
    projects: dict[str, set[str]] = {}
    for row in sample:
        pairs.setdefault(row["pair_id"], set()).add(row["group"])
        projects.setdefault(row["project_id"], set()).add(row["pair_id"])
    require(len(pairs) == 25, "amostra final não contém 25 pares")
    require(all(groups == {"hotspot", "control"} for groups in pairs.values()), "par incompleto")
    require(set(projects) == set(EXPECTED), "sistemas incorretos na amostra")
    require(all(len(project_pairs) == 5 for project_pairs in projects.values()), "não há cinco pares por sistema")

    contextual = read_csv(FINAL / "rq3_contextual_final.csv")[-1]
    require((contextual["priority_with_evidence"], contextual["control_with_evidence"]) == ("7", "3"), "totais contextuais incorretos")
    static = read_csv(FINAL / "static_analysis_final.csv")[-1]
    require((static["hotspot_higher"], static["control_higher"], static["ties"]) == ("5", "10", "5"), "totais estáticos incorretos")
    require((static["classified_pairs"], static["unclassified_pairs"]) == ("20", "5"), "cobertura estática incorreta")

    evaluation = read_csv(
        ROOT / "results" / "analise_sem_esus" / "rq4" / "rq4_avaliacao.csv"
    )
    completed = sum(bool(row.get("consensus_class", "").strip()) for row in evaluation)
    require(completed == 0, "avaliações apareceram preenchidas; revisar a proveniência")

    old_manifest = json.loads(
        (ROOT / "results" / "final" / "v143" / "manifest.json").read_text(encoding="utf-8")
    )
    require("painel_esus" in old_manifest["projects"], "manifesto histórico mudou inesperadamente")
    require("vlibras_web_browsers" not in old_manifest["projects"], "manifesto histórico deixou de representar o corpus antigo")

    print(json.dumps({
        "status": "paper_faithful_with_known_gaps",
        "pipeline_version": "1.4.3",
        "systems": len(EXPECTED),
        "verified_stability_medians": len(EXPECTED),
        "verified_pairs": len(pairs),
        "contextual_classifications_in_versioned_sheet": completed,
        "full_reproduction_verified": False,
    }, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
