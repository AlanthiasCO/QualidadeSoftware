# v1.4.2 - correções do piloto SAPL

Correção da duplicação de eventos nos limites anuais, mapa completo de identidades, manifesto versionado automaticamente, testes próprios e RQ4 alinhada ao limite de até 15 hotspots.

# Changelog

# v1.4.1 - ajuste residual de filtros de teste

Corrige tres padroes de teste que ainda podiam escapar da v1.4:

- arquivos auxiliares `testutils.py` / `test_utils.py`;
- nomes iniciados por `Test...` / `Teste...` ou `test...` / `teste...` seguidos de separador/letra maiuscula (ex.: `testeCurrency.java`);
- arquivos JavaScript/TypeScript com stem terminado em `.spec` ou `.test` (ex.: `demographicParse.spec.ts`).

A regra evita buscar `spec` como substring generica, para nao excluir nomes funcionais como `Especie` ou `Especiais`.

Os resultados consolidados v1.4.1 fornecidos junto desta correcao foram recalculados por pos-processamento sobre as metricas brutas v1.4, removendo somente esses tres arquivos e recalculando percentis, H e RQ1-RQ4. Nao foi necessario repetir a mineracao Git.

# v1.4.0 - correção de elegibilidade de arquivos e freeze reprodutível

## Motivo
A consolidação dos cinco casos revelou que a v1.3 ainda admitia arquivos que o protocolo do artigo determina excluir:
- diretórios/arquivos de teste em diferentes convenções linguísticas (ex.: `teste/`, `tests.py`, `FooTest.java`, `FooTeste.cs`, `setupTests.ts`);
- migrations Django em SAPL e SIGI, tratadas nesta versão como artefatos gerados de framework para fins do ranking principal.

## Alterações
- marcadores de teste multilíngues: test/tests/teste/testes/spec/specs;
- reconhecimento de nomes de teste em Python, Java, C# e JS/TS;
- opção `exclude_migrations`, ativada em SAPL e SIGI;
- SHAs de freeze fixados nos cinco YAMLs conforme a coleta já auditada;
- fingerprint de cache inclui `exclude_migrations`;
- proteção contra reutilizar outputs antigos quando a configuração/filtro muda.

## Consequência metodológica
Outputs da v1.3 devem ser tratados como preliminares. Para resultados finais do artigo, reexecute os cinco casos com v1.4 em uma pasta de saída limpa. O freeze SHA permanece o mesmo; a mudança é apenas a população elegível de arquivos.

# v1.3.1

Correção de compatibilidade introduzida na refatoração v1.3.

- Restaura `list_files_at()` em `static_metrics.py`.
- A função usa `git ls-tree -r -z --name-only <sha>` e não realiza checkout.
- `audit.py` volta a importar a função normalmente.
- Nenhuma fórmula, filtro, métrica, snapshot ou regra metodológica foi alterada.
- Resultados científicos produzidos por versões anteriores não são modificados por este patch.


# Changelog v1.2

## Monitoramento

- Progresso interno da mineração Git emitido a cada 100 commits ou aproximadamente 5 segundos.
- Exibição de commits processados, total estimado, percentual, taxa, ETA, ano corrente e eventos coletados.
- Progresso interno da extração de métricas estáticas por arquivo/snapshot.
- `run_with_progress.py` interpreta as mensagens de progresso e apresenta barras e ETA.

## Integridade metodológica

O ajuste é observacional. Não altera o cálculo de Nmod, churn, NLOC, CCN, rankings, RQs ou regras de filtragem.

# v1.1.1 - Git UTF-8 no Windows

## Correcao
- `run_git()` agora decodifica stdout/stderr explicitamente como UTF-8.
- Bytes invalidos em metadados historicos do Git sao substituidos durante a leitura (`errors="replace"`) em vez de interromper a pipeline sob Windows/cp1252.
- A alteracao nao modifica o repositorio, os SHAs, as janelas temporais, Nmod, churn, NLOC, CCN ou H.

## Motivacao
No Novo SGP, `git log --format=%aN` encontrou metadados que nao puderam ser decodificados pela pagina de codigo cp1252 usada automaticamente pelo Python no Windows, provocando `UnicodeDecodeError` e `stdout=None`.

# Changelog v1.1.0

## Windows / Git
- Git clone now runs with `-c core.longpaths=true`, preventing checkout failures in repositories with deeply nested paths (notably Novo SGP).
- Managed repositories also receive local `core.longpaths=true` on subsequent runs.

## RQ2
- Constant inputs are detected before Spearman calculation.
- Undefined correlations are emitted as `NaN` with a `status` field such as `constant_input:nmod`, instead of producing a SciPy warning.
- This is descriptive, not imputation: an undefined correlation remains undefined.

## Existing partial Novo SGP clone
If the first clone downloaded objects but checkout failed, recover it with:

```powershell
git -C .\repos\novo_sgp config core.longpaths true
git -C .\repos\novo_sgp restore --source=HEAD :/
```

Then rerun:

```powershell
hotspots audit --config configs/novo_sgp.yml
hotspots run --config configs/novo_sgp.yml --output outputs
```

# Changelog v1.0.0

## Ajustes apos validacao do piloto SAPL

- Corrigido `validate_pipeline.py` para tratar o inicio das janelas anuais como exclusivo.
- Documentada formalmente a regra `(snapshot anterior, snapshot atual]`.
- Registrado o caso de fronteira `sapl/rules/map_rules.py` / 2021.
- Adicionados testes de regressao para a fronteira temporal.
- Versao do pacote atualizada de `0.1.0` para `1.0.0`.
- README atualizado com o procedimento de validacao e os comandos para os quatro casos restantes.

## Impacto nos dados SAPL ja gerados

Nenhuma alteracao na pipeline principal de coleta foi necessaria. Os outputs SAPL ja produzidos permanecem validos. Basta executar novamente o validador atualizado para regenerar `validation/sapl/`.

