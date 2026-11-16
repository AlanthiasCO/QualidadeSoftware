# Public Software Hotspots

Repositório de pesquisa do paper **Longitudinal Analysis of Hotspots in Brazilian Public Software: A Prioritization Strategy for Technical Debt Inspection (2020–2026)**.

O projeto implementa e documenta uma estratégia longitudinal para priorizar arquivos combinando recorrência de modificações e complexidade estrutural. Hotspot significa **prioridade de inspeção**, não diagnóstico automático de dívida técnica.

## Estado científico desta branch

- Branch: `paper-final/v143`
- Pipeline quantitativa: `v1.4.3`
- Estado: **consolidação fiel ao paper com verificação parcial**
- Testes automatizados: **44 aprovados** no ambiente registrado
- Reprodução integral: **ainda não comprovada**

Os resultados de estabilidade e a estrutura dos 25 pares são verificáveis a partir dos dados versionados. Os totais contextuais e da análise estática final estão preservados conforme o paper, mas seus datasets-fonte finais não foram localizados no histórico Git.

Consulte `results/paper_final/`, `REPRODUCIBILITY.md`, `audit_reports/` e `paper_reference/paper.tex` para, respectivamente, consolidação, instruções, auditoria e manuscrito.

## Corpus definitivo

| Sistema | Período | Branch externa | Freeze SHA | Linguagens |
|---|---|---|---|---|
| Novo SGP | 2020–2026 | `development` | `c7c06015d2be880c1f5c854cad0c080c4508343a` | C# |
| SAPL | 2020–2026 | `3.1.x` | `55f02aa6397bc613ad5b471b799519e02e53dde5` | Python |
| SIGA | 2020–2025 | `develop` | `c65f287e84f1a0626c79310da0245bc8abb3175c` | Java |
| SIGI | 2020–2026 | `master` | `129a9dc1225e09d304cbbc9001c48d47aff11b5e` | Python |
| VLibras Web Browsers | 2020–2026 | `dev` | `d292d369419196b6e8ba826d674f5d3b4bcefa9a` | JavaScript/TypeScript |

Painel e-SUS APS pertence ao corpus histórico e **não integra os resultados finais do paper**. Seus artefatos foram preservados para auditoria e não devem ser agregados ao corpus definitivo.

## Questões de pesquisa finais

- **RQ1 — operacionalização da prioridade:** como recorrência de modificação e complexidade estrutural são combinadas para priorizar a inspeção?
- **RQ2 — estabilidade longitudinal:** quão estável é a prioridade durante a evolução dos sistemas?
- **RQ3 — evidência contextual:** arquivos prioritários apresentam mais evidências contextuais que controles pareados?

A análise estática é complementar à RQ3; ela não constitui uma quarta questão de pesquisa no paper final.

## Método implementado

Para cada arquivo `f` e snapshot anual `t`:

```text
H(f,t) = min(R_N(f,t), R_C(f,t))
```

`R_N` é a posição relativa de `Nmod` e `R_C` é a posição relativa de `CCN`, calculadas dentro de sistema, linguagem e snapshot. A prioridade longitudinal é a mediana dos valores observados de H por identidade de arquivo.

Regras principais:

- unidade quantitativa: arquivo de código-fonte first-party;
- janela de mudança: `(snapshot anterior, snapshot atual]`;
- `Nmod`: commits distintos que modificaram o arquivo na janela;
- churn: linhas adicionadas mais removidas;
- `NLOC`: tamanho do arquivo no snapshot;
- `CCN`: complexidade ciclomática agregada pelo Lizard;
- testes, migrations configuradas, vendor e código gerado são filtrados;
- renomes são tratados por identidade longitudinal conservadora;
- NLOC é variável de controle, não componente de H.

## Resultados apresentados no paper

### Estabilidade longitudinal

| Sistema | Spearman mediano | Transições válidas | Evidência |
|---|---:|---:|---|
| Novo SGP | 0,822 | 6 | verificada |
| SAPL | 0,927 | 6 | verificada |
| SIGA | 0,910 | 5 | verificada |
| SIGI | 0,929 | 6 | verificada |
| VLibras Web Browsers | 0,854 | 5 | verificada |

Fonte: `results/analise_sem_esus/rq1/resumo_rq1_sem_esus.csv`.

### Inspeção contextual

- 7 de 25 arquivos prioritários com evidência explícita;
- 3 de 25 controles com evidência explícita;
- teste pareado: `p = 0,289`.

Esses valores estão declarados no paper. As planilhas versionadas não contêm as codificações finais e não permitem reproduzir atualmente esses totais.

### Análise estática complementar

- 20 dos 25 pares classificados;
- 5 com maior densidade no arquivo prioritário;
- 10 com maior densidade no controle;
- 5 empates;
- `p = 0,302`;
- cinco pares de VLibras não classificados.

O dataset estático final não foi localizado. Os resultados antigos em `pmd/results/` usam o corpus anterior com Painel e-SUS e não devem ser apresentados como evidência do resultado final.

## Estrutura relevante

```text
.
├── audit_reports/                 # auditoria de branches, versões e evidências
├── configs/                       # configurações dos sistemas
├── data/reference/                # materiais de seleção do corpus
├── docs/                          # documentação histórica e operacional
├── paper_reference/paper.tex      # paper final de referência
├── results/
│   ├── analise_sem_esus/          # estabilidade e amostra definitiva
│   ├── final/v143/                # consolidação histórica com Painel e-SUS
│   ├── paper_final/               # consolidação fiel ao paper
│   └── validation/v1.4.3/         # validações por sistema
├── scripts/                       # execução e verificadores
├── src/hotspots/                  # pipeline v1.4.3
├── tests/                         # testes automatizados
├── REPRODUCIBILITY.md
└── pyproject.toml
```

## Instalação e validação

Python 3.11 ou superior:

```bash
python -m venv .venv
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
python -m pytest -q
python scripts/verify_paper_final.py
python scripts/verify_paper_final_checksums.py
```

O CI executa a mesma sequência para pushes nesta branch e pull requests.

## Execução quantitativa

Exemplo para um sistema:

```bash
hotspots audit --config configs/sapl.yml
hotspots run --config configs/sapl.yml --output outputs --workers 4
python scripts/validate_pipeline.py --config configs/sapl.yml --output outputs/sapl
```

Uma reprodução completa exige acesso aos cinco repositórios externos nos SHAs congelados, além de tempo e espaço para mineração e métricas estáticas. Outputs brutos, clones locais e caches não são versionados.

## Limitações conhecidas

- avaliações contextuais finais ausentes;
- dataset estático definitivo ausente;
- diferenças de contagem de arquivos do Novo SGP e SIGA ainda não reconciliadas;
- valor de H de `plugin/Plugin.js` divergente entre amostra e paper;
- um arquivo C# histórico apresentou falha de compilação, que não equivale a ausência comprovada de ocorrências.

Até a resolução dessas lacunas, descreva este material como **consolidação fiel ao paper com verificação parcial**, e não como pacote de reprodução integral.

## Regra de colaboração

Não altere silenciosamente configurações, filtros, identidades, fórmulas ou amostras congeladas. Mudanças metodológicas devem receber justificativa, nova versão e comparação explícita com a v1.4.3.
