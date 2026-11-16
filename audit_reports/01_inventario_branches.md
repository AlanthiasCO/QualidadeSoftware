# 01 — Inventário de branches e referências

Auditoria realizada em 2026-11-15, após `git fetch origin` bem-sucedido. Nenhum merge, rebase, reset, checkout, push ou exclusão foi executado. A árvore de trabalho estava em `main`; `paper_reference/` já era um diretório não rastreado e foi preservado.

## Estado e topologia

HEAD: `main` em `71f1a73dfb43efa17d41067311a753ff8b8dd312`.

| Ref | Último commit | Data ISO | Assunto | Atrás de `origin/main` | À frente de `origin/main` |
|---|---|---|---|---:|---:|
| `main` / `origin/main` | `71f1a73` | 2026-10-25T23:42:30-03:00 | versão do paper 25/10 - 23:42h | 0 | 0 |
| `origin/docs-analises` | `9436e0e` | 2026-10-25T22:07:47-03:00 | docs: documenta e adiciona resultados da RQ1 sem e-SUS | 1 | 8 |
| `origin/vlibras` | `03cd48a` | 2026-10-22T21:10:26-03:00 | adiciona análise do VLibras | 1 | 7 |
| `origin/integration/v143-automated` | `64fb765` | 2026-10-19T12:02:00-04:00 | docs: prepara artigo e coleta pré-SonarQube | 1 | 6 |
| `origin/sonarqube` | `15a5cd2` | 2026-10-05T18:00:23-04:00 | fix: corrige identidades e valida pipeline do Novo SGP | 1 | 4 |

Todas as quatro branches de trabalho divergem de `main` no merge-base `979a5d8ba2806511b76a4acef5023057569fc52c`. Elas formam uma linha ancestral única:

`sonarqube` → `integration/v143-automated` → `vlibras` → `docs-analises`.

`main` acrescenta apenas `v_0.5_paper.zip` após o merge-base. Não há tags Git. Há uma ref interna do agente (`refs/agents/.../checkpoints/turn/0`, commit `93c7f0d`), que não é branch científica nem remota e não foi usada como fonte.

## Commits exclusivos da linha de trabalho

| Commit | Papel comprovado |
|---|---|
| `68dd0d0` | análise SonarQube inicial do SAPL |
| `0f342ad` | merge histórico de `main` em `sonarqube` |
| `e8639f9` | v1.4.2: corrige duplicação de eventos no limite anual e piloto SAPL; altera a seleção qualitativa antiga |
| `15a5cd2` | v1.4.3: identidade longitudinal conservadora, validação e retomada segura; valida Novo SGP |
| `31d9612` | consolida v1.4.3, resultados de cinco casos antigos e pares estáticos |
| `64fb765` | preparação pré-SonarQube e paper intermediário |
| `03cd48a` | configuração e validação do VLibras |
| `9436e0e` | análise sem e-SUS, medianas definitivas e amostra de 25 pares com VLibras |

## PR #1

O executável `gh` não está instalado. O PR foi acessado diretamente por `git fetch origin refs/pull/1/head`; `FETCH_HEAD` resultou em `15a5cd2845345bacd3214d063e762009dd6b6f42`, exatamente o tip de `origin/sonarqube`. Portanto, o conteúdo técnico do PR #1 está disponível e corresponde aos quatro commits até `15a5cd2`. Estado, título, reviews e comentários do PR não puderam ser comprovados pela CLI/localmente.

## Arquivos exclusivos e preservação

- Exclusivo de `main`: `v_0.5_paper.zip`. Deve ser preservado como pacote de paper, mas não tomado como fonte quantitativa sem inspeção/reconciliação.
- Exclusivos de `docs-analises`: os 12 arquivos em `results/analise_sem_esus/` e `scripts/plot_rq1_sem_esus.py`. São essenciais para o corpus definitivo.
- `vlibras`: introduz sete arquivos (configuração e seis artefatos de validação VLibras), herdados por `docs-analises`.
- `integration/v143-automated`: introduz consolidados v1.4.3, scripts de consolidação/preparação, guia SonarQube, templates e `slides.pdf`, herdados pelas branches posteriores.
- `sonarqube`: não tem caminhos exclusivos contra as descendentes, mas é a origem histórica das correções e testes v1.4.2/v1.4.3; preservar os commits, não uma cópia duplicada.

## Limites

O inventário prova a presença e a ancestralidade das refs após fetch. Não prova o estado administrativo do PR #1 nem a existência de branches privadas/inacessíveis. Nenhuma reprodução da pipeline foi executada.
