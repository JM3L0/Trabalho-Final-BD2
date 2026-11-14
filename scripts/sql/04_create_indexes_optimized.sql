-- Parte 4.1: Aplicacao dos indices secundarios exclusivamente na base Ecommerce_Otimizado
-- A base Ecommerce_Baseline permanece estritamente sem indices secundarios.
USE [Ecommerce_Otimizado];
GO

-- Limpeza idempotente de indices secundarios existentes (preservando PKs)
DROP INDEX IF EXISTS IX_Clientes_Email ON dbo.Clientes;
DROP INDEX IF EXISTS IX_Produtos_Nome ON dbo.Produtos;
DROP INDEX IF EXISTS IX_Pedidos_DataPedido ON dbo.Pedidos;
DROP INDEX IF EXISTS IX_Pedidos_Status_Data ON dbo.Pedidos;
DROP INDEX IF EXISTS IX_Pedidos_ClienteID ON dbo.Pedidos;
DROP INDEX IF EXISTS IX_Pedidos_ClienteID_Cov ON dbo.Pedidos;
DROP INDEX IF EXISTS IX_Pedidos_Status_Cov ON dbo.Pedidos;
DROP INDEX IF EXISTS IX_ItensPedido_PedidoID ON dbo.ItensPedido;
DROP INDEX IF EXISTS IX_ItensPedido_ProdutoID ON dbo.ItensPedido;
DROP INDEX IF EXISTS IX_ItensPedido_Desconto_Alto ON dbo.ItensPedido;
GO

-- Q1: Indice nao-clusterizado simples em Email
CREATE NONCLUSTERED INDEX IX_Clientes_Email
    ON dbo.Clientes (Email);
GO

-- Q8: Indice nao-clusterizado cobridor em Produtos(Nome) para busca por prefixo (LIKE 'Notebook%')
CREATE NONCLUSTERED INDEX IX_Produtos_Nome
    ON dbo.Produtos (Nome)
    INCLUDE (Categoria, Preco);
GO

-- Q2, Q6, Q9: Indice nao-clusterizado em DataPedido cobrindo paginacao (Backward Scan sem Sort) e faixa temporal
CREATE NONCLUSTERED INDEX IX_Pedidos_DataPedido
    ON dbo.Pedidos (DataPedido)
    INCLUDE (ClienteID, Status, ValorTotal);
GO

-- Q3: Indice composto (igualdade primeiro, faixa depois)
CREATE NONCLUSTERED INDEX IX_Pedidos_Status_Data
    ON dbo.Pedidos (Status, DataPedido);
GO

-- Q4, Q5, Q10: Covering index em ClienteID eliminando Key Lookup
CREATE NONCLUSTERED INDEX IX_Pedidos_ClienteID_Cov
    ON dbo.Pedidos (ClienteID)
    INCLUDE (DataPedido, ValorTotal);
GO

-- Q7: Covering index em Status permitindo Stream Aggregate sem Hash Match
CREATE NONCLUSTERED INDEX IX_Pedidos_Status_Cov
    ON dbo.Pedidos (Status)
    INCLUDE (ValorTotal);
GO

-- Q5 e W1: Indices nas FKs e indice filtrado em ItensPedido
CREATE NONCLUSTERED INDEX IX_ItensPedido_PedidoID
    ON dbo.ItensPedido (PedidoID)
    INCLUDE (ProdutoID, Quantidade, PrecoUnitario);
GO

CREATE NONCLUSTERED INDEX IX_ItensPedido_ProdutoID
    ON dbo.ItensPedido (ProdutoID);
GO

CREATE NONCLUSTERED INDEX IX_ItensPedido_Desconto_Alto
    ON dbo.ItensPedido (ProdutoID, Desconto)
    WHERE Desconto >= 10.00;
GO

EXEC sp_updatestats;
GO
CHECKPOINT;
DBCC SHRINKFILE (N'Ecommerce_Baseline_log', 64);
GO
