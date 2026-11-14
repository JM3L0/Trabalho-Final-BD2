-- =============================================================================
-- Demo 03 (Q4): Eliminacao de Key Lookup com Covering Index (INCLUDE)
-- Slide 12 (Pag. 12) | Tempo alvo: ~1 min
-- Instrucao no VS Code (ms-mssql): ative "Enable Actual Plan" antes de executar.
-- Nota: compare tambem o plano intermediario em results/plans/optimized/q4_intermediate_lookup.sqlplan
-- =============================================================================

SET NOCOUNT OFF;
SET STATISTICS IO, TIME ON;
GO

USE Ecommerce_Baseline;
GO
-- [1/2] Baseline (Clustered Index Scan em PK_Pedidos: 8.090 paginas para 422 linhas)
SELECT ClienteID, DataPedido, ValorTotal
FROM dbo.Pedidos
WHERE ClienteID BETWEEN 1000 AND 1050
OPTION (MAXDOP 1);
GO

USE Ecommerce_Otimizado;
GO
-- [2/2] Otimizado (Index Seek sem Key Lookup em IX_Pedidos_ClienteID_Cov INCLUDE (DataPedido, ValorTotal))
SELECT ClienteID, DataPedido, ValorTotal
FROM dbo.Pedidos
WHERE ClienteID BETWEEN 1000 AND 1050
OPTION (MAXDOP 1);
GO

SET STATISTICS IO, TIME OFF;
GO
