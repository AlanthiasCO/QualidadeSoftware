# Resultados da análise sem e-SUS

## Objetivo

Esta pasta reúne os resultados e materiais de trabalho do estudo após a retirada do Painel e-SUS APS do escopo e a inclusão do VLibras Web Browsers.

O conjunto atual contém cinco sistemas:

- Novo SGP
- SAPL
- SIGA
- SIGI
- VLibras Web Browsers

As análises estão organizadas de acordo com as duas questões de pesquisa:

- **RQ1:** Quão estável é a prioridade produzida por H ao longo da evolução dos sistemas?
- **RQ2:** Arquivos de alta prioridade apresentam mais evidências contextuais compatíveis com dívida técnica do que arquivos comparáveis de menor prioridade?

A RQ1 possui resultados quantitativos e gráficos. A RQ2 possui uma amostra pareada congelada e planilhas para codificação manual; seus resultados dependem da avaliação dos arquivos e do registro das evidências.

## Estrutura

```text
results/analise_sem_esus/
├── README.md
├── rq1/
│   ├── estabilidade_rq1_sem_esus.csv
│   ├── resumo_rq1_sem_esus.csv
│   ├── rq1_estabilidade_H_sem_esus.png
│   └── rq1_heatmap_estabilidade_H_sem_esus.png
└── rq4/
    ├── README.md
    ├── rq4_avaliacao.csv
    ├── amostra_pares_congelada.csv
    ├── SHA256SUMS
    ├── avaliacao_avaliador1.csv
    └── avaliacao_avaliador2.csv
```

O nome da pasta `rq4/` foi mantido por compatibilidade com os materiais anteriores do projeto. No desenho atual do estudo, a análise contextual descrita nessa pasta corresponde à **RQ2**.

---

## RQ1 — Estabilidade da prioridade H

### O que foi analisado

A estabilidade foi estimada comparando os rankings de prioridade H de snapshots anuais consecutivos. Para cada sistema e transição, calculou-se a correlação de Spearman entre as posições dos arquivos presentes nos dois snapshots.

Assim, a análise mede se arquivos que aparecem em ambos os snapshots mantêm posições semelhantes no ranking. O campo `shared_files` informa quantos arquivos participaram de cada comparação.

O e-SUS foi excluído. A análise combina os resultados consolidados dos quatro sistemas mantidos do estudo anterior com os resultados do VLibras Web Browsers.

### Arquivos produzidos

#### `rq1/estabilidade_rq1_sem_esus.csv`

Tabela detalhada com uma linha por sistema e transição anual. Contém:

- `project_id`: identificador do sistema;
- `system_name`: nome legível do sistema;
- `year_a` e `year_b`: anos dos snapshots comparados;
- `shared_files`: quantidade de arquivos presentes nos dois snapshots e usados na comparação;
- `rank_spearman`: correlação de Spearman entre os rankings H;
- `p_value`: valor-p associado à correlação, conforme registrado nos dados de origem.

Este é o arquivo indicado para consultar os resultados de cada transição individual. O valor de Spearman deve ser interpretado junto com `shared_files`, pois o tamanho da amostra varia entre sistemas e anos.

#### `rq1/resumo_rq1_sem_esus.csv`

Resumo descritivo agrupado por sistema. Contém:

- `transicoes`: quantidade de transições anuais disponíveis;
- `mediana_spearman`: mediana da correlação entre as transições;
- `menor_spearman` e `maior_spearman`: extremos observados;
- `mediana_arquivos_compartilhados`: mediana do número de arquivos comparados entre snapshots.

O resumo facilita a descrição de cada sistema, mas não substitui a tabela detalhada. A mediana, isoladamente, não mostra a variação entre anos nem o tamanho de cada comparação.

#### `rq1/rq1_estabilidade_H_sem_esus.png`

Gráfico de linhas da correlação de Spearman por transição anual, com uma linha para cada sistema. Os rótulos `n` indicam a quantidade de arquivos compartilhados em cada comparação.

O gráfico ajuda a observar mudanças na estabilidade ao longo do tempo. Como os sistemas podem ter quantidades diferentes de transições, compare apenas períodos que tenham dados.

#### `rq1/rq1_heatmap_estabilidade_H_sem_esus.png`

Mapa de calor da correlação de Spearman por sistema e transição. Cada célula preenchida mostra o valor de Spearman e a quantidade de arquivos compartilhados (`n`). Células vazias correspondem a transições sem dados para aquele sistema.

O mapa de calor facilita a comparação visual entre sistemas e períodos. A cor não deve ser interpretada sem consultar o valor de Spearman e o tamanho da amostra indicado na célula.

### Script e fontes dos dados

O script `scripts/plot_rq1_sem_esus.py` reúne os dados, valida o conjunto de sistemas, calcula o resumo e gera os dois gráficos. Ele utiliza:

- `results/final/v143/consolidado_rq3_estabilidade_v143.csv` para Novo SGP, SAPL, SIGA e SIGI, filtrando o e-SUS;
- `outputs/vlibras_web_browsers/09_rq3_ranking_stability.csv` para o VLibras Web Browsers.

Para reproduzir a geração dos arquivos, execute na raiz do repositório:

```bash
.venv/bin/python scripts/plot_rq1_sem_esus.py
```

O script grava os arquivos em `results/analise_sem_esus/rq1/`.

### Limite da interpretação

A comparação considera os arquivos presentes nos dois snapshots de cada transição. Portanto, a análise descreve a estabilidade do ranking para arquivos persistentes entre os anos comparados. Ela não mede diretamente a estabilidade dos arquivos que foram adicionados ou removidos entre snapshots.

Os sistemas também apresentam quantidades diferentes de arquivos compartilhados. Essa diferença deve ser mencionada ao comparar os resultados, em especial para sistemas com amostras menores.

---

## RQ2 — Evidências contextuais em hotspots e controles

### Objetivo

A amostra da RQ2 foi construída para comparar arquivos de alta prioridade H com arquivos de menor prioridade pareados. O objetivo é verificar se os hotspots apresentam mais evidências contextuais compatíveis com dívida técnica do que controles comparáveis.

A seleção contém cinco pares por sistema, totalizando **25 pares e 50 arquivos**. O e-SUS foi removido e o VLibras Web Browsers foi incluído.

### Regra de pareamento

Cada par contém:

- um arquivo classificado como `hotspot`;
- um arquivo classificado como `control`;
- ambos do mesmo sistema e da mesma linguagem.

Os controles têm menor H e são pareados com hotspots considerando tamanho mediano em NLOC e primeiro ano observado. A seleção segue os critérios implementados na pipeline v1.4.3.

O arquivo `results/analise_sem_esus/rq4/README.md` registra os sistemas, branches, SHAs de freeze e o protocolo de avaliação da amostra.

### Arquivos da amostra e avaliação

#### `rq4/amostra_pares_congelada.csv`

Cópia de referência da amostra selecionada. Contém os pares, os arquivos e os campos destinados ao registro das evidências e classificações.

Depois de validada e congelada, esta cópia deve ser preservada. Não registre as avaliações diretamente nela. Se for necessário alterar a composição da amostra, mantenha a versão anterior, crie uma nova versão e documente a justificativa.

#### `rq4/SHA256SUMS`

Arquivo de checksum da amostra congelada. Serve para verificar se `amostra_pares_congelada.csv` continua idêntico à cópia registrada.

A verificação deve ser executada na raiz do repositório:

```bash
sha256sum -c results/analise_sem_esus/rq4/SHA256SUMS
```

A mensagem `SUCESSO` confirma que o conteúdo da amostra corresponde ao checksum registrado. O checksum não valida as planilhas de avaliação nem comprova que a codificação foi concluída.

#### `rq4/rq4_avaliacao.csv`

Planilha de trabalho consolidada da amostra. Mantém os dados dos pares e disponibiliza colunas para registrar evidências, classificações dos avaliadores, concordância e consenso.

Use-a conforme o protocolo definido pela equipe. Preserve a cópia congelada separadamente.

#### `rq4/avaliacao_avaliador1.csv`

Cópia de trabalho destinada ao primeiro avaliador. Deve ser preenchida de forma independente, registrando as evidências consultadas, a classificação e as notas pertinentes.

#### `rq4/avaliacao_avaliador2.csv`

Cópia de trabalho destinada ao segundo avaliador. Deve ser preenchida independentemente da primeira avaliação, usando o mesmo codebook.

As cópias começam a partir da mesma estrutura de dados. Durante a avaliação, cada avaliador deve registrar sua própria decisão sem consultar ou copiar a classificação do outro. Após a codificação independente, as divergências devem ser comparadas e resolvidas por consenso, com as decisões finais registradas na planilha consolidada.

### Evidências a consultar

A avaliação deve considerar o código e os artefatos de desenvolvimento disponíveis no SHA de freeze de cada sistema, como:

- comentários e justificativas no código;
- mensagens de commit;
- issues e pull requests;
- registros de refatoração.

Registre referências que permitam localizar e conferir cada evidência. A presença de uma palavra ou marcador isolado, como `TODO`, não deve ser tratada automaticamente como prova de dívida técnica.

O protocolo e as classes de avaliação devem seguir `docs/CODEBOOK_RQ4.md`. Antes de iniciar a codificação, os avaliadores devem alinhar a interpretação das classes para aplicá-las igualmente a hotspots e controles.

### Revisão de elegibilidade

Antes de codificar, confirme que todos os arquivos selecionados atendem aos critérios de elegibilidade do estudo. Registre a decisão sobre `webpack.config.js`, incluído como controle do VLibras.

Se um arquivo ou par for considerado inelegível, documente a razão e o procedimento usado para substituí-lo. Atualize a amostra e seu checksum somente após registrar a mudança e preservar a versão anterior.

### Estado da RQ2

A existência da amostra congelada e das planilhas não significa que a avaliação tenha sido concluída. Para concluir a RQ2 ainda é necessário:

1. revisar a elegibilidade dos arquivos;
2. preencher as duas planilhas independentemente;
3. registrar as evidências e referências consultadas;
4. medir e discutir a concordância entre avaliadores conforme o método definido no estudo;
5. resolver divergências por consenso;
6. consolidar os resultados e realizar a análise comparativa entre hotspots e controles.

---

## Integridade e versionamento

Os arquivos desta pasta devem ser versionados junto com os scripts e a documentação necessários para reproduzir ou auditar as análises.

A amostra congelada da RQ2 e seu checksum devem permanecer vinculados. Não sobrescreva a amostra congelada após o início da avaliação. Preserve os registros de cada avaliador e documente alterações, decisões de elegibilidade e consensos.