# Guia operacional — análise estática pareada

## Objetivo

Avaliar se arquivos de alta prioridade longitudinal apresentam maior densidade
de ocorrências detectadas por análise estática do que controles comparáveis.
A etapa não diagnostica dívida técnica e não depende de inspeção manual.

## Amostra

- até 5 pares por sistema e 25 pares no total;
- hotspot e controle do mesmo sistema e linguagem;
- arquivos presentes em pelo menos 2 snapshots;
- hotspots no quantil superior de H mediano;
- controles na metade inferior de H mediano;
- controle mais próximo por NLOC mediano e primeiro ano observado;
- cada controle pode ser utilizado uma única vez.

A pipeline grava a amostra em:

```text
outputs/<projeto>/10_rq4_static_analysis_pairs.csv
```

## Coleta automatizada

Executar analisadores adequados a cada linguagem e registrar ferramenta, versão,
regra, severidade, tipo, arquivo, linha e esforço estimado quando disponível.
Falhas de compilação ou de análise devem ser distintas de zero ocorrências.

## Desfecho principal

Para cada arquivo:

```text
densidade = total de ocorrências / NLOC * 1000
```

Para cada par:

```text
diferença = densidade do hotspot - densidade do controle
```

Relatar pares favoráveis ao hotspot, favoráveis ao controle e empates, mediana
das diferenças, teste exato de sinais e tamanho de efeito pareado.

## Sensibilidade

Repetir a comparação excluindo regras cosméticas, considerando severidades
maiores, restringindo a regras de complexidade/manutenibilidade e excluindo
arquivos cuja análise não tenha sido concluída corretamente.
