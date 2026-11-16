# 05 — Plano de consolidação (não executado)

## Branch candidata

Usar `origin/docs-analises` (`9436e0e`) como base técnica da futura branch final, não `main`. Ela contém toda a ancestralidade v1.4.3, VLibras, medianas definitivas e amostra definitiva. Trazer de `main` apenas o paper que for confirmado como final (`v_0.5_paper.zip` e/ou fonte reconciliada), evitando sobrescrever código e resultados com a baseline v1.4.1.

## Conteúdo a incorporar/preservar

1. Correções e testes dos commits `e8639f9`, `15a5cd2` e `31d9612`.
2. Configuração e validação VLibras de `03cd48a`.
3. CSVs/gráficos/amostra de `9436e0e`.
4. Artefatos antigos v1.4.1 e Painel e-SUS em área claramente arquivada, sem apresentá-los como resultado final.
5. Manuscrito final somente após resolver sua proveniência e as divergências numéricas.

## Trabalho necessário antes de declarar consolidação/reprodução

1. Criar uma nova branch a partir de `9436e0e` (ação futura, não realizada).
2. Atualizar a consolidação para a lista definitiva de cinco sistemas e gerar manifesto/checksums novos; não editar silenciosamente o consolidado antigo.
3. Versionar os outputs brutos/mínimos de VLibras necessários para reconstruir master, ranking e pares.
4. Reconciliar regras de pareamento (primeiro ano versus quantidade de snapshots) com o método do paper e congelar uma única amostra versionada.
5. Recuperar ou refazer, com protocolo documentado, as avaliações contextuais; versionar decisões, referências e consenso que produzam 7/25 e 3/25.
6. Recuperar o dataset estático final de 20 pares ou reexecutar as ferramentas para a amostra definitiva. Registrar os cinco VLibras como não classificados e o caso C# como falha/inconclusivo, nunca como ausência automática.
7. Executar testes automatizados e pipeline v1.4.3 em ambiente congelado; comparar hashes, linhas, métricas, rankings e tabelas com tolerâncias explícitas.
8. Explicar/reconciliar 9.637 vs 9.655 (Novo SGP), 2.115 vs 2.116 (SIGA) e 0,898 vs 0,921538 (VLibras).
9. Só então atualizar README, metodologia, nomes RQ1–RQ3, tabelas e figuras, mantendo um changelog de proveniência.

## Riscos de merge

- `main` e a linha v1.4.3 divergem no mesmo merge-base; merge ingênuo pode manter documentação v1.4.1 ou substituir o paper.
- `README.md`, `docs/METHODOLOGY.md`, `docs/RQ4_GUIDE.md`, `docs/TODO.md`, `pyproject.toml`, pipeline e scripts têm versões semanticamente diferentes.
- Consolidados v1.4.3 têm nome “final”, mas corpus antigo; copiá-los sem namespace perpetua evidência incompatível.
- A análise estática antiga usa Painel e-SUS e não pode ser renomeada como resultado definitivo.
- Arquivos de avaliação vazios podem ser confundidos com codificação concluída.
- Checksum confirma integridade, não validade científica nem execução.

## Critério de saída da futura consolidação

Uma branch final só deve ser chamada reprodutível quando uma execução limpa gerar os cinco sistemas definitivos, as medianas publicadas e os artefatos de RQ3/estática com dados-fonte auditáveis, seguida de comparação automática com os valores do paper. Até lá, a formulação correta é “implementação e resultados parciais/localizados”, não “reprodução bem-sucedida”.

## Progresso posterior à auditoria

A branch local `paper-final/v143` foi criada a partir de `9436e0e`. Ela inclui manifesto, registro de proveniência, tabelas fiéis ao paper, verificadores, checksums, guia de reprodução e CI. A suíte automatizada passou com 44 testes. Permanecem pendentes os datasets-fonte contextual e estático finais e a reexecução completa sobre os cinco repositórios externos.
