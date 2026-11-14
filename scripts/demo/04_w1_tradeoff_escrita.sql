-- =============================================================================
-- Demo 04 (W1): Trade-off de Escrita Massiva (10.000 INSERTs com ROLLBACK)
-- Slide 12 (Pag. 12) | Tempo alvo: ~1m30s
-- Instrucao no VS Code (ms-mssql): ative "Enable Actual Plan" antes de executar.
-- Seguranca: cada insercao roda isolada dentro de BEGIN TRAN ... ROLLBACK TRAN.
-- =============================================================================

SET NOCOUNT OFF;
SET XACT_ABORT ON;
GO

USE Ecommerce_Baseline;
GO
-- [1/2] Baseline: escrita apenas na B+ Tree clusterizada (PK_ItensPedido)
BEGIN TRANSACTION;
SET STATISTICS IO, TIME ON;
INSERT INTO dbo.ItensPedido (ItemPedidoID, PedidoID, ProdutoID, Quantidade, PrecoUnitario, Desconto)
SELECT ItemPedidoID + 4500000, PedidoID, ProdutoID, Quantidade, PrecoUnitario, Desconto
FROM dbo.ItensPedido
WHERE ItemPedidoID <= 10000
OPTION (MAXDOP 1);
SET STATISTICS IO, TIME OFF;
ROLLBACK TRANSACTION;
SELECT COUNT(*) AS TotalItensBaselineAposRollback FROM dbo.ItensPedido;
GO

USE Ecommerce_Otimizado;
GO
-- [2/2] Otimizado: Sequence atualiza 4 B+ Trees (PK + 2 FKs + indice filtrado Desconto >= 10)
BEGIN TRANSACTION;
SET STATISTICS IO, TIME ON;
INSERT INTO dbo.ItensPedido (ItemPedidoID, PedidoID, ProdutoID, Quantidade, PrecoUnitario, Desconto)
SELECT ItemPedidoID + 4500000, PedidoID, ProdutoID, Quantidade, PrecoUnitario, Desconto
FROM dbo.ItensPedido
WHERE ItemPedidoID <= 10000
OPTION (MAXDOP 1);
SET STATISTICS IO, TIME OFF;
ROLLBACK TRANSACTION;
SELECT COUNT(*) AS TotalItensOtimizadoAposRollback FROM dbo.ItensPedido;
GO
