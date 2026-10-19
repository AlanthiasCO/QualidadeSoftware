# Execução do SonarQube — amostra v1.4.3

## Objetivo

Executar uma análise reproduzível dos cinco repositórios nas revisões congeladas
e exportar as ocorrências referentes aos 50 arquivos da amostra pareada. O
SonarQube não deve ser executado apenas sobre arquivos isolados, pois parte dos
analisadores depende do contexto do projeto.

## Arquivos preparados

- `results/sonarqube/v143/input_manifest_v143.csv`: 25 pares e 50 arquivos;
- `results/sonarqube/v143/issues_template_v143.csv`: formato de entrega das ocorrências;
- `results/sonarqube/v143/execution_log_template_v143.csv`: registro das cinco execuções.

## Procedimento no outro computador

1. Copiar este repositório e os cinco repositórios de estudo.
2. Em cada repositório, confirmar o remoto e fazer checkout do `freeze_sha`
   indicado no manifesto. Não analisar o HEAD atual por engano.
3. Registrar as versões do servidor SonarQube, scanner, Java/.NET e plugins.
4. Registrar o perfil de qualidade e qualquer configuração alterada. Usar o
   mesmo perfil para projetos da mesma linguagem.
5. Restaurar dependências e compilar quando o analisador da linguagem exigir.
6. Executar o scanner sobre o projeto completo e guardar o log integral.
7. Confirmar no servidor que a análise terminou com sucesso. Falha não equivale
   a zero ocorrências.
8. Exportar todas as ocorrências dos caminhos presentes no manifesto, incluindo
   regra, nome da regra, tipo, severidade, status, linha, esforço e mensagem.
9. Preencher uma linha por projeto em `execution_log_template_v143.csv` e uma
   linha por ocorrência em `issues_template_v143.csv`.
10. Para um arquivo analisado com sucesso e sem ocorrências, inserir uma linha
    com `analysis_status=success`, deixando os campos de ocorrência vazios.
11. Para caminho não encontrado, falha de build ou falha do sensor, registrar
    `analysis_status` correspondente e explicar em `notes`; não inserir zero.
12. Devolver os dois CSVs preenchidos e os cinco logs do scanner.

Tokens de acesso e URLs privadas não devem ser gravados nos CSVs ou logs.

## Validação ao receber os resultados

- os cinco `freeze_sha` devem coincidir com o manifesto;
- todos os 50 arquivos devem possuir estado explícito;
- hotspot e controle de cada par devem usar a mesma execução e configuração;
- duplicatas de paginação da API devem ser removidas por identificador da ocorrência;
- arquivos com falha devem ser excluídos da comparação principal, não tratados como zero.

Somente após essa validação serão calculadas a densidade por mil linhas, a
diferença intrapar, o teste exato de sinais e as análises de sensibilidade.
