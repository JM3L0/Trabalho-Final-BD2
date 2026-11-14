# Relatório Final de Conformidade — Trabalho Final de Banco de Dados II

- **Instituição:** Universidade Federal do Piauí (UFPI) — Campus Senador Helvídio Nunes de Barros (CSHNB), Picos – PI
- **Curso / Disciplina:** Bacharelado em Sistemas de Informação — Banco de Dados II (Prof. Dennis Sávio)
- **Data de Consolidação Técnica:** 14/11/2026
- **Referências Base:** [texto-integral-pdf.md](../00-visao-geral/texto-integral-pdf.md), [requisitos.md](../01-requisitos/requisitos.md), [plano-de-implementacao.md](../02-planejamento/plano-de-implementacao.md)
- **Parecer Global:** **CONFORME** em todas as **6 partes (15 subpartes)** planejadas, com auditoria dupla (`auditor_conformidade` e `auditor_tecnico`) concluída com `[APROVADO]` em todas as etapas e validação experimental ao vivo executada com êxito.

---

## 1. Matriz de Conformidade com o Enunciado (`Trabalho Final.pdf`)

| Requisito do Enunciado | Classificação | Peso | Evidência Verificada no Repositório | Status |
| :--- | :---: | :---: | :--- | :---: |
| **Artigo científico em LaTeX usando template oficial da SBC** | `[PDF]` | 7,0 | `paper/sbc-template.sty`, `paper/sbc.bst`, `paper/main.tex`, `paper/sbc-template.bib`, compilado em `paper/main.pdf` | Conforme |
| **Limite máximo de 10 páginas no artigo** | `[PDF]` | 7,0 | `paper/main.pdf` com **10 páginas exatas** (incluindo resumo, abstract, tabelas, 5 figuras e 8 referências); validado em `results/latex_validation.json` (`"passed": true`, 0 *warnings*, 0 `Overfull \hbox`) | Conforme |
| **Abordar os 3 eixos: índices, plano de execução e otimização** | `[PDF]` | 7,0 | Seção 2 (B+ Trees, cobertura, filtragem, CBO, sargabilidade, operadores físicos, *Batch Mode*), Seção 3 (metodologia) e Seção 4 (11 cenários, diagramas de `ShowPlanXML`, estudo em 3 estágios de `Q4` e *trade-offs*) em `paper/main.tex` | Conforme |
| **Experimentos em SGBD comercial (exceto MySQL)** | `[PDF]` | 7,0 | `Microsoft SQL Server 2022 (RTM-CU28) (KB5125472) - 16.0.4325.4 (X64) Developer Edition` em Docker (`bd2_sqlserver`), justificado em [comparativo-sgbds.md](../06-experimentacao/comparativo-sgbds.md) | Conforme |
| **Base volumosa + comparação estruturada com referencial teórico** | `[PDF]` | 7,0 | Esquema B2C com **6.250.000 registros** (`seed=42`), bases gêmeas isoladas (`Ecommerce_Baseline` vs. `Ecommerce_Otimizado`), 880 medições (`N=30` *Warm* + `N=10` *Cold*) e testes pareados em `results/summary_stats.json` | Conforme |
| **Apresentação oral ($\le 20$ min) com demonstração prática** | `[PDF]` | 3,0 | `slides/apresentacao.pdf` (**13 páginas**, 16:9), roteiro cronometrado para **17m30s** (`slides/roteiro-apresentacao.md`) e 4 scripts testados ao vivo em `scripts/demo/` com planos B e C em `scripts/demo/README_CONTINGENCIA.md` | Conforme |
| **Nomes finais da equipe e entregas nas datas formais** | `[PDF]` | — | Submissão do paper até **17/11/2026** e apresentação em **18 ou 19/11/2026** (ações manuais listadas na Seção 7) | Ação da equipe |

---

## 2. Rastreabilidade por Parte e Subparte do Plano de Implementação

Todas as subpartes listadas em [plano-de-implementacao.md](../02-planejamento/plano-de-implementacao.md) passaram por execução sequencial e dupla auditoria independente (`auditor_conformidade` + `auditor_tecnico`) antes da passagem para a etapa seguinte:

| Parte / Subparte | Escopo Executado | Principais Artefatos | Auditorias |
| :--- | :--- | :--- | :---: |
| **1.1** Docker Multiplataforma | Container SQL Server 2022 Developer (`bd2_sqlserver`) em `127.0.0.1:1433`, volume `./data:/var/opt/mssql/data_import` | `docker-compose.yml`, `.env.example` | `[APROVADO]` x2 |
| **1.2** Ferramental Gráfico | Configuração para VS Code (`ms-mssql.mssql`), *Actual Execution Plan* e captura `ShowPlanXML` | Perfis de conexão e scripts XML | `[APROVADO]` x2 |
| **1.3** Orquestração Python & Portabilidade | Projeto `uv` (`pyproject.toml`, `uv.lock`), conexão `pymssql`, `pathlib.Path`, `snake_case`, `.gitattributes` (`LF`) e *smoke test* | `scripts/db.py`, `scripts/smoke_test.py`, `scripts/setup_ubuntu.sh` | `[APROVADO]` x2 |
| **1.4** Compilação LaTeX Multiplataforma | Extração do pacote oficial SBC e orquestrador multiplataforma de compilação | `paper/sbc-template.sty`, `paper/sbc.bst`, `scripts/compile_paper.py` | `[APROVADO]` x2 |
| **2.1** Esquema Relacional B2C | DDL de `Clientes`, `Produtos`, `Pedidos`, `ItensPedido` com 4 PKs clusterizadas e 3 FKs confiáveis | `scripts/sql/01_create_baseline_db.sql`, `scripts/create_schema.py` | `[APROVADO]` x2 |
| **2.2** Gerador Vetorizado Reprodutível | Geração em massa via `numpy` com `seed=42`, UTF-8 / UTF-16 (`widechar` p/ acentuação no Linux) e `newline='\n'` | `scripts/generate_data.py` | `[APROVADO]` x2 |
| **2.3** Carga Massiva no Baseline | `RECOVERY SIMPLE` + `bcp`/`BULK INSERT` com `BATCHSIZE=100000`, carregando 6.250.000 linhas e integridade referencial | `scripts/sql/02_bulk_load_baseline.sql`, `scripts/load_baseline.py` | `[APROVADO]` x2 |
| **2.4** Clone Gêmeo via Backup/Restore | Clonagem nativa idêntica de `Ecommerce_Baseline` para `Ecommerce_Otimizado` via `.bak` (`WITH MOVE`) | `scripts/sql/03_backup_and_clone.sql`, `scripts/clone_optimized.py`, `results/environment_info.json` | `[APROVADO]` x2 |
| **3.1** Catálogo de Consultas (`Q1`–`Q10`, `W1`) | 10 consultas de leitura + 1 carga DML (`W1` em transação revertida), todas com `OPTION (MAXDOP 1)` e literais tipados | `scripts/queries.py`, `scripts/metrics.py` | `[APROVADO]` x2 |
| **3.2** Coleta Inicial do Baseline & XML | Captura inicial de métricas `STATISTICS IO, TIME` e 11 planos `.sqlplan` de referência no Baseline | `scripts/collect_baseline.py`, `results/baseline_initial.json`, `results/plans/baseline/*.sqlplan` | `[APROVADO]` x2 |
| **4.1** Aplicação das Otimizações | Criação dos 9 índices secundários em `Ecommerce_Otimizado` (`sp_updatestats` / 100%), plano intermediário de `Q4` e 11 planos otimizados | `scripts/sql/04_create_indexes_optimized.sql`, `scripts/apply_optimizations.py`, `results/optimized_initial.json`, `results/q4_intermediate.json`, `results/plans/optimized/*.sqlplan` | `[APROVADO]` x2 |
| **4.2** Protocolo Experimental Automatizado | Bateria automatizada com 2 aquecimentos + `N=30` *Warm* alternados + `N=10` *Cold* (`DROPCLEANBUFFERS`/`FREEPROCCACHE`), paridade de linhas e rollback `W1` | `scripts/run_benchmarks.py`, `results/benchmark_runs.json`, `results/benchmark_runs.csv` (880 registros) | `[APROVADO]` x2 |
| **4.3** Estatística, Tabelas e Gráficos | Shapiro-Wilk, Wilcoxon/$t$-Student pareado ($\alpha=0,05$), speedups, tabela LaTeX e 4 gráficos a 300 DPI | `scripts/analyze_results.py`, `scripts/generate_charts.py`, `results/summary_stats.json`, `results/summary_table.csv`, `paper/generated/tabela_resultados.tex`, `fig1`–`fig4` | `[APROVADO]` x2 |
| **5.1** Redação do Artigo SBC + Diagramas XML | Geração da `fig5_planos_execucao.png` direto dos `.sqlplan`, 8 referências reais BibTeX e redação integral em português | `scripts/generate_plan_diagrams.py`, `paper/main.tex`, `paper/sbc-template.bib`, `paper/main.pdf` | `[APROVADO]` x2 |
| **5.2** Validação Rígida de Conformidade LaTeX | Verificador automático de páginas ($\le 10$), margens (`Overfull`), citações/referências, BibTeX e 300 DPI das 5 figuras | `scripts/compile_paper.py`, `results/latex_validation.json` | `[APROVADO]` x2 |
| **6.1** Slides Beamer e Roteiro Cronometrado | Apresentação 16:9 com 13 páginas, 5 figuras integradas, zero *overflow* e roteiro de **17m30s** + Q&A | `slides/apresentacao.tex`, `slides/apresentacao.pdf`, `slides/roteiro-apresentacao.md` | `[APROVADO]` x2 |
| **6.2** Kit da Demo ao Vivo e Contingência | 4 scripts T-SQL padronizados, guia de contingência (Planos A, B, C) e validador automatizado ao vivo com checagem `IndexScan[@Lookup='1']` | `scripts/demo/01`–`04`, `scripts/demo/README_CONTINGENCIA.md`, `scripts/test_demo_kit.py` | `[APROVADO]` x2 |

---

## 3. Infraestrutura, Base de Dados e Estratégia de Indexação

### 3.1. Ambiente e Volumetria Verificada
- **Motor SGBD:** `Microsoft SQL Server 2022 (RTM-CU28) (KB5125472) - 16.0.4325.4 (X64)` — *Developer Edition (64-bit)* em `Linux (Ubuntu 22.04.5 LTS)` via Docker (`bd2_sqlserver`).
- **Host de Execução:** Windows 11 Home Single Language, Intel Core i5-1235U (10 núcleos / 12 threads), 15,71 GB RAM, SSD.
- **Espaço Registrado (`Ecommerce_Baseline`):** `400.00 MB` totais alocados (`62.16 MB` não alocados; `272216 KB` reservados = `259064 KB` dados + `2576 KB` índices iniciais + `10576 KB` não usados), conforme [environment_info.json](../../results/environment_info.json).
- **Cardinalidade Exata Confirmada em Ambas as Bases:**
  - `dbo.Clientes`: **200.000** linhas
  - `dbo.Produtos`: **50.000** linhas
  - `dbo.Pedidos`: **1.500.000** linhas
  - `dbo.ItensPedido`: **4.500.000** linhas
  - **Total consolidado:** **6.250.000** registros por base.

### 3.2. Os 9 Índices Secundários Aplicados Exclusivamente em `Ecommerce_Otimizado`
Definidos em [04_create_indexes_optimized.sql](../../scripts/sql/04_create_indexes_optimized.sql), mantendo `Ecommerce_Baseline` apenas com suas 4 chaves primárias clusterizadas (`PK_Clientes`, `PK_Produtos`, `PK_Pedidos`, `PK_ItensPedido`):

1. `IX_Clientes_Email` em `dbo.Clientes (Email)` — índice não-clusterizado simples (`Q1`).
2. `IX_Produtos_Nome` em `dbo.Produtos (Nome) INCLUDE (Categoria, Preco)` — índice de cobertura para busca textual por prefixo (`Q8`).
3. `IX_Pedidos_DataPedido` em `dbo.Pedidos (DataPedido) INCLUDE (ClienteID, Status, ValorTotal)` — cobertura para faixa temporal (`Q2`, `Q9`) e leitura ordenada `BACKWARD` sem `Sort` (`Q6`).
4. `IX_Pedidos_Status_Data` em `dbo.Pedidos (Status, DataPedido)` — índice composto com igualdade à esquerda e faixa à direita (`Q3`).
5. `IX_Pedidos_ClienteID_Cov` em `dbo.Pedidos (ClienteID) INCLUDE (DataPedido, ValorTotal)` — índice de cobertura eliminando 422 *Key Lookups* (`Q4`, além de apoiar `Q5` e `Q10`).
6. `IX_Pedidos_Status_Cov` em `dbo.Pedidos (Status) INCLUDE (ValorTotal)` — índice de cobertura para agregação `GROUP BY Status` (`Q7`).
7. `IX_ItensPedido_PedidoID` em `dbo.ItensPedido (PedidoID) INCLUDE (ProdutoID, Quantidade, PrecoUnitario)` — cobertura de junção pela FK (`Q5`) e impacto em escrita (`W1`).
8. `IX_ItensPedido_ProdutoID` em `dbo.ItensPedido (ProdutoID)` — índice na FK para integridade referencial e escrita (`W1`).
9. `IX_ItensPedido_Desconto_Alto` em `dbo.ItensPedido (ProdutoID, Desconto) WHERE Desconto >= 10.00` — índice filtrado cobrindo ~20% das linhas (`1.964 / 10.000` linhas inseridas em `W1`).

---

## 4. Síntese Quantitativa dos Experimentos (`880` Execuções)

Os dados completos encontram-se em [summary_stats.json](../../results/summary_stats.json) e [summary_table.csv](../../results/summary_table.csv) (`warmups_discarded = 2`, `warm_runs = 30`, `cold_runs = 10`, `OPTION (MAXDOP 1)`). Em todos os cenários *Warm Cache* ($660/660$ rodadas), `physical_reads == 0`; em *Cold Cache* ($220/220$ rodadas), `physical_reads >= 1`.

### 4.1. Resultados Principais — *Warm Cache* ($N = 30$ por cenário)

| Cód. | Linhas | Leituras Base (med.) | Leituras Otim. (med.) | Redução E/S | Tempo Base med. ± DP (ms) | Tempo Otim. med. ± DP (ms) | Speedup | Teste / $p$-valor |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: | :---: | :--- |
| **Q1** | 1 | 2.856 | 6 | **99,79%** | $15{,}0 \pm 4{,}4$ | $0{,}0 \pm 0{,}0$ | **$>15\times$** (`<1 ms`) | Wilcoxon ($1{,}49 \times 10^{-6}$) |
| **Q2** | 6.028 | 8.090 | 34 | **99,58%** | $104{,}5 \pm 96{,}9$ | $1{,}5 \pm 1{,}8$ | **69,7$\times$** | Wilcoxon ($1{,}71 \times 10^{-6}$) |
| **Q3** | 3.198 | 8.090 | 17 | **99,79%** | $87{,}0 \pm 17{,}5$ | $1{,}0 \pm 0{,}6$ | **87,0$\times$** | Wilcoxon ($1{,}69 \times 10^{-6}$) |
| **Q4** | 422 | 8.090 | 5 | **99,94%** | $111{,}0 \pm 62{,}9$ | $0{,}0 \pm 0{,}3$ | **$>111\times$** (`<1 ms`) | Wilcoxon ($1{,}72 \times 10^{-6}$) |
| **Q5** | 4.965 | 28.818 | 5.295 | **81,63%** | $450{,}0 \pm 19{,}4$ | $12{,}0 \pm 2{,}4$ | **37,5$\times$** | Wilcoxon ($1{,}71 \times 10^{-6}$) |
| **Q6** | 50 | 8.090 | 3 | **99,96%** | $424{,}0 \pm 25{,}0$ | $0{,}0 \pm 0{,}0$ | **$>424\times$** (`<1 ms`) | Wilcoxon ($1{,}73 \times 10^{-6}$) |
| **Q7** | 6 | 8.090 | 5.658 | **30,06%** | $217{,}0 \pm 11{,}8$ | $364{,}0 \pm 36{,}0$ | **0,60$\times$** | Wilcoxon ($1{,}73 \times 10^{-6}$) |
| **Q8** | 2.002 | 637 | 28 | **95,60%** | $114{,}0 \pm 3{,}6$ | $1{,}0 \pm 0{,}4$ | **114,0$\times$** | $t$-Student ($3{,}45 \times 10^{-45}$) |
| **Q9** | 1 | 8.090 | 1.565 | **80,66%** | $226{,}0 \pm 17{,}9$ | $26{,}0 \pm 1{,}8$ | **8,69$\times$** | Wilcoxon ($1{,}72 \times 10^{-6}$) |
| **Q10** | 10.060 | 10.946 | 8.252 | **24,61%** | $370{,}5 \pm 34{,}2$ | $219{,}5 \pm 23{,}9$ | **1,69$\times$** | Wilcoxon ($1{,}72 \times 10^{-6}$) |
| **W1** | 10.000 | 97.154 | 180.057 | **-85,33%** | $384{,}0 \pm 113{,}9$ | $404{,}0 \pm 853{,}2$ | **0,95$\times$** | Wilcoxon ($0{,}129$) |

### 4.2. Resultados Complementares — *Cold Cache* ($N = 10$ por cenário)
Em leitura fria após limpeza explícita de *buffers* e cache de planos:
- **Ganhos expressivos e estatisticamente significativos ($p < 0{,}002$):** `Q6` ($772{,}0 \rightarrow 2{,}0$ ms, **386,0$\times$**), `Q4` ($194{,}0 \rightarrow 2{,}0$ ms, **97,0$\times$**), `Q2` ($281{,}5 \rightarrow 6{,}0$ ms, **46,9$\times$**), `Q8` ($207{,}0 \rightarrow 5{,}0$ ms, **41,4$\times$**), `Q3` ($246{,}5 \rightarrow 6{,}5$ ms, **37,9$\times$**), `Q1` ($44{,}0 \rightarrow 3{,}5$ ms, **12,6$\times$**), `Q9` ($588{,}0 \rightarrow 74{,}5$ ms, **7,89$\times$**), `Q5` ($1.027{,}5 \rightarrow 237{,}5$ ms, **4,33$\times$**) e `Q10` ($715{,}0 \rightarrow 443{,}0$ ms, **1,61$\times$**).
- **Trade-offs acentuados:** `Q7` ($402{,}0 \rightarrow 685{,}0$ ms, **0,59$\times$**, $p = 1{,}64 \times 10^{-7}$) e `W1` ($77.448{,}5 \rightarrow 282.476{,}0$ leituras lógicas, **-264,73%**; latência mediana $502{,}0 \rightarrow 1.098{,}5$ ms, **0,46$\times$**, $p = 0{,}00195$).

### 4.3. Estudo de Caso em 3 Estágios (`Q4`) e *Trade-offs* Críticos
- **Eliminação progressiva do *Key Lookup* (`Q4`, 422 linhas):**
  1. *Baseline* (`PK_Pedidos`, `Clustered Index Scan`): **8.090** leituras lógicas, mediana **111,0 ms**.
  2. *Intermediário* (`IX_Pedidos_ClienteID` sem `INCLUDE`, `Index Seek` + 422 `Key Lookups`): **1.296** leituras lógicas, **1 ms**.
  3. *Otimizado* (`IX_Pedidos_ClienteID_Cov` com `INCLUDE (DataPedido, ValorTotal)`, `Index Seek` puro): **5** leituras lógicas (**-99,61%** frente ao estágio intermediário e **-99,94%** frente ao *Baseline*), mediana **$<1$ ms**.
- **Análise crítica de `Q7` (*Batch Mode on Rowstore* vs. *Row Mode*):** Embora `IX_Pedidos_Status_Cov` tenha reduzido E/S em **30,06%** ($8.090 \rightarrow 5.658$ páginas) e substituído o plano de custo estimado `12,640` (*Hash Match* em *Batch Mode*) por custo estimado `6,728` (*Index Scan* ordenado + *Stream Aggregate*), a execução tupla-a-tupla do `Stream Aggregate` em *Row Mode* sob `MAXDOP 1` resultou em maior custo de CPU e latência superior ($217{,}0 \rightarrow 364{,}0$ ms).
- **Amplificação de escrita em `W1`:** O plano otimizado emprega operador `Sequence` mantendo **4 B+ Trees** (`PK_ItensPedido`, `IX_ItensPedido_PedidoID`, `IX_ItensPedido_ProdutoID` e 1.964/10.000 linhas no índice filtrado `IX_ItensPedido_Desconto_Alto`), explicando a sobrecarga de **+85,33%** em *Warm* ($97.154 \rightarrow 180.057$ páginas) e **+264,73%** em *Cold*.

---

## 5. Verificação Automática dos Entregáveis Finais

1. **Artigo Científico ([compile_paper.py](../../scripts/compile_paper.py) $\rightarrow$ [latex_validation.json](../../results/latex_validation.json)):**
   - PDF: `paper/main.pdf` (**1.311.836 bytes**, **10 páginas**, teto 10 páginas).
   - `overfull_count = 0`, `undefined_warnings = []`, `bibtex_issues = []`.
   - Figuras validadas a **300 DPI** exatos (`fig1_leituras_logicas.png`, `fig2_tempos_execucao_boxplot.png`, `fig3_q4_tres_estagios.png`, `fig4_warm_vs_cold_cache.png`, `fig5_planos_execucao.png`).
   - Resultado final: **`"passed": true`**.
2. **Apresentação ([apresentacao.pdf](../../slides/apresentacao.pdf)):**
   - **13 páginas** em Beamer 16:9 (**1.485.698 bytes**), integrando todas as 5 figuras, **0 erros, 0 warnings, 0 `Overfull \hbox`/`\vbox`**.
3. **Kit da Demonstração ao Vivo ([test_demo_kit.py](../../scripts/test_demo_kit.py)):**
   - Código de saída `0` contra ambas as bases reais no Docker:
     - `01_q1_seek_vs_scan.sql`: `2856 -> 6` leituras lógicas (`1` linha); plano otimizado confirma `Index Seek` + `Key Lookup`.
     - `02_q3_indice_composto.sql`: `8090 -> 17` leituras lógicas (`3198` linhas); plano otimizado confirma `Index Seek` em `IX_Pedidos_Status_Data` sem `Key Lookup`.
     - `03_q4_eliminacao_key_lookup.sql`: `8090 -> 5` leituras lógicas (`422` linhas); plano otimizado exato `["Index Seek (Pedidos.IX_Pedidos_ClienteID_Cov)"]` com `has_lookup = False` (e verificação negativa confirmando `has_key_lookup = True` em `q4_intermediate_lookup.sqlplan`).
     - `04_w1_tradeoff_escrita.sql`: confirma `Sequence` com manutenção de 4 B+ Trees e preserva exatas **4.500.000** linhas em `dbo.ItensPedido` pós-`ROLLBACK` em ambas as bases (`@@TRANCOUNT == 0`).
4. **Integridade de Codificação e Diretórios:**
   - Documentação e arquivos de planejamento consolidados em `cerebro/` (`comparativo-sgbds.md` em `06-experimentacao/` e `plano-de-implementacao.md` em `02-planejamento/`), sem links relativos quebrados e terminadores padronizados em `LF` (`crlf=0`).

---

## 6. Matriz Rápida de Riscos Residuais e Contingências

- **Falha de container/rede na apresentação ao vivo:** utilizar **Plano B** com os 23 arquivos `.sqlplan` pré-capturados em `results/plans/` (`README_CONTINGENCIA.md`) ou **Plano C** (vídeo MP4 gravado previamente pela equipe).
- **Mutação acidental da base durante a demo:** blindada por `SET XACT_ABORT ON;` e `BEGIN TRANSACTION ... ROLLBACK TRANSACTION;` em `04_w1_tradeoff_escrita.sql`.
- **Diferenças de plataforma (Windows / Ubuntu):** todo o pipeline utiliza Docker Compose, `uv`, `pymssql`, `pathlib.Path`, nomenclatura `snake_case` e finais de linha `LF`.

---

## 7. Ações Manuais Pendentes (Responsabilidade Exclusiva da Equipe)

1. **Autores e filiações reais:** substituir o placeholder `\author{Equipe de Banco de Dados II}` (e e-mail) em [paper/main.tex](../../paper/main.tex) e [slides/apresentacao.tex](../../slides/apresentacao.tex), e recompilar (`uv run python scripts/compile_paper.py` e `pdflatex` em `slides/`).
2. **Submissão formal do artigo:** enviar `paper/main.pdf` pelo canal oficial da disciplina até **17/11/2026**.
3. **Vídeo backup e defesa oral:** gravar `slides/demo_backup_local.mp4` (captura de tela dos 4 scripts em execução conforme Seção 4 de [README_CONTINGENCIA.md](../../scripts/demo/README_CONTINGENCIA.md)) e realizar a apresentação oral nos dias **18 ou 19/11/2026**.
