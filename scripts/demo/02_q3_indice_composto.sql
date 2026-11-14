-- =============================================================================
-- Demo 02 (Q3): Indice Composto (Status por igualdade + DataPedido por faixa)
-- Slide 12 (Pag. 12) | Tempo alvo: ~1 min
-- Instrucao no VS Code (ms-mssql): ative "Enable Actual Plan" antes de executar.
-- =============================================================================

SET NOCOUNT OFF;
SET STATISTICS IO, TIME ON;
GO

USE Ecommerce_Baseline;
GO
-- [1/2] Baseline (Clustered Index Scan integral em PK_Pedidos: 8.090 paginas)
SELECT PedidoID, Status, DataPedido
FROM dbo.Pedidos
WHERE Status = 'ENTREGUE'
  AND DataPedido >= '2026-10-25'
  AND DataPedido < '2026-11-01'
OPTION (MAXDOP 1);
GO

USE Ecommerce_Otimizado;
GO
-- [2/2] Otimizado (Index Seek puro no indice composto IX_Pedidos_Status_Data)
SELECT PedidoID, Status, DataPedido
FROM dbo.Pedidos
WHERE Status = 'ENTREGUE'
  AND DataPedido >= '2026-10-25'
  AND DataPedido < '2026-11-01'
OPTION (MAXDOP 1);
GO

SET STATISTICS IO, TIME OFF;
GO
