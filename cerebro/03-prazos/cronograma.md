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
| **12/11 (qui)** | Analise de conformidade do enunciado e escolha do SGBD | **Concluido** (Microsoft SQL Server 2022 Developer; [comparativo-sgbds.md](../06-experimentacao/comparativo-sgbds.md)) |
| **13/11 (sex)** | Elaboracao e refinamento tecnico do plano de implementacao em 6 partes, ajuste do catalogo de consultas e sincronizacao da base de conhecimento do cerebro | **Concluido** ([plano-de-implementacao.md](../02-planejamento/plano-de-implementacao.md)) |
| **14/11 (sab)** | Execucao integral das Partes 1 a 6: container SQL Server 2022 (`bd2_sqlserver`), carga de 6,25M linhas, clone `Ecommerce_Otimizado` + 9 indices, planos `.sqlplan`, benchmark completo ($N=30$ Warm / $N=10$ Cold, 880 execucoes), analise estatistica, 5 figuras (300 DPI), artigo SBC (`paper/main.pdf`, 10 paginas), slides (`slides/apresentacao.pdf`, 13 paginas) e kit da demo (`scripts/demo/`) — todas as subpartes aprovadas por 2 auditores | **Concluido** ([relatorio-final-conformidade.md](../10-checklists/relatorio-final-conformidade.md)) |
| **15–16/11 (dom/seg)** | Substituicao dos nomes reais da equipe em `paper/main.tex` e `slides/apresentacao.tex`, recompilacao, revisao final humana, ensaio cronometrado e gravacao do video local de contingencia (`slides/demo_backup_local.mp4`) | **Pendente (Acao Manual da Equipe)** |
| **17/11 (ter)** | Submissao do PDF definitivo do artigo SBC (`<= 10 paginas`) pelo canal oficial | **Pendente (Prazo Formal)** |
| **18 e 19/11 (qua/qui)** | Apresentacao oral (`<= 20 min`, alvo `17m30s`) com demonstracao pratica comparativa lado a lado | **Pendente (Prazo Formal)** |
