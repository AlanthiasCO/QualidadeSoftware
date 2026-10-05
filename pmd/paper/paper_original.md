\documentclass[12pt]{article}



\usepackage{sbc-template}

\usepackage{graphicx,url}

\usepackage[utf8]{inputenc}

\usepackage[brazil]{babel}

\usepackage{array}

\usepackage{booktabs}

\usepackage{float}

\usepackage{enumitem}

\usepackage{amsmath}



\sloppy



\newcommand{\Nmod}{\ensuremath{N\_{\mathrm{mod}}}}

\newcommand{\NLOC}{\ensuremath{N\_{\mathrm{LOC}}}}

\newcommand{\CCN}{\ensuremath{CCN}}



\title{Priorização de Inspeção de Dívida Técnica por Hotspots Longitudinais em Software Público Brasileiro}



\author{Alan Mathias\inst{1}, Domini Acco\inst{1}, Guilherme Tombini\inst{1}, Jemison Santos\inst{1}}



\address{Universidade Estadual de Maringá (UEM)\\\\

Av. Colombo, 5790 -- Zona 07 -- 87020-900 -- Maringá -- PR -- Brasil\\\\

\email{pg2026009962\@uem.br}\\\\

\email{pg20261017594\@uem.br}\\\\

\email{pg20261018223\@uem.br}\\\\

\email{pg2026007135\@uem.br}}



\begin{document}

\maketitle



\begin{abstract}

Technical debt cannot be reliably diagnosed by a single code metric, which makes exhaustive inspection costly in large systems. This paper investigates whether change recurrence and structural complexity can be combined to prioritize files for technical-debt inspection in Brazilian public software. We conduct a longitudinal multi-case study with five public systems and annual snapshots between 2020 and 2026. For each source file, we extract modification frequency, lines of code, and cyclomatic complexity. Priority is represented by the continuous score $H=\min(R_N,R_C)$, which combines the relative positions of modification frequency and complexity without defining hotspots through a fixed percentage threshold. We then analyze ranking stability over time and compare 25 high-priority files with 25 size- and history-aware controls through contextual inspection. Explicit contextual evidence was found in 28\\% of high-priority files and 12\\% of controls, but the paired comparison was inconclusive. The results support longitudinal hotspots as a search-space reduction mechanism, not as an automatic diagnosis of technical debt.

\end{abstract}



\begin{resumo}

Dívida técnica não pode ser diagnosticada de forma confiável por uma única métrica de código, o que torna custosa a inspeção exaustiva de sistemas de maior porte. Este trabalho investiga se recorrência de mudança e complexidade estrutural podem ser combinadas para priorizar arquivos para inspeção de dívida técnica em software público brasileiro. Foi realizado um estudo longitudinal multi-caso com cinco sistemas públicos e snapshots anuais entre 2020 e 2026. Para cada arquivo de código-fonte, foram extraídas frequência de modificação, linhas de código e complexidade ciclomática. A prioridade é representada pelo escore contínuo $H=\min(R_N,R_C)$, que combina as posições relativas de frequência de modificação e complexidade sem definir hotspots por um percentual fixo. Em seguida, avalia-se a estabilidade do ranking no tempo e comparam-se 25 arquivos de alta prioridade com 25 controles pareados por tamanho e histórico. Evidência contextual explícita foi encontrada em 28\\% dos arquivos prioritários e em 12\\% dos controles, embora a comparação pareada tenha sido inconclusiva. Os resultados sustentam hotspots longitudinais como mecanismo de redução do espaço de busca, e não como diagnóstico automático de dívida técnica.

\end{resumo}



\section{Introdução}



Dívida técnica descreve compromissos técnicos que podem atender objetivos de curto prazo, mas aumentar custos de manutenção e evolução posteriormente. Estudos de mapeamento mostram que o fenômeno possui diferentes tipos, indicadores e formas de gerenciamento; por isso, uma métrica isolada não deve ser interpretada como diagnóstico automático de dívida técnica \cite{li2015mapping,alves2016identification}.



Uma alternativa é usar informações já presentes no processo de evolução do software para decidir \emph{onde inspecionar primeiro}. O histórico de mudanças contém informação relevante sobre manutenção e incidência de problemas \cite{graves2000changehistory,moser2008changemetrics}, enquanto a complexidade ciclomática descreve a estrutura do fluxo de controle \cite{mccabe1976complexity}. Essas dimensões podem ser combinadas para priorização sem assumir que alta mudança ou alta complexidade, isoladamente, representem dívida técnica.



Neste estudo, \emph{hotspot} significa uma região do código que merece inspeção prioritária por combinar elevada recorrência de modificação e elevada complexidade estrutural relativa. O objetivo não é criar um \`\`escore de dívida técnica'', mas reduzir o espaço de busca para análise posterior. Essa distinção é coerente com a literatura de Self-Admitted Technical Debt (SATD), que utiliza comentários e outros artefatos registrados por desenvolvedores como evidência contextual \cite{potdar2014satd,li2023satd}, e com estudos que combinam histórico, estrutura e contexto para investigar dívida técnica ao longo da evolução do software \cite{sutoyo2025tracing}.



O contexto empírico é o software público brasileiro. A experiência brasileira de software público está associada ao compartilhamento de soluções e à modernização da administração pública \cite{alves2009spb,pereira2019spb}. A Lei n. 14.129/2021 também reforça a relação entre governo digital, modernização e eficiência na prestação de serviços públicos \cite{leigovernodigital}. Além da relevância institucional, repositórios públicos permitem auditar e reproduzir a análise.



O objetivo geral é investigar se hotspots longitudinais de mudança e complexidade constituem uma estratégia útil para priorizar a inspeção de possíveis evidências de dívida técnica em softwares públicos brasileiros. O estudo é organizado em três questões de pesquisa:



\begin{description}[leftmargin=1.3cm,style=nextline]

&#x20;   \item[RQ1.] Como recorrência de modificação e complexidade estrutural são combinadas para produzir uma prioridade de inspeção?

&#x20;   \item[RQ2.] Quão estável é essa prioridade ao longo da evolução dos sistemas?

&#x20;   \item[RQ3.] Arquivos de alta prioridade apresentam mais evidências contextuais compatíveis com dívida técnica do que arquivos comparáveis de baixa prioridade?

\end{description}



\section{Trabalhos relacionados}



\subsection{Dívida técnica e evidência contextual}



\cite{li2015mapping} e \cite{alves2016identification} mostram que dívida técnica é um conceito amplo e que seus indicadores precisam ser interpretados no contexto do sistema. Essa literatura fundamenta a principal cautela deste trabalho: mudança e complexidade são sinais para priorização, não prova da existência de dívida.



A literatura de SATD fornece uma ponte entre métricas quantitativas e evidência contextual. \cite{potdar2014satd} mostraram que comentários de código podem registrar trabalho incompleto, soluções temporárias e necessidades de retrabalho. \cite{li2023satd} ampliaram essa perspectiva para comentários, commits, pull requests e issues. Assim, a inspeção de arquivos priorizados pode procurar evidências explícitas sem assumir que palavras-chave isoladas sejam suficientes para classificar dívida técnica.



\subsection{Mudança, complexidade e evolução}



Métricas derivadas do histórico de mudanças são recorrentes em estudos de qualidade de software. \cite{graves2000changehistory} mostraram que o histórico de mudanças contém informação relevante sobre incidência de falhas, e \cite{moser2008changemetrics} observaram valor informativo em métricas de processo. Neste trabalho, a frequência de modificação é utilizada como medida de recorrência de manutenção.



A \CCN{} deriva da medida proposta por \cite{mccabe1976complexity} e representa uma dimensão estrutural do código. A combinação de histórico e estrutura é coerente com estudos longitudinais recentes sobre dívida técnica, que também ressaltam a necessidade de evidência contextual para interpretação \cite{sutoyo2025tracing}. \NLOC{} é utilizada apenas para tornar a comparação entre arquivos prioritários e controles mais equilibrada em termos de tamanho.



\section{Metodologia}



\subsection{Desenho e corpus}



A pesquisa é um estudo empírico longitudinal multi-caso, baseado em mineração de repositórios Git e inspeção contextual. A descoberta dos projetos partiu de fontes públicas, incluindo o diretório GitHub Government Community \cite{githubgovernment}, e foi ampliada para organizações públicas brasileiras. O processo resultou em 77 itens inspecionados, 45 softwares catalogados, 21 candidatos elegíveis ao núcleo analítico e cinco sistemas selecionados.



A seleção final foi intencional, buscando diversidade de porte, domínio, maturidade, tecnologia e contexto institucional. Esse tipo de escolha é compatível com estudos de caso e com recomendações de amostragem em engenharia de software, desde que os critérios de seleção e os limites de generalização sejam explicitados \cite{runeson2009casestudy,baltes2022sampling}. A unidade quantitativa de análise é o arquivo de código-fonte \emph{first-party}; dependências de terceiros, artefatos gerados, arquivos de build e testes são excluídos conforme as regras de cada projeto.



\begin{table}[H]

\centering

\caption{Corpus longitudinal analisado.}

\label{tab:corpus}

\small

\begin{tabular}{lrrrrl}

\toprule

\textbf{Sistema} & \textbf{Período} & \textbf{Anos} & \textbf{Arq. únicos} & \textbf{Obs. arq.-ano} & \textbf{Linguagem} \\\\

\midrule

Novo SGP & 2020--2026 & 7 & 9.637 & 50.840 & C\\# \\\\

SAPL & 2020--2026 & 7 & 239 & 1.411 & Python \\\\

SIGA & 2020--2025 & 6 & 2.115 & 10.895 & Java \\\\

SIGI & 2020--2026 & 7 & 299 & 1.516 & Python \\\\

Painel e-SUS APS & 2024--2025 & 2 & 599 & 906 & Python/JS/TS \\\\

\bottomrule

\end{tabular}

\end{table}



\subsection{Snapshots, métricas e escore de prioridade}



Foram utilizados snapshots anuais entre 2020 e 2026, conforme a disponibilidade de histórico de cada sistema. A mineração usa Git e PyDriller \cite{pydriller}; tamanho e complexidade são obtidos com Lizard \cite{lizard}. Para cada arquivo são consideradas três medidas: \Nmod{} (número de modificações na janela), \NLOC{} (tamanho no snapshot) e \CCN{} (complexidade ciclomática). O escore de prioridade utiliza apenas \Nmod{} e \CCN{}.



Para evitar um corte arbitrário como \`\`top 20\\%'', \Nmod{} e \CCN{} são convertidos em posições relativas dentro de cada combinação sistema--linguagem--snapshot. Sejam $R_N(f,t)$ e $R_C(f,t)$ os postos relativos, reescalados no intervalo $[0,1]$. Define-se:



\begin{equation}

H(f,t)=\min\left(R_N(f,t),R_C(f,t)\right).

\end{equation}



O mínimo implementa uma regra conjuntiva: prioridade elevada exige que o arquivo esteja simultaneamente bem posicionado em recorrência de mudança e complexidade. Para resumir a prioridade ao longo do histórico de cada arquivo, utiliza-se a mediana dos valores observados:



\begin{equation}

\widetilde{H}(f)=\mathrm{mediana}\_{t}\\,H(f,t).

\end{equation}



Assim, $H$ e $\widetilde H$ são escores de priorização, não classificadores de dívida técnica.



\subsection{Procedimento para as questões de pesquisa}



\textbf{RQ1 -- priorização.} O escore $H$ é calculado em cada snapshot e $\widetilde H$ resume a prioridade longitudinal. Os arquivos são ordenados por $\widetilde H$, de modo que valores maiores indiquem maior combinação de recorrência de mudança e complexidade relativa. Não há um percentual fixo que defina o constructo de hotspot.



\textbf{RQ2 -- estabilidade longitudinal.} A estabilidade do ranking $H$ entre snapshots consecutivos é estimada pela correlação de postos de Spearman, considerando apenas arquivos presentes nos dois momentos. O objetivo é verificar se a lista de prioridades pode ser tratada como estática ou precisa ser recalculada ao longo do tempo.



\textbf{RQ3 -- evidência contextual.} Para a inspeção foram formados 25 pares, cinco por sistema, com um arquivo da região de alta prioridade e um controle de menor prioridade. O pareamento foi realizado dentro do mesmo sistema e linguagem, considerando proximidade em tamanho (\NLOC{}) e quantidade de snapshots observados. Os cortes usados apenas para compor essa amostra são operacionais e não definem hotspot. O código do último snapshot observado foi submetido a triagem de \texttt{TODO}/\texttt{FIXME}; ocorrências positivas foram lidas no contexto da implementação. O desfecho principal é binário: presença ou ausência de evidência explícita de manutenção pendente, necessidade de refatoração, risco conhecido ou implementação incompleta. As proporções pareadas são comparadas por teste binomial exato sobre pares discordantes.



\section{Resultados}



\subsection{RQ1 -- prioridade de inspeção}



A aplicação de $H$ gera um ranking contínuo em cada snapshot e, por meio de $\widetilde H$, uma prioridade longitudinal por arquivo. Isso permite ordenar o código sem declarar que uma fronteira percentual específica separa \`\`hotspots'' de \`\`não hotspots''. A Tabela\~\ref{tab:rq1} apresenta, para tornar o resultado concreto, o arquivo com maior $\widetilde H$ entre os cinco arquivos de alta prioridade selecionados para inspeção em cada sistema.



\begin{table}[H]

\centering

\caption{Exemplos de arquivos de alta prioridade utilizados na inspeção contextual.}

\label{tab:rq1}

\small

\begin{tabular}{lp{7.2cm}r}

\toprule

\textbf{Sistema} & \textbf{Arquivo} & \textbf{$\widetilde H$} \\\\

\midrule

Novo SGP & \texttt{ObterNotasFrequenciaUseCase.cs} & 0,999 \\\\

SAPL & \texttt{sessao/views.py} & 0,980 \\\\

SIGA & \texttt{ExMovimentacaoController.java} & 0,997 \\\\

SIGI & \texttt{convenios/models.py} & 0,964 \\\\

Painel e-SUS APS & \texttt{nominal\\\_list\\\_adapter.py} & 0,994 \\\\

\bottomrule

\end{tabular}

\end{table}



A RQ1, portanto, não procura demonstrar que esses arquivos possuem dívida técnica. Ela estabelece apenas uma ordem de inspeção baseada na interseção contínua entre recorrência de mudança e complexidade estrutural.



\subsection{RQ2 -- estabilidade longitudinal da prioridade}



A estabilidade do ranking variou entre os sistemas (Tabela\~\ref{tab:rq2}). O Painel e-SUS APS apresentou a maior correlação mediana, 0,695, mas possui apenas uma transição anual comparável. SAPL e SIGI apresentaram estabilidade intermediária, enquanto Novo SGP e SIGA ficaram próximos de 0,40.



\begin{table}[H]

\centering

\caption{RQ2 -- estabilidade de $H$ entre snapshots consecutivos.}

\label{tab:rq2}

\begin{tabular}{lrr}

\toprule

\textbf{Sistema} & \textbf{Spearman mediano} & \textbf{Transições válidas} \\\\

\midrule

Novo SGP & 0,403 & 6 \\\\

SAPL & 0,539 & 6 \\\\

SIGA & 0,394 & 4 \\\\

SIGI & 0,574 & 6 \\\\

Painel e-SUS APS & 0,695 & 1 \\\\

\bottomrule

\end{tabular}

\end{table}



Os resultados mostram alguma persistência, mas não estabilidade suficiente para tratar a priorização como uma lista permanente. Em uso prático, o ranking precisa ser recalculado à medida que o sistema evolui.



\subsection{RQ3 -- evidência contextual nos arquivos priorizados}



A inspeção encontrou evidência contextual explícita em 7 dos 25 arquivos de alta prioridade (28\\%) e em 3 dos 25 controles (12\\%). Houve seis pares com evidência apenas no arquivo prioritário e dois apenas no controle; o teste exato sobre os pares discordantes resultou em $p=0{,}289$. A diferença observada segue a direção esperada, mas a amostra não permite concluir que arquivos prioritários apresentem evidência com frequência estatisticamente distinta dos controles.



\begin{table}[H]

\centering

\caption{RQ3 -- presença de evidência contextual nos 25 pares inspecionados.}

\label{tab:rq3}

\small

\begin{tabular}{lrr}

\toprule

\textbf{Sistema} & \textbf{Alta prioridade} & \textbf{Controle} \\\\

\midrule

Novo SGP & 0/5 & 0/5 \\\\

SAPL & 4/5 & 2/5 \\\\

SIGA & 3/5 & 1/5 \\\\

SIGI & 0/5 & 0/5 \\\\

Painel e-SUS APS & 0/5 & 0/5 \\\\

\midrule

Total & 7/25 (28\\%) & 3/25 (12\\%) \\\\

\bottomrule

\end{tabular}

\end{table}



O sinal ficou concentrado em SAPL e SIGA. Entre os casos encontrados aparecem comentários que identificam \texttt{HACK}, necessidade de refatoração, risco conhecido de erro, tratamento de exceção pendente e métodos incompletos ou \emph{stubs}. A RQ3 fornece, portanto, evidência direcional de utilidade para inspeção, mas não permite afirmar que arquivos prioritários \`\`contêm dívida técnica''.



\section{Discussão}



A principal contribuição do estudo é operacional: transformar duas informações simples --- recorrência de mudança e complexidade estrutural --- em uma fila contínua de inspeção. O escore não depende de um corte percentual para definir hotspot e não pretende substituir julgamento técnico.



A análise longitudinal mostra que a prioridade é dinâmica. As correlações entre snapshots consecutivos são moderadas em vários sistemas, o que desaconselha manter uma lista fixa de arquivos prioritários. O ranking deve acompanhar a evolução do software.



Na inspeção contextual, arquivos prioritários apresentaram evidência explícita com maior frequência que seus controles, mas a diferença foi inconclusiva. A amostra é pequena e comentários de código dependem da cultura de documentação do projeto. O resultado deve ser interpretado como sinal exploratório de utilidade, não como validação definitiva de dívida técnica. Uma continuidade natural é ampliar a triangulação para commits, issues e pull requests, conforme sugerido pela literatura de SATD \cite{li2023satd}.



Do ponto de vista prático, a proposta não decide automaticamente quais arquivos possuem dívida técnica. Ela reduz o espaço inicial de busca e direciona inspeção humana para arquivos que combinam maior pressão evolutiva e maior complexidade estrutural relativa.



\section{Ameaças à validade}



\paragraph{Construto.} \Nmod{}, \CCN{} e $H$ não medem dívida técnica diretamente. O estudo usa essas variáveis para priorização. A evidência contextual baseada em comentários também é incompleta: ausência de marcador não implica ausência de dívida e presença de \texttt{TODO}/\texttt{FIXME} exige leitura do contexto.



\paragraph{Validade interna.} Arquivos maiores podem ser mais difíceis de comparar diretamente; por isso, \NLOC{} é considerada no pareamento dos controles. Snapshots terminais podem possuir durações diferentes, o que pode afetar a quantidade observada de modificações e a comparação entre transições.



\paragraph{Validade externa.} Os cinco casos constituem amostra intencional e não representam estatisticamente todo o universo de software público brasileiro. A generalização pretendida é analítica: avaliar o comportamento do procedimento em sistemas com diferentes domínios, tecnologias e históricos \cite{baltes2022sampling}.



\paragraph{Confiabilidade.} Repositórios, SHAs, filtros, scripts, dados intermediários e resultados foram preservados em pacote de replicação. O escore principal evita um limiar percentual fixo; números utilizados apenas para formar a amostra qualitativa têm função operacional.



\section{Conclusão}



Este trabalho avaliou uma estratégia longitudinal para priorizar a inspeção de possíveis evidências de dívida técnica em cinco softwares públicos brasileiros. O método combina recorrência de modificação e complexidade estrutural em um escore contínuo, evitando definir hotspot por um corte percentual fixo.



O ranking apresenta alguma persistência entre snapshots, mas varia o suficiente para precisar ser atualizado ao longo do tempo. Na inspeção contextual, 28\\% dos arquivos prioritários apresentaram evidência explícita, contra 12\\% dos controles; a comparação pareada, porém, permaneceu inconclusiva.



A conclusão central é deliberadamente limitada: \textbf{arquivos que combinam elevada recorrência de modificação e elevada complexidade estrutural relativa são candidatos úteis para inspeção prioritária, mas a existência de dívida técnica depende de evidência contextual adicional}. Como continuidade, a inspeção pode incorporar outros artefatos de desenvolvimento, como commits, issues e pull requests, sem transformar esses sinais em verdade de referência.



\bibliographystyle{sbc}

\bibliography{references}

\end{document}
