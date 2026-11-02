# Relatório de execução da extração de métricas — SAPL

## 1. Escopo e identificação da execução

- Data da execução: 5 de outubro de 2026.
- Projeto piloto: SAPL.
- Repositório: `https://github.com/interlegis/sapl.git`.
- Cópia local: `repos/sapl`.
- Branch configurada: `3.1.x`.
- Commit de congelamento: `55f02aa6397bc613ad5b471b799519e02e53dde5`.
- Data do commit de congelamento: `2026-09-01T18:43:34-03:00`.
- Período configurado: 2020 a 2026.
- Extensão analisada: `.py`.
- Exclusões preservadas: `node_modules`, `vendor`, `static/vendor`, `dist`, `build`, testes e migrações.

Nenhum período, branch, commit de referência, filtro ou fórmula metodológica foi alterado. Não foi feito commit nem push.

## 2. Inspeção do projeto e do ambiente

Foram inspecionados `pyproject.toml`, `configs/sapl.yml` e os módulos da pipeline em `src/hotspots`, especialmente `cli.py`, `audit.py`, `pipeline.py`, `repository.py`, `snapshots.py`, `git_metrics.py`, `static_metrics.py` e `filtering.py`.

O terminal inicialmente não tinha o ambiente virtual ativo: `python` e `hotspots` não estavam no `PATH`. O ambiente existente em `.venv` foi ativado, sem reinstalação nem alteração de dependências. Estado verificado:

- Python 3.12.3;
- `public-software-hotspots` 1.4.2;
- PyDriller 2.12;
- Lizard 1.24.0;
- pandas 3.0.6;
- NumPy 2.5.3;
- SciPy 1.18.1;
- PyYAML 6.0.3;
- Matplotlib 3.11.2.

O repositório SAPL já estava disponível em `repos/sapl`. O SHA congelado foi resolvido corretamente e estava associado a `3.1.x` e à tag `3.1.165-RC3`.

## 3. Comandos executados

Comandos principais solicitados:

```bash
source .venv/bin/activate
hotspots audit --config configs/sapl.yml
hotspots run --config configs/sapl.yml --output outputs --workers 4
```

Depois da detecção e correção de duplicação técnica nos limites das janelas, os artefatos foram obrigatoriamente regenerados sem reutilizar os CSVs incorretos:

```bash
source .venv/bin/activate
hotspots run --config configs/sapl.yml --output outputs --workers 4 --no-resume
```

Validação independente antes e depois da correção, inicialmente gravada em área temporária e posteriormente preservada em `results/validation/sapl`:

```bash
source .venv/bin/activate
python scripts/validate_pipeline.py \
  --project sapl \
  --config configs/sapl.yml \
  --outputs outputs \
  --validation /tmp/hotspots-validation

source .venv/bin/activate
python scripts/validate_pipeline.py \
  --project sapl \
  --config configs/sapl.yml \
  --outputs outputs \
  --validation /tmp/hotspots-validation-corrected
```

Verificações auxiliares executadas incluíram:

```bash
pwd
rg --files
sed -n ... pyproject.toml configs/sapl.yml src/hotspots/*.py
command -v python3
python3 --version
git status --short
git -C repos/sapl status --short --branch
git -C repos/sapl remote -v
git -C repos/sapl show -s --format=... 55f02aa6397bc613ad5b471b799519e02e53dde5
find outputs/sapl -type f ...
python -m compileall -q src
pytest -q
```

Também foram usados pequenos programas Python, via entrada padrão, para conferir versões instaladas, dimensões e colunas dos CSVs, valores ausentes, faixas das métricas, amostras, contagens anuais e eventos Git repetidos entre checkpoints.

## 4. Resultado da auditoria

O comando `hotspots audit` terminou sem erro e retornou:

| Campo | Resultado |
|---|---:|
| Projeto | `sapl` |
| Branch | `3.1.x` |
| Freeze SHA | `55f02aa6397bc613ad5b471b799519e02e53dde5` |
| Freeze date | `2026-09-01T18:43:34-03:00` |
| Commits desde 2020 | 791 |
| Autores desde 2020 | 28 |
| Arquivos no freeze | 1.598 |
| Arquivos de primeira parte incluídos no freeze | 207 |
| Percentual incluído | 12,953692% |

O percentual reduzido é coerente com o recorte configurado: somente Python de primeira parte, sem testes, migrações e caminhos excluídos.

## 5. Problema encontrado, causa e correção

A primeira execução reutilizou caches considerados compatíveis pelo manifesto. A inspeção dos CSVs mostrou as quatro métricas e ausência de nulos, mas a validação independente encontrou uma divergência em uma das nove amostras:

- arquivo: `sapl/sessao/views.py`;
- período: 2021;
- Nmod: 12 na pipeline e 12 no Git;
- churn: 302 na pipeline e 291 no `git log --follow`;
- NLOC e CCN: coincidentes.

A investigação por commit demonstrou que o commit que encerrava o snapshot de 2021 também estava presente no checkpoint de 2022. O PyDriller trata o limite `since` como inclusivo com precisão de segundos, enquanto a pipeline avançava o início da janela seguinte em um microssegundo. Ao concatenar os checkpoints, o mesmo evento era agregado duas vezes. Nmod não mudava porque é calculado com commits distintos (`nunique`), mas linhas adicionadas, removidas e churn eram somados novamente.

Foram encontrados 11 eventos excedentes idênticos, em 6 commits-limite e 10 caminhos. O efeito acumulado antes da correção era de 160 linhas adicionadas, 26 removidas e 186 de churn indevidamente repetidos.

A correção em `src/hotspots/git_metrics.py` deduplica somente eventos completamente idênticos, usando as colunas já definidas em `EVENT_COLUMNS`, logo após a concatenação dos checkpoints e antes da reconstrução de identidade e agregação. Essa é uma correção operacional de fronteira; mantém as janelas científicas, os filtros e as fórmulas:

```python
ev = ev.drop_duplicates(subset=EVENT_COLUMNS).reset_index(drop=True)
```

Após a alteração, o código compilou e a pipeline foi executada novamente com `--no-resume`, para substituir os CSVs anteriormente derivados dos eventos duplicados. A execução percorreu 797 ocorrências de commits nas janelas; seis são as repetições nos limites dos snapshots. Depois da deduplicação, permaneceram 1.182 eventos de modificação únicos.

## 6. Snapshots obtidos

| Ano | SHA | Data do snapshot |
|---:|---|---|
| 2020 | `522769dcdbd7dff05fd80d9196cc2620cb10980f` | `2020-12-21T13:01:53-03:00` |
| 2021 | `42cdc0b0602db0a6d5c7957a445ff06c26dd2ace` | `2021-12-13T10:48:10-03:00` |
| 2022 | `71f445fcc95d35ff485374552a5c9a9d5e5d3e64` | `2022-12-06T12:51:08-03:00` |
| 2023 | `162bc6e0bf69740549cad065749c36c6a7136fc6` | `2023-12-30T18:48:26-08:00` |
| 2024 | `85a35885719ee49bd5a7affe7150deae4efa6b10` | `2024-10-03T13:21:34-03:00` |
| 2025 | `c926b75c05e63b214184e1a292565df56d80e8dd` | `2025-12-14T16:01:47-03:00` |
| 2026 | `55f02aa6397bc613ad5b471b799519e02e53dde5` | `2026-09-01T18:43:34-03:00` |

Há um snapshot para cada ano de 2020 a 2026. O snapshot de 2026 representa o estado até o freeze de 1º de setembro, não o ano civil completo.

## 7. Arquivos analisados e métricas

A tabela estática contém 1.411 observações arquivo-snapshot, correspondentes a 239 identidades longitudinais únicas e 247 caminhos distintos, pois renomes são reconciliados por identidade. O arquivo mestre também contém 1.411 linhas.

| Ano | Arquivos no snapshot | Arquivos com alteração na janela | Soma de Nmod | Soma de churn | Soma de NLOC | Soma de CCN |
|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 195 | 72 | 353 | 8.587 | 44.399 | 6.784 |
| 2021 | 211 | 80 | 280 | 8.204 | 45.365 | 6.916 |
| 2022 | 196 | 103 | 252 | 11.640 | 43.689 | 6.738 |
| 2023 | 199 | 38 | 110 | 6.941 | 44.336 | 6.872 |
| 2024 | 199 | 21 | 40 | 726 | 44.657 | 6.946 |
| 2025 | 204 | 51 | 109 | 2.450 | 45.256 | 7.076 |
| 2026 | 207 | 24 | 38 | 1.022 | 45.603 | 7.172 |

As quatro métricas estão disponíveis por arquivo e snapshot no arquivo mestre:

- **Nmod**: número de commits distintos que modificaram o arquivo na janela;
- **churn**: soma das linhas adicionadas e removidas na janela;
- **NLOC**: linhas de código reportadas pelo Lizard no snapshot;
- **CCN**: soma da complexidade ciclomática das funções reportadas pelo Lizard no snapshot.

Não há valores ausentes em Nmod, churn, NLOC ou CCN nas 1.411 linhas. As faixas observadas são:

| Métrica | Mínimo | Máximo |
|---|---:|---:|
| Nmod | 0 | 32 |
| churn | 0 | 1.716 |
| NLOC | 0 | 4.296 |
| CCN | 0 | 771 |

Amostra do arquivo mestre corrigido:

| Ano | Caminho | Nmod | churn | NLOC | CCN |
|---:|---|---:|---:|---:|---:|
| 2020 | `docker/create_admin.py` | 1 | 0 | 45 | 6 |
| 2021 | `sapl/api/core/__init__.py` | 7 | 332 | 138 | 29 |
| 2022 | `docker/solr_cli.py` | 1 | 129 | 245 | 35 |
| 2023 | `sapl/api/serializers.py` | 1 | 2 | 240 | 45 |
| 2024 | `sapl/base/models.py` | 1 | 2 | 374 | 18 |
| 2025 | `docker/startup_scripts/create_admin.py` | 1 | 0 | 45 | 6 |
| 2026 | `drfautoapi/drfautoapi.py` | 2 | 204 | 435 | 134 |

## 8. Artefatos gerados e verificados

Todos os arquivos abaixo existem em `outputs/sapl`, têm tamanho maior que zero e foram abertos com pandas para conferência de linhas, colunas e conteúdo:

| Arquivo | Tamanho | Linhas | Colunas | Conteúdo principal |
|---|---:|---:|---:|---|
| `outputs/sapl/00_audit.csv` | 406 B | 1 | 13 | Auditoria do corpus |
| `outputs/sapl/01_snapshots.csv` | 573 B | 7 | 4 | Snapshots anuais |
| `outputs/sapl/02_git_metrics.csv` | 24.184 B | 389 | 8 | Nmod, added, deleted e churn para arquivos modificados |
| `outputs/sapl/03_file_identity.csv` | 20.192 B | 252 | 4 | Mapa completo de caminhos e identidades |
| `outputs/sapl/04_static_metrics.csv` | 154.723 B | 1.411 | 8 | NLOC e CCN por snapshot |
| `outputs/sapl/05_master_hotspots.csv` | 273.050 B | 1.411 | 16 | Base integrada das quatro métricas e escores |
| `outputs/sapl/06_rq1_gini.csv` | 739 B | 21 | 4 | Gini por métrica e ano |
| `outputs/sapl/06b_rq1_lorenz_points.csv` | 199.192 B | 4.254 | 6 | Pontos das curvas de Lorenz |
| `outputs/sapl/07_rq2_associations.csv` | 1.683 B | 14 | 9 | Associações estatísticas |
| `outputs/sapl/08_rq3_longitudinal_files.csv` | 35.491 B | 239 | 12 | Resumo longitudinal com caminho do arquivo |
| `outputs/sapl/09_rq3_ranking_stability.csv` | 427 B | 6 | 6 | Estabilidade entre anos consecutivos |
| `outputs/sapl/10_rq4_hotspot_candidates.csv` | 880 B | 3 | 14 | Hotspots selecionados para a RQ4 |
| `outputs/sapl/11_rq4_qualitative_template.csv` | 1.039 B | 3 | 22 | Modelo qualitativo dos hotspots selecionados |
| `outputs/sapl/pipeline_manifest.json` | 140 B | — | — | Manifesto da execução sem resume, quatro workers |

As colunas essenciais do mestre são `project_id`, `year`, `sha`, `path`, `language`, `file_id`, `nloc`, `ccn`, `nmod`, `added`, `deleted`, `churn`, `r_nmod`, `r_ccn`, `h` e `h_geom`.

### 8.1 Populações de arquivos

`02_git_metrics.csv` representa todos os arquivos modificados durante cada janela histórica, inclusive arquivos removidos antes do snapshot. O arquivo mestre representa somente os arquivos presentes no snapshot correspondente.

| Ano | Modificados na janela | Presentes no snapshot | Modificados presentes | Modificados ausentes | Churn da janela | Churn dos presentes | Churn dos ausentes |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 2020 | 72 | 195 | 71 | 1 | 8.587 | 8.538 | 49 |
| 2021 | 80 | 211 | 78 | 2 | 8.204 | 8.156 | 48 |
| 2022 | 103 | 196 | 74 | 29 | 11.640 | 6.310 | 5.330 |
| 2023 | 38 | 199 | 38 | 0 | 6.941 | 6.941 | 0 |
| 2024 | 21 | 199 | 21 | 0 | 726 | 726 | 0 |
| 2025 | 51 | 204 | 50 | 1 | 2.450 | 2.375 | 75 |
| 2026 | 24 | 207 | 24 | 0 | 1.022 | 1.022 | 0 |

As diferenças não indicam perda de dados: elas decorrem da remoção de arquivos modificados durante a janela antes da formação do snapshot anual.

### 8.2 Seleção da RQ4

A proposta estabelece inspeção qualitativa de até 15 hotspots. Para manter equilíbrio entre os cinco sistemas, a pipeline seleciona até três casos por sistema, pertencentes ao decil superior de H mediano por sistema e linguagem e presentes em pelo menos dois snapshots.

No SAPL foram selecionados:

| Posição | Caminho | Snapshots | Período | H mediano | NLOC mediano |
|---:|---|---:|---:|---:|---:|
| 1 | `sapl/sessao/views.py` | 7 | 2020–2026 | 0,987745 | 4.223 |
| 2 | `sapl/materia/views.py` | 7 | 2020–2026 | 0,969849 | 2.333 |
| 3 | `sapl/base/views.py` | 7 | 2020–2026 | 0,959799 | 1.227 |

Os antigos pares hotspot-controle foram preservados apenas como artefatos preliminares em `outputs/sapl/obsolete_v1.4.1` e não devem ser usados na inspeção qualitativa.

## 9. Validação final

O validador independente recalculou Git e Lizard para nove amostras distribuídas em 2021, 2023 e 2025. Resultado após a correção:

- Nmod: 9/9 coincidentes;
- churn: 9/9 coincidentes;
- NLOC: 9/9 coincidentes;
- CCN: 9/9 coincidentes;
- quatro métricas simultaneamente coincidentes: 9/9.

O comando `python -m compileall -q src` também terminou corretamente.

O comando `pytest -q` foi restringido à pasta `tests` e terminou com três testes aprovados. A coleta não entra mais no repositório aninhado do SAPL.

## 10. Limitações

- O ano de 2026 é parcial e termina no commit congelado de 1º de setembro de 2026.
- O estudo piloto está limitado a arquivos `.py` de primeira parte conforme a configuração; outras linguagens e os caminhos excluídos não estão representados.
- O arquivo `02_git_metrics.csv` contém todos os arquivos modificados na janela; a base mestre contém apenas arquivos presentes no snapshot e atribui Nmod e churn iguais a zero aos presentes sem modificação.
- NLOC e CCN seguem as definições e o parser do Lizard. Em especial, a CCN de arquivo é a soma da CCN das funções detectadas.
- A validação independente detalhada cobriu uma amostra de nove linhas, embora as verificações de esquema, ausência de nulos, intervalos e dimensões tenham abrangido todos os resultados.
- O validador alerta que renomes complexos podem produzir diferenças em verificações com `git log --follow`; nenhuma diferença permaneceu na amostra final.
- As validações anteriores, posteriores e finais da versão 1.4.2 foram preservadas em `results/validation/sapl`, acompanhadas pelo arquivo `SHA256SUMS`.

## 11. Próximo passo recomendado

Com o piloto do SAPL regenerado e validado na versão 1.4.2, o próximo passo é aplicar o mesmo protocolo auditável aos outros quatro softwares. Depois, devem ser consolidados os cinco arquivos mestre, verificada a comparabilidade entre sistemas e congelada a seleção final de até 15 hotspots para a RQ4.
