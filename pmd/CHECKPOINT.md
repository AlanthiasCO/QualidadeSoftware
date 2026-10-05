# Checkpoint científico — 2026-10-04

## Estado da análise estática pareada

- Pares totais: **25**
- Pares válidos: **25**
- Pares incompletos: **0**
- Hotspot com maior densidade: **9**
- Controle com maior densidade: **11**
- Empates: **5**
- Pares discordantes: **20**
- Teste exato bilateral de sinais: **p = 0.823803**

## Conclusão deste checkpoint

A análise estática complementar dos mesmos 25 pares da inspeção contextual não mostrou maior densidade de ocorrências nos hotspots. O resultado não sustenta o uso do escore longitudinal como detector automático de dívida técnica. A interpretação preservada no paper é que o método serve para **priorizar onde inspecionar primeiro**, enquanto a caracterização de dívida técnica depende de evidências adicionais.

## Nota de reprodutibilidade

Arquivos ausentes no HEAD foram recuperados pela revisão Git mais recente em que o caminho exato da amostra existia. O pipeline registra `resolution_mode` e `source_revision`. Um arquivo C# histórico (`ServicoEOL.cs`) teve `restore_returncode=0` e `build_returncode=1`; como o par resultou em empate de zero ocorrências, ele não participa dos pares discordantes do teste de sinais.
