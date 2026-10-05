# Priorização de Inspeção de Dívida Técnica — checkpoint 2026-10-04

Este diretório registra um checkpoint do paper e dos resultados de análise estática pareada.

## Estrutura

```text
paper/
  paper_checkpoint.tex      # versão atualizada do artigo
  paper_original.md         # fonte recebida antes desta atualização
results/
  resultado_rq3_50_arquivos.csv
  resultado_rq3_50_arquivos.json
  comparacao_pareada_rq3.csv
  estatistica_pareada_rq3.json
  issues_detalhadas_rq3.csv
  pmd_siga/                 # relatórios PMD brutos dos 10 arquivos SIGA
pipeline/
  hotspots-static-analysis-rq3-historico.zip
CHECKPOINT.md
README.md
```

## Resultado principal

Foram analisados 25 pares (50 arquivos). Em 9 pares a densidade de ocorrências foi maior no hotspot, em 11 foi maior no controle e em 5 houve empate. O teste exato bilateral de sinais nos 20 pares discordantes resultou em `p = 0.823803`.

A conclusão adotada no paper é deliberadamente limitada: hotspots longitudinais são uma estratégia de **priorização de inspeção**, não um detector automático de dívida técnica.

## Compilação do paper

O `.tex` usa `sbc-template` e `references.bib`, que não estavam presentes nos arquivos fornecidos neste checkpoint. Para compilar localmente, mantenha `sbc-template.sty` e `references.bib` no projeto/ambiente LaTeX do paper.

## Proveniência

Os resultados foram produzidos pelo pipeline incluído em `pipeline/`. Quando um caminho da amostra não existia mais no HEAD, o pipeline recuperou a última revisão Git em que o caminho exato existia, sem substituir o arquivo por outro candidato.
