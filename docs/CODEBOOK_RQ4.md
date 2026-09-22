# Codebook RQ4

## Classe 1 - Hotspot quantitativo
Identificado exclusivamente pelas metricas. Nao ha evidencia contextual suficiente para elevar a classificacao.

## Classe 2 - Hotspot com evidencia contextual
Ha artefatos de desenvolvimento indicando manutencao problematica, retrabalho, refatoracao, limitacao tecnica relevante ou trabalho tecnico adiado.

## Classe 3 - Evidencia explicita de divida tecnica
Ha registro textual ou decisao tecnica que sustente claramente uma solucao inadequada, provisoria ou deliberadamente postergada com custo futuro.

## Fontes a inspecionar
- comentarios de codigo
- mensagens de commit
- issues
- pull requests
- registros de refatoracao

## Termos de entrada
TODO, FIXME, HACK, workaround, legacy, temporary, refactor.

Termos isolados nao constituem evidencia suficiente. A classificacao deve considerar o contexto.
