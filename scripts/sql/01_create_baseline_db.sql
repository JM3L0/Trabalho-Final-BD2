-- Parte 2.1: Definicao do Esquema Relacional (E-Commerce B2C) na base Ecommerce_Baseline
-- Nao cria indices secundarios (apenas chaves primarias clustered e restricoes de integridade).

IF DB_ID(N'Ecommerce_Baseline') IS NULL
BEGIN
    CREATE DATABASE [Ecommerce_Baseline];
END;
GO

ALTER DATABASE [Ecommerce_Baseline] SET RECOVERY SIMPLE;
GO

USE [Ecommerce_Baseline];
GO

IF OBJECT_ID(N'dbo.ItensPedido', N'U') IS NOT NULL DROP TABLE dbo.ItensPedido;
IF OBJECT_ID(N'dbo.Pedidos', N'U') IS NOT NULL DROP TABLE dbo.Pedidos;
IF OBJECT_ID(N'dbo.Produtos', N'U') IS NOT NULL DROP TABLE dbo.Produtos;
IF OBJECT_ID(N'dbo.Clientes', N'U') IS NOT NULL DROP TABLE dbo.Clientes;
GO

CREATE TABLE dbo.Clientes (
    ClienteID    INT           NOT NULL,
    Nome         NVARCHAR(120) NOT NULL,
    Email        VARCHAR(150)  NOT NULL,
    Cidade       NVARCHAR(80)  NOT NULL,
    Estado       CHAR(2)       NOT NULL,
    DataCadastro DATE          NOT NULL,
    CONSTRAINT PK_Clientes PRIMARY KEY CLUSTERED (ClienteID)
);
GO

CREATE TABLE dbo.Produtos (
    ProdutoID INT            NOT NULL,
    Nome      NVARCHAR(150)  NOT NULL,
    Categoria NVARCHAR(60)   NOT NULL,
    Preco     DECIMAL(10, 2) NOT NULL,
    Estoque   INT            NOT NULL,
    CONSTRAINT PK_Produtos PRIMARY KEY CLUSTERED (ProdutoID)
);
GO

CREATE TABLE dbo.Pedidos (
    PedidoID   INT            NOT NULL,
    ClienteID  INT            NOT NULL,
    DataPedido DATETIME2(0)   NOT NULL,
    Status     VARCHAR(20)    NOT NULL,
    ValorTotal DECIMAL(12, 2) NOT NULL,
    CONSTRAINT PK_Pedidos PRIMARY KEY CLUSTERED (PedidoID),
    CONSTRAINT FK_Pedidos_Clientes FOREIGN KEY (ClienteID) REFERENCES dbo.Clientes (ClienteID)
);
GO

CREATE TABLE dbo.ItensPedido (
    ItemPedidoID  INT            NOT NULL,
    PedidoID      INT            NOT NULL,
    ProdutoID     INT            NOT NULL,
    Quantidade    SMALLINT       NOT NULL,
    PrecoUnitario DECIMAL(10, 2) NOT NULL,
    Desconto      DECIMAL(5, 2)  NOT NULL,
    CONSTRAINT PK_ItensPedido PRIMARY KEY CLUSTERED (ItemPedidoID),
    CONSTRAINT FK_ItensPedido_Pedidos FOREIGN KEY (PedidoID) REFERENCES dbo.Pedidos (PedidoID),
    CONSTRAINT FK_ItensPedido_Produtos FOREIGN KEY (ProdutoID) REFERENCES dbo.Produtos (ProdutoID)
);
GO
