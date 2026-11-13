# Metodologia e análise estatística

Objetivo: resultados reprodutíveis e detalhados.

## Registrar no paper
- Hardware (CPU, RAM, tipo de disco), SO, **versão exata** do SGBD (`SELECT @@VERSION;`), configurações (memória do container/SQL Server, paralelismo `MAXDOP`).
- Dataset: origem, linhas por tabela, tamanho em disco (`sp_spaceused`), esquema.
- Texto das consultas e DDL dos índices.
- Cache: cold com `CHECKPOINT; DBCC DROPCLEANBUFFERS;` (SQL Server, só em ambiente de teste; opcionalmente `DBCC FREEPROCCACHE;` quando quiser testar recompilação); warm repetindo a execução.
- Métricas: tempo decorrido (`elapsed time`), CPU (`CPU time`), leituras lógicas/físicas (`SET STATISTICS IO, TIME ON`), custo estimado e plano real (`SET STATISTICS XML ON` + plano gráfico no SSMS/VS Code `mssql`).

## Protocolo
1. Carregar dados e atualizar estatísticas.
2. **Baseline** sem índices secundários: capturar plano e métricas.
3. Aplicar **uma** otimização por vez (índice simples, composto, covering, reescrita).
4. Capturar plano e métricas, repetindo N vezes.
5. Medir o custo de escrita (INSERT/UPDATE) com os índices.
6. Comparar e explicar pelo plano.

## Estatística
- N ≥ 30 repetições por cenário (descartar a primeira se warm). É sugestão, não exigência.
- Reportar média, mediana, desvio padrão, mín/máx e IC 95%.
- Speedup = t_antes / t_depois; redução % de leituras lógicas.
- Comparação: teste t pareado ou Wilcoxon (se não normal), com p-valor.
- Boxplot ou barras com erro, e tabela antes/depois. Script Python/R versionado.
