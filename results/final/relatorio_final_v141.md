# Consolidacao final dos resultados quantitativos - v1.4.1

## Controle de qualidade

A base v1.4 foi auditada antes da consolidacao. Tres arquivos residuais de teste ainda escapavam dos filtros: `sigatp/src/main/java/testeCurrency.java`, `sigi/testutils.py` e `paineis-v2-front/src/services/demographicParse.spec.ts`. Eles foram removidos por pos-processamento e todos os percentis, H, RQ1, RQ2, RQ3 e pareamentos RQ4 foram recalculados. Nenhuma migration permaneceu em SAPL ou SIGI.

## RQ1 - Concentracao

Os coeficientes de Gini indicam concentracao elevada de churn, Nmod e CCN na maior parte dos sistemas. As medianas de Gini de churn foram: Novo SGP 0.870, SAPL 0.934, SIGA 0.906, SIGI 0.931 e Painel e-SUS 0.876. Para CCN, as medianas variaram aproximadamente de 0.719 a 0.848.

## RQ2 - Mudanca e complexidade

As correlacoes brutas sao predominantemente positivas, mas o controle por NLOC reduz fortemente a associacao em varios sistemas. A mediana da correlacao parcial Nmod x CCN e 0.003 no Novo SGP, 0.093 no SAPL, -0.011 no SIGA, 0.059 no SIGI e 0.362 no Painel e-SUS. Isso sustenta uma interpretacao cautelosa: tamanho do arquivo explica parte relevante da associacao bruta entre atividade de manutencao e complexidade. Em SIGA 2025, Nmod e churn sao constantes em zero e a correlacao nao e definida.

## RQ3 - Persistencia e estabilidade

A estabilidade do ranking H e elevada na maior parte das transicoes. Medianas de Spearman entre snapshots consecutivos: Novo SGP 0.821, SAPL 0.927, SIGA 0.910, SIGI 0.929 e Painel e-SUS 0.800. O Novo SGP apresenta crescimento marcado da estabilidade ao longo da serie, de 0.418 a 0.975. O Painel e-SUS possui apenas uma transicao (2024-2025).

## RQ4 - Proxima etapa

A RQ4 ainda nao pode ser respondida apenas com as metricas. Foi preparada uma amostra inicial de 5 pares hotspot-controle por sistema, totalizando 25 pares e 50 arquivos. O pareamento preserva sistema e linguagem e usa vizinho mais proximo sobre NLOC e idade padronizados. Essa amostra deve ser submetida ao protocolo qualitativo por dois avaliadores.

## Decisao operacional

Os resultados quantitativos podem ser usados para redigir RQ1-RQ3. A conclusao sobre divida tecnica deve aguardar a inspeção contextual da RQ4.
