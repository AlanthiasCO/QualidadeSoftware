# Guia operacional — RQ4

## Objetivo

Avaliar se arquivos de alta prioridade longitudinal apresentam mais evidências contextuais compatíveis com dívida técnica do que arquivos comparáveis de baixa prioridade.

## Amostra inicial

- até 15 hotspots no conjunto dos cinco sistemas;
- sem controles pareados obrigatórios;
- máximo de 3 hotspots por sistema;
- arquivos presentes em pelo menos 2 snapshots;
- seleção no decil superior de H mediano por sistema e linguagem.

Arquivo de trabalho:

```text
outputs/<projeto>/10_rq4_hotspot_candidates.csv
```

## Fontes a inspecionar

Para cada arquivo, procurar:

1. comentários de código;
2. mensagens de commit;
3. issues;
4. pull requests;
5. registros de refatoração.

Termos como `TODO`, `FIXME`, `HACK`, `workaround`, `legacy`, `temporary` e `refactor` são pontos de entrada, não evidência suficiente isoladamente.

## Classes

### Nível 1 — hotspot quantitativo

Há apenas sinal quantitativo; não foi encontrada evidência contextual suficiente.

### Nível 2 — hotspot com evidência contextual

Há artefatos indicando manutenção problemática, retrabalho, refatoração, limitação técnica relevante ou trabalho técnico adiado.

### Nível 3 — evidência explícita de dívida técnica

Há registro textual ou decisão técnica que sustente claramente solução inadequada, provisória ou deliberadamente postergada com custo futuro.

## Procedimento dos avaliadores

1. Cada avaliador preenche sua classificação independentemente.
2. Não sobrescrever a coluna do outro avaliador.
3. Toda classificação 2 ou 3 deve ter referência rastreável: SHA, issue, PR, URL ou caminho/linha do comentário.
4. Termo isolado não basta; registrar o contexto.
5. Depois das avaliações independentes, preencher `agreement`.
6. Divergências devem ser discutidas e registradas em `consensus_class` e `consensus_notes`.

## Critério de encerramento

A inspeção termina após até 15 hotspots. Qualquer ampliação exige revisão e justificativa formal da proposta metodológica.
