# 02 — Comparação das implementações

## Localização das versões

| Versão | Localização/commit | Situação |
|---|---|---|
| v1.4.1 | `main`/`979a5d8` e `results/final/*_v141*` | baseline antigo, com Painel e-SUS e documentação RQ4 antiga |
| v1.4.2 | `e8639f9`; `CACHE_SCHEMA = "v1.4.2"`; validação em `results/validation/sapl/` | correção do piloto SAPL e do limite anual |
| v1.4.3 | `15a5cd2` e descendentes; `pyproject.toml`/`src/hotspots/__init__.py` em 1.4.3 | implementação quantitativa candidata; cache permanece v1.4.2 porque o formato não mudou |

## Correções comprovadas

### PyDriller, janelas, Nmod e churn

Em `e8639f9`, `mine_git_metrics` passa a remover eventos idênticos (`EVENT_COLUMNS`) antes da agregação. A justificativa documentada e testada é que PyDriller trata `since` como inclusivo com precisão de segundos; avançar um microssegundo não impedia o mesmo commit de aparecer em checkpoints adjacentes. O efeito declarado é sobre adições, remoções e churn; Nmod já usava commits distintos.

As janelas científicas permanecem `(snapshot anterior, snapshot atual]`. A correção evita dupla contagem sem mudar os instantes dos snapshots.

### Identidade longitudinal

Em `e8639f9`, `complete_identity_map` inclui caminhos presentes somente em snapshots. Em `15a5cd2`, a implementação é fortalecida: enumera caminhos por snapshot, mantém uniões conservadoras de renomes, detecta colisões e gera mapa completo/determinístico. O validador deixa de usar `git log --follow` para um único caminho e passa a consultar `--full-history` sobre aliases aprovados pelo mapa de identidade.

Risco metodológico mitigado: arquivos renomeados não são validados somente pelo caminho atual e caminhos distintos não devem ser fundidos silenciosamente.

### Lizard, NLOC e CCN

Em `15a5cd2`, a extração estática passa a se integrar ao mapa completo de identidades e recebe testes dedicados. O validador recalcula NLOC/CCN no mesmo SHA com Lizard. A documentação define NLOC como medida do snapshot e CCN como soma da complexidade das unidades detectadas pelo Lizard. Não foi encontrada mudança na fórmula científica de CCN; foram encontradas correções de cobertura/identidade e validação.

### Escore e prioridade longitudinal

O código v1.4.3 preserva `H = min(R_Nmod, R_CCN)`. `rq3.py` ordena por ano antes de agregar e registra o último caminho; a prioridade longitudinal usa a mediana de H por `file_id`. NLOC e churn não entram em H: NLOC é controle/pareamento e churn é medida histórica complementar.

### RQ4/pares

Há três desenhos sucessivos e incompatíveis:

1. v1.4.1: pares hotspot/controle e RQ4 qualitativa;
2. v1.4.2/primeiro v1.4.3: até três hotspots por sistema (máximo 15), sem controles;
3. `31d9612`: cinco pares por sistema (25 pares/50 arquivos), pareados por NLOC mediano e primeiro ano, destinado inicialmente a análise estática.

O paper final renomeia a inspeção contextual para RQ3 e usa os 25 pares. Logo, não se deve reintroduzir a regra intermediária de 15 hotspots.

## Automação e validação

`15a5cd2` adiciona validação de outputs, recuperação de execução, manifesto de estado, execução validada e testes para Git, identidade, retomada, métricas estáticas e validação. `31d9612` adapta a validação para pares e adiciona `consolidate_v143.py`.

Os arquivos de validação registram 9/9 coincidências para amostras dos sistemas antigos e do VLibras, com 3/3 para Painel e-SUS por sua série curta. Isso é evidência de registros versionados, não uma reexecução nesta auditoria.

## Conclusão de implementação

O código a preservar é o de `docs-analises` (idêntico ao núcleo de `integration/v143-automated`/`vlibras` nos módulos principais), incluindo testes e utilitários originados em `e8639f9`, `15a5cd2` e `31d9612`. O script `consolidate_v143.py` não representa sozinho o corpus final: sua lista fixa ainda contém Painel e-SUS e não VLibras. `plot_rq1_sem_esus.py` corrige apenas a consolidação de estabilidade; falta uma consolidação geral do corpus definitivo.

Não foram executados testes nem a pipeline completa; portanto, não há declaração de reprodução bem-sucedida.
