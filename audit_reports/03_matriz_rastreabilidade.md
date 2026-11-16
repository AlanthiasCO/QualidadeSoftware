# 03 — Matriz de rastreabilidade

## Paper → evidência versionada

| Afirmação/artefato do paper final | Evidência encontrada | Commit/versão | Estado |
|---|---|---|---|
| Pipeline quantitativa v1.4.3 | código, versão, testes, validação e recuperação | `15a5cd2`, complementado por `31d9612` | comprovado como implementação presente; não reexecutado |
| `H=min(R_N,R_C)` | `src/hotspots/scoring.py`, documentação e masters | v1.4.1 e v1.4.3 | comprovado |
| mediana de H por arquivo | `src/hotspots/rq3.py` e consolidados longitudinais | `e8639f9`/`31d9612` | comprovado |
| Novo SGP 2020–2026 | consolidado v1.4.3: 7 snapshots, 9.655 ids/50.840 observações | `31d9612` | comprovado; paper informa 9.637 arquivos, diferença não explicada |
| SAPL 2020–2026 | 7 snapshots, 239 arquivos/1.411 observações | `31d9612` | comprovado |
| SIGA 2020–2025 | 6 snapshots, 2.116 arquivos/10.895 observações | `31d9612` | comprovado; paper informa 2.115 arquivos |
| SIGI 2020–2026 | 7 snapshots, 299 arquivos/1.516 observações | `31d9612` | comprovado |
| VLibras 2020–2026 | config + outputs/validação; análise reporta 398 arquivos/447 observações | `03cd48a`, resumido em `9436e0e` e paper de referência | parcialmente comprovado; master bruto não foi versionado nesta branch |
| Spearman 0,822; 0,927; 0,910; 0,929; 0,854 | `results/analise_sem_esus/rq1/resumo_rq1_sem_esus.csv` | `9436e0e` | comprovado numericamente |
| transições válidas 6/6/5/6/5 | CSV detalhado; VLibras 2025–2026 existe como linha vazia e não conta | `9436e0e` | comprovado |
| 25 pares, cinco por sistema definitivo | `amostra_pares_congelada.csv`/`rq4_avaliacao.csv` | `9436e0e` | comprovado |
| 7/25 prioritários, 3/25 controles, p=0,289 | tabelas em `pmd/paper/paper_original.md`, `paper_checkpoint.tex` e `paper_reference/paper.tex` | paper; números aparecem em arquivos rastreados anteriores | resultado declarado, mas planilha-fonte não preenchida; não comprovado por dados de avaliação |
| estática: 20 classificados, 5/10/5, p=0,302; VLibras ausente | apenas `paper_reference/paper.tex` | não rastreado | não comprovado por dataset versionado |
| empate C# apesar de build falhar | `pmd/CHECKPOINT.md` e `resultado_rq3_50_arquivos.json`: `ServicoEOL.cs`, restore 0/build 1, zero ocorrências | `979a5d8`/main | ocorrência comprovada, mas pertence ao resultado antigo 9/11/5 com Painel e-SUS |

## Tabelas do paper

- Tabela de corpus: parcialmente sustentada por `results/final/v143/consolidado_casos_v143.csv` mais artefatos de VLibras. O consolidado ainda contém Painel e-SUS.
- Tabela RQ1 (arquivos exemplares): os quatro caminhos antigos estão nos pares/consolidados; `plugin/Plugin.js` está na amostra definitiva. Há discrepância no H de VLibras: amostra versionada `0,921538...`, paper `0,898`.
- Tabela RQ2: sustentada diretamente pelos CSVs de `9436e0e`.
- Tabela RQ3 contextual: sustentada somente por texto/tabela do manuscrito; as quatro planilhas de avaliação de `9436e0e` são cópias idênticas e vazias nos campos de evidência/classificação.
- Tabela de análise estática: o dataset rastreado em `pmd/results/` classifica 25 pares do corpus antigo, com 9 hotspots, 11 controles, 5 empates, p=0,823803. Não sustenta 5/10/5 nem a exclusão dos cinco pares de VLibras.

## Manifestos, rankings e snapshots

- v1.4.1: `metadata/freeze_manifest.csv`, `results/final/*_v141*`, masters, rankings e figuras para Novo SGP, SAPL, SIGA, SIGI e Painel e-SUS.
- v1.4.3 antigo: `results/final/v143/manifest.json`, `SHA256SUMS`, master e tabelas consolidadas; ainda lista os cinco sistemas antigos.
- validação v1.4.3: `results/validation/v1.4.3/<sistema>/` para quatro sistemas antigos + Painel em `31d9612`, e VLibras em `03cd48a`.
- corpus definitivo: estabilidade e amostra pareada em `results/analise_sem_esus/` (`9436e0e`). Não existe manifesto geral definitivo que substitua Painel por VLibras em todos os artefatos.

## Proveniência do paper

`main` contém somente `v_0.5_paper.zip` no commit `71f1a73`. O arquivo `paper_reference/paper.tex` é não rastreado, mas corresponde exatamente à referência científica fornecida pelo solicitante e explicita os resultados finais. Foi usado como alvo de comparação, não como prova de execução.
