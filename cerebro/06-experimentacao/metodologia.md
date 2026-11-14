# Metodologia Experimental e Analise Estatistica

Objetivo: Garantir resultados reproduziveis, estatisticamente confiaveis e metodologicamente rigorosos.

## 1. Variaveis e Registros Obrigatorios no Artigo
* **Ambiente de Execucao:** Hardware (CPU, RAM, SSD), sistema operacional (Windows/Ubuntu), versao exata do SGBD (`SELECT @@VERSION;`) e limites de recursos do container Docker.
* **Dataset:** Volume exato por tabela, semente pseudoaleatoria (`seed=42`), tamanho ocupado em disco (`sp_spaceused`) e esquema relacional E-Commerce B2C.
* **Estrategia Experimental:** Utilizacao de duas bases de dados identicas no mesmo servidor (`Ecommerce_Baseline` e `Ecommerce_Otimizado`), isolando o grupo de controle do grupo experimental.
* **Paralelismo Padronizado:** Fixacao do grau de paralelismo (`OPTION (MAXDOP 1)`) em todas as consultas para eliminar dispersao e variancia induzida por scheduling de threads da CPU.
* **Metrica Primaria Deterministica:** **Leituras Logicas (`logical reads`)** via `SET STATISTICS IO ON`, medindo com precisao de pagina (8 KB) o I/O no buffer pool, independente de flutuacoes termicas ou de carga na CPU do host. Metricas secundarias: tempo total decorrido (*elapsed time*) e tempo de CPU (*CPU time*).

---

## 2. Protocolo Experimental Automatizado

1. **Carga Inicial e Criacao do Clone:**
   * Carga dos dados sinteticos em `Ecommerce_Baseline` (apenas com chaves primarias).
   * Geracao do backup `ecommerce_init.bak` e restauracao com `WITH MOVE` para criar `Ecommerce_Otimizado`.
   * Atualizacao de estatisticas completas em ambas as bases (`sp_updatestats`).
2. **Aplicacao de Indices na Base Otimizada e Validacao Previa de Planos:**
   * Criacao de indices secundarios especificos (simples, compostos, covering com `INCLUDE` e filtrados) exclusivamente na base `Ecommerce_Otimizado`.
   * Execucao unica (`1x`) de cada consulta (Q1–Q10 e W1) com `SET STATISTICS XML ON` em ambas as bases (e cenario intermediario de Q4 sem `INCLUDE` para demonstrar o `Key Lookup`) para validar que os planos reais gerados pelo SQL Server correspondem ao comportamento esperado antes da bateria estatistica.
3. **Execucao do Benchmark Automatizado via Script Python (`scripts/run_benchmarks.py`):**
   * Alternancia de contexto via sessao (`USE Ecommerce_Baseline;` e `USE Ecommerce_Otimizado;`).
   * **Separacao entre Captura de Plano e Loop Estatistico:** O loop de repeticoes roda exclusivamente com `SET STATISTICS IO, TIME ON` (sem `STATISTICS XML ON` dentro do loop), evitando overhead de serializacao XML e mistura de result sets no `pymssql`.
   * **Controle de Cache:**
     * *Warm Cache (Bateria Principal):* $N \ge 30$ execucoes repetidas sequenciais por cenario, descartando as rodadas iniciais de aquecimento.
     * *Cold Cache (Bateria Complementar Calibrada):* Sanitizacao antes de cada medicao com `CHECKPOINT; DBCC DROPCLEANBUFFERS; DBCC FREEPROCCACHE;` (com $N = 5\text{ a }10$, ou $N = 30$ caso o tempo total dos scans em baseline permaneca curto), medindo I/O fisico real e recompilacao.
   * **Tratamento Especial para W1 (Operacoes DML de Escrita):**
     * Para que a tabela nao infle e distorca o tempo de insercao ao longo das 30 repeticoes, cada rodada de medicao de W1 sera executada dentro de uma transacao desfeita:
       `BEGIN TRANSACTION; ... medicao DML ...; ROLLBACK TRANSACTION;`.
     * Os contadores de `STATISTICS IO, TIME` devem ser coletados **exclusivamente do comando `INSERT` (antes do `ROLLBACK`)**.
4. **Captura dos Planos de Execucao:**
   * Extracao automatica do plano real em XML (`SET STATISTICS XML ON`) em passada dedicada e captura grafica dos operadores no cliente SQL (VS Code / SSMS / Azure Data Studio).

---

## 3. Analise Estatistica

* **Amostragem:** $N \ge 30$ repeticoes validas por cenario em *Warm Cache* para assegurar convergencia assintotica (Teorema Central do Limite), complementadas por rodadas em *Cold Cache*.
* **Medidas Descritivas:** Media, mediana, desvio padrao, minimo, maximo e intervalo de confianca de 95% ($IC_{95\%} = \bar{x} \pm 1,96 \cdot \frac{s}{\sqrt{N}}$).
* **Speedup e Reducao de I/O:**
  * $Speedup = \frac{Tempo_{Baseline}}{Tempo_{Otimizado}}$ (valores $< 1,0$ em `W1` indicam desaceleracao esperada na escrita)
  * $Reducao_{I/O} = \frac{Leituras_{Baseline} - Leituras_{Otimizado}}{Leituras_{Baseline}} \times 100\%$ (em `W1`, reportado como aumento/overhead percentual negativo)
* **Testes de Significancia Estatistica:**
  * Teste de normalidade de Shapiro-Wilk para os tempos de execucao.
  * Para distribuicoes com normalidade: **Teste t de Student pareado** (*paired t-test*).
  * Para distribuicoes assimetricas: **Teste dos postos com sinais de Wilcoxon** (*Wilcoxon signed-rank test*).
  * Reportar formalmente o valor de $p$ (ex.: $p < 0,001$).
* **Apresentacao dos Dados:** Tabela sintetica unificada no artigo em LaTeX e boxplots gerados via `scripts/generate_charts.py`.
