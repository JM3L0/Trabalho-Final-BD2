-- Parte 2.3: Carga massiva otimizada em Ecommerce_Baseline via BULK INSERT
-- Nota: No SQL Server em Linux (container Docker), CODEPAGE = '65001' nao e suportado (erro 16202).
-- Para preservar acentos UTF-8 em Clientes e Produtos, o load_baseline.py gera temporarios UTF-16
-- carregados com DATAFILETYPE = 'widechar', enquanto Pedidos e ItensPedido (ASCII) usam DATAFILETYPE = 'char'.
ALTER DATABASE [Ecommerce_Baseline] SET RECOVERY SIMPLE;
GO

USE [Ecommerce_Baseline];
GO

-- Garante idempotencia caso o script seja reexecutado
DELETE FROM dbo.ItensPedido;
DELETE FROM dbo.Pedidos;
DELETE FROM dbo.Produtos;
DELETE FROM dbo.Clientes;
GO

BULK INSERT dbo.Clientes
FROM '/var/opt/mssql/data_import/_clientes_u16.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    DATAFILETYPE = 'widechar',
    BATCHSIZE = 100000,
    TABLOCK,
    CHECK_CONSTRAINTS
);
GO

BULK INSERT dbo.Produtos
FROM '/var/opt/mssql/data_import/_produtos_u16.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    DATAFILETYPE = 'widechar',
    BATCHSIZE = 100000,
    TABLOCK,
    CHECK_CONSTRAINTS
);
GO

BULK INSERT dbo.Pedidos
FROM '/var/opt/mssql/data_import/pedidos.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '0x0a',
    DATAFILETYPE = 'char',
    BATCHSIZE = 100000,
    TABLOCK,
    CHECK_CONSTRAINTS
);
GO

BULK INSERT dbo.ItensPedido
FROM '/var/opt/mssql/data_import/itens_pedido.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '0x0a',
    DATAFILETYPE = 'char',
    BATCHSIZE = 100000,
    TABLOCK,
    CHECK_CONSTRAINTS
);
GO

-- Atualiza estatisticas, valida integridade referencial e compacta log em modo SIMPLE
EXEC sp_updatestats;
GO
DBCC CHECKCONSTRAINTS WITH ALL_CONSTRAINTS;
GO
CHECKPOINT;
DBCC SHRINKFILE (N'Ecommerce_Baseline_log', 64);
GO
