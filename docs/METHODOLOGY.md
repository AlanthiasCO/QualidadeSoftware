# Congelamento metodologico - Pipeline v1.0

Data de congelamento: 2026-09-21

## Regra temporal oficial

Para cada snapshot anual `t`, `Nmod` e `churn` sao calculados na janela:

`(snapshot anterior, snapshot atual]`

Isto significa:

- o commit que constitui o snapshot anterior e **excluido** da janela seguinte;
- o commit que constitui o snapshot atual e **incluido**;
- para o primeiro snapshot da serie, o inicio operacional e `start_year-01-01T00:00:00Z`.

A implementacao principal ja aplicava essa regra ao atualizar o inicio da janela para um instante posterior ao snapshot anterior. O validador independente foi ajustado para reproduzir explicitamente essa semantica.

## Caso de teste de fronteira: SAPL / map_rules.py / 2021

Arquivo: `sapl/rules/map_rules.py`

O `git log --follow --since=<timestamp do snapshot 2020>` retornou quatro commits, porque incluiu tambem o commit exatamente no instante inicial da janela:

- `522769dcdbd7dff05fd80d9196cc2620cb10980f` - 2020-12-21 13:01:53 -0300 - `Adiciona Cargo para Bloco Parlamentar (#3284)`

Esse commit forma o snapshot anterior e nao pertence a janela de 2021. Ao aplicar a janela `(t-1,t]`, o valor correto e:

- `Nmod = 3`
- `churn = 404`

A pipeline principal estava correta; o primeiro script de validacao usava fronteira inicial inclusiva e foi corrigido.

## Validacao do piloto SAPL

Amostra auditada: 9 observacoes arquivo x snapshot.

Apos a correcao da fronteira temporal, a expectativa metodologica e:

- Nmod: 9/9
- churn: 9/9
- NLOC: 9/9
- CCN: 9/9

A analise de sensibilidade `todos os arquivos` vs `somente Nmod > 0` manteve o mesmo top 10 em todos os snapshots do SAPL, com alta correlacao de postos. O cenario principal permanece com todos os arquivos first-party existentes no snapshot; o cenario ativo e tratado como analise de robustez.

## Regras congeladas

1. Unidade quantitativa: arquivo first-party.
2. Testes, vendor, generated, build e minificados sao excluidos conforme configuracao auditada por projeto.
3. Renomes sao preservados em identidade longitudinal quando detectados.
4. Metricas principais: Nmod, churn, NLOC e CCN.
5. H e calculado por software + linguagem + snapshot como `min(R_Nmod, R_CCN)`.
6. Empates usam postos medios.
7. H representa prioridade de hotspot, nao diagnostico de divida tecnica.
8. RQ1: Gini e Lorenz.
9. RQ2: Spearman e Spearman parcial controlando NLOC.
10. RQ3: mediana/IQR de H e estabilidade de ranking.
11. RQ4: pareamento e inspecao contextual humana por pelo menos dois avaliadores.

## Mudancas futuras

Qualquer alteracao que afete filtros, identidade de arquivos, janelas temporais, calculo de metricas, percentis ou H deve gerar nova versao da pipeline e ser registrada no pacote de replicacao.
