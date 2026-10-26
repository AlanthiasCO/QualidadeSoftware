# Amostra de inspeção contextual — escopo sem e-SUS

## Objetivo

Esta pasta registra a amostra de arquivos selecionada para investigar se arquivos de alta prioridade H apresentam mais evidências contextuais compatíveis com dívida técnica do que controles comparáveis.

## Escopo

A amostra contém cinco sistemas, com cinco pares por sistema: 25 pares e 50 arquivos.

| Sistema | Branch | SHA de freeze | Último snapshot analisado |
|---|---|---|---:|
| Novo SGP | `development` | `c7c06015d2be880c1f5c854cad0c080c4508343a` | 2026 |
| SAPL | `3.1.x` | `55f02aa6397bc613ad5b471b799519e02e53dde5` | 2026 |
| SIGA | `develop` | `c65f287e84f1a0626c79310da0245bc8abb3175c` | 2025 |
| SIGI | `master` | `129a9dc1225e09d304cbbc9001c48d47aff11b5e` | 2026 |
| VLibras Web Browsers | `dev` | `d292d369419196b6e8ba826d674f5d3b4bcefa9a` | 2026 |

O Painel e-SUS APS foi retirado do escopo. O VLibras Web Browsers foi incluído em seu lugar.

## Regra de seleção e pareamento

Cada par contém um arquivo hotspot e um arquivo controle, do mesmo sistema e da mesma linguagem. Os hotspots são selecionados pela prioridade longitudinal H; os controles têm menor H e são pareados por tamanho mediano (NLOC) e primeiro ano observado. A seleção utiliza os critérios implementados na pipeline v1.4.3.

## Arquivos desta pasta

- `amostra_pares_congelada.csv`: cópia de referência da amostra; não editar durante a avaliação.
- `SHA256SUMS`: checksum usado para verificar a integridade dessa cópia.
- `rq4_avaliacao.csv`: planilha de trabalho para registrar evidências e avaliações.

## Revisão de elegibilidade

Antes da codificação, os avaliadores devem confirmar que todos os arquivos da amostra atendem aos critérios de elegibilidade do estudo. Em particular, deve ser registrada a decisão sobre `webpack.config.js`, selecionado como controle do VLibras.

Se qualquer par for alterado, deve-se gerar uma nova versão da amostra, atualizar seu checksum e registrar a justificativa. A amostra anterior deve ser preservada.

## Protocolo de avaliação

Dois avaliadores devem analisar os arquivos independentemente, considerando o código e os artefatos de desenvolvimento disponíveis no SHA de freeze: comentários, mensagens de commit, issues, pull requests e registros de refatoração.

O protocolo de classificação está em `docs/CODEBOOK_RQ4.md`. Antes de iniciar, os avaliadores devem alinhar a interpretação das classes para que indiquem níveis de evidência contextual, independentemente de o arquivo ser hotspot ou controle. Divergências devem ser registradas e resolvidas por consenso.

A planilha final deve manter as evidências e referências que sustentam cada classificação.

## Integridade e rastreabilidade

- Versão da pipeline: `1.4.3`
- Período configurado: 2020–2026
- Quantidade de pares: 25
- Quantidade de arquivos: 50
- Sistemas: Novo SGP, SAPL, SIGA, SIGI e VLibras Web Browsers

O checksum da amostra congelada está em `SHA256SUMS`. Após qualquer mudança na amostra, o checksum deve ser atualizado e a alteração registrada no Git.

