-- =============================================================================
-- Demo 01 (Q1): Index Seek vs. Clustered Index Scan (Busca Pontual por Email)
-- Slide 12 (Pag. 12) | Tempo alvo: ~1 min
-- Instrucao no VS Code (ms-mssql): ative "Enable Actual Plan" antes de executar.
-- =============================================================================

SET NOCOUNT OFF;
SET STATISTICS IO, TIME ON;
GO

USE Ecommerce_Baseline;
GO
-- [1/2] Baseline (0 indices secundarios -> Clustered Index Scan em PK_Clientes)
SELECT ClienteID, Nome, Email, Cidade, Estado
FROM dbo.Clientes
WHERE Email = 'cliente_125432@exemplo.com.br'
OPTION (MAXDOP 1);
GO

USE Ecommerce_Otimizado;
GO
-- [2/2] Otimizado (IX_Clientes_Email -> Index Seek + 1 Key Lookup)
SELECT ClienteID, Nome, Email, Cidade, Estado
FROM dbo.Clientes
WHERE Email = 'cliente_125432@exemplo.com.br'
OPTION (MAXDOP 1);
GO

SET STATISTICS IO, TIME OFF;
GO
