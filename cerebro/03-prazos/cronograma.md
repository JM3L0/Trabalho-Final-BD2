# Cronograma Operacional

## Prazos Formais do Enunciado
| Evento | Data Limite | Observacoes |
|---|---|---|
| Submissao do artigo | **17/11/2026** (terca-feira) | Submissao do PDF (<= 10 paginas no template SBC) |
| Apresentacao oral e demo | **18 e 19/11/2026** (quarta e quinta) | Apresentacao de ate 20 minutos com demonstracao ao vivo |

---

## Detalhamento das Metas Operacionais (13/11 a 19/11)

| Data | Meta Operacional | Status |
|---|---|---|
| **12/11 (qui)** | Analise de conformidade do enunciado e escolha do SGBD | **Concluido** (Microsoft SQL Server 2022 Developer; [comparativo-sgbds.md](../../comparativo-sgbds.md)) |
| **13/11 (sex — hoje)** | Elaboracao e refinamento tecnico do plano de implementacao em 6 partes, ajuste do catalogo de consultas e sincronizacao da base de conhecimento do cerebro | **Concluido** ([plano-de-implementacao.md](../../plano-de-implementacao.md)) |
| **14/11 (sab)** | Subida do container Docker; extracao do template SBC e criacao do esqueleto LaTeX + `compile_paper.py`; geracao vetorizada (`numpy`) e carga em `Ecommerce_Baseline`; clonagem de `Ecommerce_Otimizado` e aplicacao de indices; validacao dos planos reais (XML) de Q1–Q10 e W1; inicio da redacao (Introducao e Referencial Teorico) | **Proxima Etapa** |
| **15/11 (dom)** | Execucao automatizada do benchmark ($N \ge 30$ em Warm Cache + Cold Cache calibrado, `MAXDOP 1`); consolidacao das metricas, testes de hipotese (t pareado / Wilcoxon) e geracao de graficos; redacao de Metodologia e Resultados no paper SBC | Pendente |
| **16/11 (seg)** | Conclusao da redacao do paper SBC em LaTeX (Resultados, Discussao, Conclusao); compilacao cruzada com controle rigoroso de 10 paginas; elaboracao dos slides, kit da demo (`scripts/demo/`) e gravacao do video de contingencia | Pendente |
| **17/11 (ter)** | Revisao ortografica e tecnica final; compilacao definitiva do PDF e submissao do artigo antes do prazo | Pendente |
| **18 e 19/11 (qua/qui)** | Apresentacao oral (<= 20 min) com demonstracao pratica comparativa lado a lado | Pendente |
