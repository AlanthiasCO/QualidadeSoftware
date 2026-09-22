# Public Software Hotspots

Pipeline reproduzível para o estudo longitudinal de hotspots em software público brasileiro, com foco em priorização de inspeção de evidências de dívida técnica.

## Estado atual do projeto

**Versão científica atual:** `v1.4.1`  
**Etapa quantitativa:** concluída e congelada  
**RQ1–RQ3:** análises quantitativas concluídas  
**RQ4:** amostra preparada; inspeção qualitativa pelos avaliadores é o próximo passo

Os cinco casos congelados são:

| Sistema | Branch | Freeze SHA | Linguagens |
|---|---|---|---|
| Novo SGP | `development` | `c7c06015d2be880c1f5c854cad0c080c4508343a` | C# |
| SAPL | `3.1.x` | `55f02aa6397bc613ad5b471b799519e02e53dde5` | Python |
| SIGA | `develop` | `c65f287e84f1a0626c79310da0245bc8abb3175c` | Java |
| SIGI | `master` | `129a9dc1225e09d304cbbc9001c48d47aff11b5e` | Python |
| Painel e-SUS APS | `main` | `d21fe44562fd73c4ae46261a40496079b6e94f15` | Python, JavaScript, TypeScript |

## Estrutura do repositório

```text
.
├── configs/                  # configurações congeladas dos 5 sistemas
├── data/reference/           # corpus e evidências de seleção
├── docs/                     # método, codebook, todo e colaboração
├── metadata/                 # ambiente e manifesto do congelamento
├── results/
│   ├── final/                # resultados quantitativos finais v1.4.1
│   ├── figures/              # figuras consolidadas
│   └── rq4/                  # material operacional da inspeção qualitativa
├── scripts/                  # execução, validação, comparação e congelamento
├── src/hotspots/             # código da pipeline
├── .gitignore
├── pyproject.toml
└── README.md
```

## O que não está versionado no GitHub

Arquivos pesados e regeneráveis ficam fora do repositório:

- clones locais em `repos/`;
- outputs brutos de execução em `outputs*/`;
- caches intermediários;
- logs de execução;
- ambientes virtuais;
- freezes completos duplicados;
- outputs preliminares v1.3 e versões anteriores.

Esses itens são excluídos pelo `.gitignore`. Os resultados finais necessários para análise e colaboração estão em `results/`.

## Instalação

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Linux/macOS:

```bash
source .venv/bin/activate
pip install -e ".[dev]"
```

## Executar a pipeline

Exemplo:

```powershell
hotspots audit --config configs/sapl.yml
hotspots run --config configs/sapl.yml --output outputs --workers 4
```

Com monitor de progresso:

```powershell
python .\scripts\run_with_progress.py --config configs/novo_sgp.yml --output outputs --workers 4
```

## Regras metodológicas implementadas

- unidade quantitativa: arquivo de código-fonte first-party;
- snapshots anuais a partir de 2020;
- janela de mudança: `(snapshot anterior, snapshot atual]`;
- `Nmod`: número de commits que modificaram o arquivo na janela;
- `churn`: linhas adicionadas + removidas;
- `NLOC`: linhas de código no snapshot;
- `CCN`: complexidade ciclomática agregada do arquivo;
- ranking por software + linguagem + snapshot;
- `H = min(R_N, R_C)`;
- testes excluídos;
- migrations excluídas em SAPL e SIGI;
- vendor/generated/build excluídos conforme configuração;
- renomes preservados quando identificados pelo histórico.

`H` é um escore de **prioridade de hotspot**, não um escore de dívida técnica.

## Resultados atuais

A consolidação oficial está em:

```text
results/final/consolidacao_final_resultados_v141.xlsx
results/final/relatorio_final_v141.md
```

A amostra inicial da RQ4 está em:

```text
results/final/consolidado_rq4_amostra_v141.csv
results/rq4/rq4_avaliacao.csv
```

## Próximo trabalho da equipe

O gargalo atual é a **RQ4 — inspeção qualitativa**. A equipe deve:

1. revisar os 25 pares hotspot-controle;
2. inspecionar comentários, commits, issues, PRs e registros de refatoração;
3. classificar independentemente os 50 arquivos por dois avaliadores;
4. resolver divergências por consenso;
5. comparar hotspots e controles;
6. avaliar suficiência informacional;
7. fechar Resultados, Discussão e Ameaças à Validade.

Veja `docs/TODO.md` e `docs/RQ4_GUIDE.md`.

## Reprodutibilidade

O ambiente usado no congelamento está documentado em:

```text
metadata/environment_versions.txt
metadata/pip_freeze.txt
metadata/freeze_manifest.csv
```

A versão congelada usada nos resultados finais é `v1.4.1`.

## Regra de colaboração

Não altere silenciosamente `configs/`, regras de filtro ou fórmulas da pipeline enquanto a RQ4 estiver em andamento. Mudanças metodológicas devem ser registradas em issue/PR e receber nova versão da pipeline.
