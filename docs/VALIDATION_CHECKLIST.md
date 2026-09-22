# Checklist de validacao do piloto

## Corpus e freeze
- [ ] Branch confirmada no repositorio oficial.
- [ ] Freeze SHA registrado no YAML.
- [ ] Data do freeze registrada.
- [ ] Linguagens first-party confirmadas.
- [ ] Diretorios vendor/generated/build identificados e excluidos.
- [ ] Testes excluidos do ranking principal.

## Snapshots
- [ ] Cada SHA e o ultimo commit valido do periodo pretendido.
- [ ] Nao ha snapshots posteriores ao encerramento real do desenvolvimento.
- [ ] Arquivos criados depois de 2020 nao aparecem antes da criacao.

## Historico
- [ ] Amostra de Nmod conferida manualmente com git log.
- [ ] Amostra de churn conferida manualmente com git show/diff.
- [ ] Renomes relevantes preservam o mesmo file_id.

## Metricas estaticas
- [ ] Amostra de NLOC conferida manualmente.
- [ ] Agregacao de CCN do arquivo conferida com a saida do Lizard.
- [ ] Arquivos nao suportados nao entram silenciosamente na base final.

## Escore
- [ ] Percentis calculados por software + linguagem + snapshot.
- [ ] Empates usam postos medios.
- [ ] H = min(R_N, R_C).
- [ ] H_geom utilizado apenas como sensibilidade.

## RQ1-RQ3
- [ ] Gini validado em distribuicoes simples conhecidas.
- [ ] Spearman revisado em uma amostra.
- [ ] Spearman parcial revisado por segundo pesquisador.
- [ ] Estabilidade usa apenas arquivos presentes nos dois snapshots.

## RQ4
- [ ] Lista quantitativa congelada antes da leitura qualitativa.
- [ ] Controles selecionados antes da leitura dos artefatos.
- [ ] Mesmo software e linguagem no pareamento.
- [ ] Dois avaliadores aplicam o mesmo codebook.
- [ ] Divergencias e decisoes consensuais sao registradas.
