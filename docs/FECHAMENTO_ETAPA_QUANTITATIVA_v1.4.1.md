# Fechamento da etapa quantitativa — v1.4.1

## Status

**Situação:** pronta para congelamento oficial, condicionada apenas ao registro automático das versões exatas do ambiente de execução local.

A base quantitativa oficial do artigo passa a ser identificada como **v1.4.1**.

A v1.4 foi a execução completa dos cinco casos com os filtros metodológicos corrigidos. A v1.4.1 removeu três arquivos de teste residuais detectados na auditoria final e recalculou os resultados derivados (percentis, H e RQ1–RQ4), sem necessidade de repetir a mineração Git.

---

## 1. Casos e SHAs congelados

| Sistema | Branch | Freeze SHA | Data do freeze | Linguagens |
|---|---|---|---|---|
| Novo SGP | `development` | `c7c06015d2be880c1f5c854cad0c080c4508343a` | 2026-02-09 14:04:41 -03:00 | `.cs` |
| SAPL | `3.1.x` | `55f02aa6397bc613ad5b471b799519e02e53dde5` | 2026-09-01 18:43:34 -03:00 | `.py` |
| SIGA | `develop` | `c65f287e84f1a0626c79310da0245bc8abb3175c` | 2025-11-04 17:28:34 -03:00 | `.java` |
| SIGI | `master` | `129a9dc1225e09d304cbbc9001c48d47aff11b5e` | 2026-09-17 11:05:57 -03:00 | `.py` |
| Painel e-SUS APS | `main` | `d21fe44562fd73c4ae46261a40496079b6e94f15` | 2025-11-26 17:21:47 -03:00 | `.py`, `.js`, `.ts` |

Esses SHAs são a referência oficial da coleta e não devem ser atualizados durante a redação do artigo.

---

## 2. Unidade de análise

A unidade quantitativa é o **arquivo de código-fonte first-party**.

O software é a unidade de seleção do corpus.

Os rankings são calculados por **software + linguagem + snapshot**.

---

## 3. Regras finais de elegibilidade de arquivos

### Inclusão

- arquivos de código-fonte first-party;
- apenas extensões explicitamente configuradas para cada sistema;
- arquivo existente no snapshot correspondente;
- linguagem suportada pelo Lizard e definida previamente na configuração do caso.

### Exclusão

São excluídos do ranking principal:

- testes automatizados;
- diretórios e arquivos com padrões `test`, `tests`, `teste`, `testes`, `spec`, `specs`;
- arquivos auxiliares como `conftest.py`, `testutils.py`, `test_utils.py` e variantes `setupTests`;
- padrões de nomes como `FooTest`, `FooTests`, `FooTeste`, `FooTestes`, `test_*`, `teste_*`, `*.spec.*` e `*.test.*`;
- dependências de terceiros;
- `vendor`;
- `node_modules`;
- artefatos de `build`, `dist`, `bin`, `obj` e `target`, conforme aplicável;
- migrations Django em SAPL e SIGI;
- demais caminhos explicitamente excluídos no YAML de cada caso.

### Correção residual v1.4.1

A auditoria final da v1.4 identificou três arquivos de teste residuais:

- SIGA: `sigatp/src/main/java/testeCurrency.java`;
- SIGI: `sigi/testutils.py`;
- Painel e-SUS APS: `paineis-v2-front/src/services/demographicParse.spec.ts`.

Na v1.4.1 esses arquivos foram removidos por pós-processamento das métricas brutas e os resultados derivados foram recalculados. A mineração Git não precisou ser repetida.

---

## 4. Snapshots

- início da janela de observação: **1º de janeiro de 2020**;
- um snapshot por ano, correspondente ao último commit válido disponível no ano;
- snapshot final corresponde ao SHA de freeze do sistema;
- anos posteriores ao encerramento público da atividade do sistema não são criados artificialmente;
- arquivos presentes em apenas um snapshot permanecem nas análises transversais, mas não recebem interpretação de persistência longitudinal.

O Painel e-SUS APS possui apenas dois snapshots válidos no período analisado (2024 e 2025), devendo essa limitação ser explicitada na RQ3.

---

## 5. Janela temporal das métricas históricas

Para cada snapshot anual `t`, `Nmod` e churn são calculados na janela:

`(snapshot anterior, snapshot atual]`

Isto significa:

- o commit que constitui o snapshot anterior é **excluído** da janela seguinte;
- o commit que constitui o snapshot atual é **incluído**;
- as medidas não são acumuladas desde 2020.

Essa regra foi validada empiricamente no SAPL com o caso de fronteira `sapl/rules/map_rules.py`.

---

## 6. Tratamento de renomes

Renomes e movimentações de arquivos são rastreados no histórico Git sempre que possível.

Um identificador longitudinal (`file_id`) preserva a identidade do artefato ao longo dos snapshots, evitando interpretar um arquivo renomeado como um novo arquivo.

---

## 7. Métricas oficiais

Quatro métricas são utilizadas por arquivo:

- `Nmod`: quantidade de commits que modificaram o arquivo na janela anual;
- `churn`: soma de linhas adicionadas e removidas na mesma janela;
- `NLOC`: linhas de código não vazias no snapshot;
- `CCN`: complexidade ciclomática agregada das unidades reportadas pelo Lizard.

Somente `Nmod` e `CCN` entram no escore principal de prioridade.

`churn` é medida histórica complementar.

`NLOC` é variável de controle.

---

## 8. Escore de prioridade de hotspot

Para cada software, linguagem e snapshot:

- `R_N(f,t)`: posição percentual de `Nmod`;
- `R_C(f,t)`: posição percentual de `CCN`;
- empates são tratados por postos médios.

O escore principal é:

`H(f,t) = min(R_N(f,t), R_C(f,t))`

`H` é um **escore de prioridade de hotspot**, não um escore de dívida técnica.

---

## 9. Resultados quantitativos oficiais

São considerados produtos oficiais da etapa quantitativa v1.4.1:

- métricas por arquivo e snapshot;
- ranking H recalculado após a limpeza residual;
- RQ1 — Gini e curvas de Lorenz;
- RQ2 — Spearman e Spearman parcial controlando NLOC;
- RQ3 — mediana/dispersão de H e estabilidade entre rankings consecutivos;
- seleção quantitativa e pareamento inicial para RQ4.

Os outputs v1.3 devem permanecer arquivados apenas como material preliminar/rastreabilidade e não devem ser utilizados como fonte de números no artigo.

Os outputs brutos v1.4 devem ser preservados como origem auditável da correção v1.4.1.

---

## 10. Validação realizada

O piloto SAPL foi validado por comparação independente com Git e Lizard.

Após a correção da fronteira temporal:

- `Nmod`: 9/9 verificações consistentes;
- churn: 9/9 verificações consistentes;
- NLOC: 9/9 verificações consistentes;
- CCN: 9/9 verificações consistentes.

A análise de sensibilidade comparando todos os arquivos com somente `Nmod > 0` manteve o mesmo top 10 em todos os snapshots do SAPL, apoiando a manutenção de todos os arquivos existentes no snapshot como população principal do ranking.

---

## 11. Artefatos que devem ser preservados

A pasta oficial de congelamento deve conter, no mínimo:

- `outputs_v14/` — execução bruta com os cinco sistemas;
- `resultados_corrigidos_v141/` — resultados derivados oficiais após correção residual;
- `consolidacao_final_resultados_v141.xlsx`;
- `relatorio_final_v141.md`;
- figuras finais;
- código-fonte da pipeline v1.4.1;
- `configs/*.yml` congelados;
- changelogs v1.4 e v1.4.1;
- manifesto de versões do ambiente;
- checksums SHA-256 dos artefatos;
- este documento de fechamento.

---

## 12. Versões do ambiente

As versões **exatas** utilizadas na máquina de execução devem ser capturadas no congelamento local.

Dependências mínimas declaradas pelo projeto:

- Python >= 3.11;
- PyDriller >= 2.7;
- Lizard >= 1.17;
- pandas >= 2.1;
- NumPy >= 1.26;
- SciPy >= 1.11;
- PyYAML >= 6.0;
- Matplotlib >= 3.8.

**Não substituir as versões reais executadas por esses mínimos.** O script `congelar_etapa_quantitativa.ps1` deve ser executado para registrar as versões efetivamente instaladas.

---

## 13. Status do checklist

- [x] Congelar oficialmente a base quantitativa na versão **v1.4.1**
- [x] Arquivar os outputs finais dos cinco sistemas — estrutura definida; executar script local para cópia/manifesto
- [x] Registrar os SHAs utilizados em cada sistema
- [ ] Registrar versões exatas das ferramentas e dependências — executar script local
- [x] Consolidar regra de inclusão de arquivos first-party
- [x] Consolidar exclusão de testes
- [x] Consolidar exclusão de migrations
- [x] Consolidar exclusão de vendor/generated/build
- [x] Consolidar tratamento de renomes
- [x] Consolidar definição dos snapshots
- [x] Consolidar janela temporal `(snapshot anterior, snapshot atual]`
- [x] Preservar resultados preliminares anteriores para rastreabilidade — manter `outputs_v13_preliminar` separado
- [x] Definir a v1.4.1 como referência oficial para os resultados quantitativos do artigo

---

## 14. Critério de encerramento desta etapa

A etapa quantitativa estará formalmente encerrada quando o script de congelamento local gerar:

1. `environment_versions.txt`;
2. `pip_freeze.txt`;
3. `freeze_manifest.csv`;
4. `SHA256SUMS.txt`;
5. cópia dos YAMLs e código da pipeline usados na coleta.

Após isso, nenhuma métrica quantitativa deve ser recalculada ou alterada sem abertura explícita de uma nova versão metodológica.
