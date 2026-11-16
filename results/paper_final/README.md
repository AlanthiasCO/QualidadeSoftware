# Consolidação do paper final

Esta pasta registra o estado científico descrito em `paper_reference/paper.tex` para o corpus definitivo da pipeline v1.4.3.

Ela distingue deliberadamente:

- `verified_from_versioned_data`: valor recalculável a partir de dados versionados nesta branch;
- `declared_in_paper`: valor presente no manuscrito, mas sem dataset-fonte final suficiente no repositório;
- `known_mismatch`: valor para o qual existe um artefato antigo incompatível.

## Corpus definitivo

Novo SGP, SAPL, SIGA, SIGI e VLibras Web Browsers. Painel e-SUS APS é material histórico e não integra o corpus final.

## Arquivos

- `manifest.json`: escopo, versão, fontes e estado de reprodutibilidade;
- `corpus_final.csv`: períodos e dimensões reportadas no paper;
- `rq2_stability_final.csv`: medianas e transições verificadas nos CSVs versionados;
- `rq3_contextual_final.csv`: resultado contextual declarado no paper;
- `static_analysis_final.csv`: resultado estático declarado no paper;
- `value_registry.csv`: proveniência e nível de comprovação de cada grupo de resultados.

## Estado

Esta consolidação é fiel ao paper, mas ainda não constitui reprodução integral. As medianas de estabilidade e a composição dos 25 pares são verificáveis. As codificações contextuais finais e o dataset estático de 20 pares não foram localizados.

Execute:

```bash
python scripts/verify_paper_final.py
```

O verificador confirma a consistência estrutural e imprime as lacunas sem transformar resultados declarados em resultados reproduzidos.
