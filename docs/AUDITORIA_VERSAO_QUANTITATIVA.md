# Auditoria da versão quantitativa

Data da auditoria: 2026-10-19

## Decisão

A `v1.4.3`, atualmente na branch `origin/sonarqube`, é a versão-alvo da
pipeline para o fechamento do artigo. A `v1.4.1` não deve ser usada para gerar
novos resultados finais, pois a `v1.4.2` corrigiu a duplicação de eventos Git em
limites anuais e a `v1.4.3` corrigiu problemas de identidade longitudinal e de
retomada de execuções.

A `v1.4.3` foi reexecutada, validada nos cinco sistemas, consolidada e comparada
com a `v1.4.1`. Ela passa a ser a base quantitativa oficial do artigo. Os
arquivos em `results/final/*_v141.*` permanecem apenas como baseline histórica.

## Evidências examinadas

- SAPL foi reexecutado após a correção de eventos duplicados. A validação
  independente passou de 8/9 para 9/9 coincidências simultâneas de Nmod, churn,
  NLOC e CCN.
- Novo SGP foi executado com a `v1.4.3` e obteve 9/9 coincidências nas quatro
  métricas.
- Os relatórios de sensibilidade e seus checksums estão preservados em
  `results/validation/` na branch auditada.
- A suíte automatizada da `v1.4.3` foi executada em ambiente temporário e
  terminou com 42 testes aprovados.
- SAPL, Novo SGP, SIGA e SIGI obtiveram 9/9 coincidências nas quatro métricas;
  Painel e-SUS APS obteve 3/3, devido à disponibilidade de apenas dois snapshots.
- A seleção final produziu 5 pares por sistema, totalizando 25 pares e 50 arquivos.
- A branch altera a RQ4 para inspeção manual de até 15 hotspots. Essa alteração
  não deve ser adotada, pois o desenho atual do artigo será automatizado e
  manterá a comparação de 25 pares hotspot-controle.

## Critério para oficializar a v1.4.3

1. Integrar na branch de trabalho as correções da pipeline e os testes da
   `origin/sonarqube`, preservando o desenho pareado automatizado da RQ final.
2. Disponibilizar os cinco repositórios locais nos SHAs congelados.
3. Executar a pipeline `v1.4.3` sem reutilizar resultados `v1.4.1` incompatíveis.
4. Validar amostras de Nmod, churn, NLOC e CCN nos cinco sistemas.
5. Regenerar RQ1, RQ2, estabilidade longitudinal e os 25 pares.
6. Comparar a nova consolidação com a `v1.4.1` e documentar todo impacto.
7. Gerar manifesto de ambiente e checksums da nova base.
8. Somente então declarar a nova versão como base oficial do artigo.

## Estado ao final da auditoria

- Versão oficial anterior: `v1.4.1`, com limitação conhecida.
- Versão-alvo: `v1.4.3`.
- Sistemas validados na versão-alvo: os cinco casos.
- Sistemas ainda pendentes: nenhum.
- Consolidação final `v1.4.3`: concluída em `results/final/v143/`.
- Comparação com `v1.4.1`: concluída; os 25 pares foram preservados.
- Situação: `v1.4.3` oficial para o artigo.
