# Relatório de limpeza para publicação no GitHub

## Objetivo

Manter no repositório somente o estado atual necessário para colaboração e reprodução da pesquisa, removendo artefatos temporários, duplicados e versões superadas.

## Mantido

- código da pipeline com filtro final v1.4.1;
- configurações congeladas dos cinco sistemas;
- scripts de execução, progresso, validação, comparação e congelamento;
- documentação metodológica atual;
- codebook da RQ4;
- corpus/evidências de referência;
- metadados do congelamento quantitativo;
- resultados finais consolidados v1.4.1;
- figuras finais;
- amostra e ficha colaborativa da RQ4;
- TODO e guia de contribuição.

## Removido do repositório limpo

### Outputs preliminares

`outputs_v13_preliminar/` foi removido. Era uma versão anterior aos filtros finais e ocupava aproximadamente 81 MB descompactados.

### Duplicação de outputs v1.4

`outputs_v14/` e a cópia `freeze_quantitativo_v1.4.1/outputs_v14_raw/` não foram mantidas no GitHub. Os dados finais necessários estão em `results/final/`, e a pipeline/configurações permitem regenerar os outputs brutos.

### Caches

Pastas `.cache/` de mineração Git e métricas estáticas foram removidas. São aceleradores de execução, não resultados científicos finais.

### Logs antigos

Logs de execuções de desenvolvimento, tentativas interrompidas e erros já resolvidos foram removidos. O histórico metodológico relevante está consolidado em `docs/CHANGELOG.md`.

### Versões antigas e patches

Foram removidos READMEs de versões intermediárias, patches ZIP, scripts drop-in duplicados e changelogs separados. O histórico útil foi consolidado.

### Arquivos gerados pelo Python

Foram removidos `__pycache__`, `.pyc`, `.egg-info` e caches de testes.

### Clones de terceiros

Os repositórios analisados não devem ser commitados. Eles são recriados em `repos/` a partir das URLs e SHAs definidos em `configs/`.

## Regra daqui em diante

- `main` deve representar o estado científico atual.
- outputs locais, caches e logs permanecem fora do Git.
- resultados finais pequenos e necessários para o artigo podem ser versionados em `results/`.
- mudanças metodológicas exigem issue/PR, atualização do changelog e nova versão.
