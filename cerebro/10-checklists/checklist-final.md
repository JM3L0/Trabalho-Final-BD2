# Checklist Final de Conformidade

## 1. Setup, Infraestrutura e Dados
- [x] SGBD comercial (nao MySQL) definido: **Microsoft SQL Server 2022 Developer**
- [x] Plano de implementacao completo elaborado e aprovado por subagentes ([plano-de-implementacao.md](../02-planejamento/plano-de-implementacao.md))
- [x] Dataset definido: E-Commerce B2C sintetico com ~6,25 milhoes de registros (`seed=42`)
- [x] Estrategia de bases gemeas definida: `Ecommerce_Baseline` e `Ecommerce_Otimizado` via backup/restore nativo
- [x] Compatibilidade multiplataforma (Windows e Ubuntu) assegurada no planejamento
- [x] Container Docker em execucao (`bd2_sqlserver` via `docker compose up -d`)
- [x] Diretorio `./data` provisionado para o container (em hosts Linux nativos, aplicar `chmod -R 777 ./data`)
- [x] Smoke test de captura de `SET STATISTICS IO, TIME ON` via `pymssql` validado (`scripts/smoke_test.py`)
- [x] Dados gerados (vetorizacao `numpy`, `seed=42`, 6.250.000 linhas) e carregados em `Ecommerce_Baseline` via `bcp`/`BULK INSERT` com `RECOVERY SIMPLE`
- [x] Clone `Ecommerce_Otimizado` restaurado via `BACKUP`/`RESTORE` com sucesso e CSVs temporarios tratados
- [x] 9 indices secundarios criados em `Ecommerce_Otimizado` com amostragem estatistica de 100% (`scripts/sql/04_create_indexes_optimized.sql`)
- [x] Planos reais (`SET STATISTICS XML ON`) de Q1 a Q10 e W1 (+ `q4_intermediate_lookup.sqlplan`) capturados e validados em `results/plans/`
- [x] Metricas e versoes exatas registradas (`results/environment_info.json` e `sp_spaceused`)
- [x] Benchmark automatizado de Q1 a Q10 e W1 executado: 880 runs validas ($N=30$ Warm Cache + $N=10$ Cold Cache, `OPTION (MAXDOP 1)`)

## 2. Artigo Cientifico (Paper em LaTeX)
- [x] Pacote oficial SBC descompactado (`paper/sbc-template.sty`, `paper/sbc.bst`) e artigo redigido em `paper/main.tex`
- [x] Limite estrito de no maximo 10 paginas respeitado no PDF final (`paper/main.pdf` = 10 paginas exatas)
- [x] Formatacao original da SBC preservada sem alteracao de margens ou fontes
- [x] Cobertura dos tres temas obrigatorios: indices, plano de execucao e otimizacao
- [x] Fundamentacao teorica consistente com 8 citacoes reais verificadas no padrao SBC (`paper/sbc-template.bib`, `sbc.bst`)
- [x] Metodologia experimental detalhada (hardware, SQL Server 2022 RTM-CU28, 6,25M linhas, `MAXDOP 1`, protocolo estatistico)
- [x] Tabela comparativa unificada gerada automaticamente (`paper/generated/tabela_resultados.tex`) com Leituras Logicas, Tempos, Speedup e p-valores
- [x] Diagramacao grafica de 4 cenarios representativos de planos fisicos reais (`fig5_planos_execucao.png` a 300 DPI)
- [x] Analise honesta de trade-offs: amplificacao de escrita (`W1`: +85,33% Warm / +264,73% Cold) e inversao *Batch* vs. *Row Mode* (`Q7`: 0,60x)
- [x] Compilacao validada via `scripts/compile_paper.py` (`results/latex_validation.json`: `passed=true`, 0 warnings, 0 `Overfull \hbox`)
- [x] Revisao textual e auditoria tecnica concluidas em todas as subpartes (`[APROVADO]`)
- [ ] **[Acao manual]** Substituir placeholder `\author{Equipe de Banco de Dados II}` pelos nomes reais da equipe (e recompilar) antes de submeter ate **17/11/2026**

## 3. Apresentacao Oral e Demonstracao Pratica
- [x] Slides Beamer 16:9 elaborados (`slides/apresentacao.tex` / `slides/apresentacao.pdf`, 13 paginas) com roteiro cronometrado para **17m30s** (`slides/roteiro-apresentacao.md`)
- [x] Kit de demonstracao pratica configurado com comparacao `Ecommerce_Baseline` vs. `Ecommerce_Otimizado` (`scripts/demo/01..04*.sql`)
- [x] Scripts de demonstracao numerados e testados ao vivo via `scripts/test_demo_kit.py` (incluindo `Q4` puro sem `Key Lookup` e `W1` em `ROLLBACK`) e guia de contingencia (`scripts/demo/README_CONTINGENCIA.md`)
- [ ] **[Acao manual]** Gravar previamente video MP4 local de contingencia (`slides/demo_backup_local.mp4`) antes da banca
- [ ] **[Acao manual]** Confirmacao do dia exato de apresentacao (**18 ou 19/11/2026**) e preenchimento de nomes na capa de `slides/apresentacao.tex`
