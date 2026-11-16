# 04 — Divergências em relação ao paper final

## Divergências críticas

1. **Corpus consolidado:** `results/final/v143/manifest.json` lista Painel e-SUS e não VLibras. O corpus final exige VLibras e exclui Painel.
2. **Análise estática:** dados rastreados produzem 9/11/5, p=0,823803 em 25 pares antigos. O paper final declara 5/10/5, p=0,302 em 20 pares, com cinco VLibras não classificados. Não foi localizado o dataset que transforma/sustenta esse resultado.
3. **Inspeção contextual:** as planilhas definitivas de 50 arquivos estão sem qualquer evidência, classe de avaliador ou consenso preenchido. Os números 7/25, 3/25 e p=0,289 constam no manuscrito, mas a trilha de dados subjacente está ausente.
4. **Contagens do corpus:** paper: Novo SGP 9.637 e SIGA 2.115 arquivos; consolidado v1.4.3 antigo: 9.655 e 2.116. É preciso documentar o filtro/versão que explica a diferença.
5. **H do exemplo VLibras:** paper `plugin/Plugin.js = 0,898`; amostra rastreada `0,921538...`. Sem um ranking definitivo versionado, a origem de 0,898 é incerta.

## Documentação antiga versus método definitivo

| Tema | Antigo | Definitivo |
|---|---|---|
| Questões | RQ1 concentração; RQ2 associação; RQ3 estabilidade; RQ4 qualitativa | RQ1 operacionalização; RQ2 estabilidade; RQ3 evidência contextual; estática complementar |
| Seleção qualitativa | RQ4, às vezes até 15 hotspots sem controles | 25 hotspots + 25 controles, cinco pares por sistema |
| Quinto sistema | Painel e-SUS APS, só 2024–2025 | VLibras Web Browsers, 2020–2026 |
| Papel de H | inicialmente associado a “hotspots” por cortes operacionais | ranking contínuo; cortes só formam a amostra |
| Pareamento | variantes por NLOC/primeiro ano ou NLOC/snapshots | paper: mesmo sistema/linguagem, NLOC e quantidade de snapshots |

Há inconsistência residual na própria documentação de `results/analise_sem_esus`: chama estabilidade de RQ1 e contexto de RQ2, enquanto o paper final usa RQ2 e RQ3. O diretório `rq4/` foi mantido por compatibilidade, não por semântica final.

## Falha de compilação C#

O caso `ServicoEOL.cs` tem `restore_returncode=0`, `build_returncode=1` e foi registrado como zero ocorrências, gerando empate. Isso não prova ausência de ocorrências. O paper final reconhece corretamente a ameaça. Em qualquer consolidação, o registro deve manter estado “falha/inconclusivo” separado de contagem zero; não se deve converter falha em ausência.

## Evidência e incerteza

Comprovado: código v1.4.3 presente; correções técnicas; medianas de estabilidade; configuração/validação VLibras; composição da amostra de 25 pares; resultado estático antigo e falha C#.

Não comprovado: execução local bem-sucedida; equivalência integral dos resultados ao paper; dataset contextual preenchido; dataset estático final; explicação das contagens divergentes; proveniência do H=0,898; metadados administrativos do PR #1.
