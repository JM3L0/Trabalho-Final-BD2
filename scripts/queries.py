"""Parte 3.1: Catalogo oficial de consultas de benchmark (Q1 a Q10 e W1)."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.db import get_connection


@dataclass(frozen=True)
class QuerySpec:
    """Definicao de um cenario de benchmark (Baseline vs Otimizado)."""

    code: str
    title: str
    category: str
    sql_baseline: str
    sql_optimized: str
    is_dml_write: bool = False
    sql_intermediate: str | None = None
    notes: str = ""


QUERIES: tuple[QuerySpec, ...] = (
    QuerySpec(
        code="Q1",
        title="Filtro simples em coluna nao indexada (Email)",
        category="Indice Simples (Scan vs Seek)",
        sql_baseline=(
            "SELECT ClienteID, Nome, Email, Cidade, Estado "
            "FROM dbo.Clientes "
            "WHERE Email = 'cliente_125432@exemplo.com.br' "
            "OPTION (MAXDOP 1);"
        ),
        sql_optimized=(
            "SELECT ClienteID, Nome, Email, Cidade, Estado "
            "FROM dbo.Clientes "
            "WHERE Email = 'cliente_125432@exemplo.com.br' "
            "OPTION (MAXDOP 1);"
        ),
        notes="Usa literal VARCHAR sem prefixo N para evitar CONVERT_IMPLICIT.",
    ),
    QuerySpec(
        code="Q2",
        title="Filtro seletivo por faixa de datas em Pedidos",
        category="Indice Simples Range (Scan vs Seek)",
        sql_baseline=(
            "SELECT PedidoID, DataPedido "
            "FROM dbo.Pedidos "
            "WHERE DataPedido >= '2025-06-01' AND DataPedido < '2025-06-08' "
            "OPTION (MAXDOP 1);"
        ),
        sql_optimized=(
            "SELECT PedidoID, DataPedido "
            "FROM dbo.Pedidos "
            "WHERE DataPedido >= '2025-06-01' AND DataPedido < '2025-06-08' "
            "OPTION (MAXDOP 1);"
        ),
        notes="Projecao coberta pela chave do indice (PedidoID + DataPedido) sem Key Lookup.",
    ),
    QuerySpec(
        code="Q3",
        title="Filtro composto por Status (igualdade) e DataPedido (faixa)",
        category="Indice Composto (Ordem de Colunas)",
        sql_baseline=(
            "SELECT PedidoID, Status, DataPedido "
            "FROM dbo.Pedidos "
            "WHERE Status = 'ENTREGUE' "
            "AND DataPedido >= '2026-10-25' AND DataPedido < '2026-11-01' "
            "OPTION (MAXDOP 1);"
        ),
        sql_optimized=(
            "SELECT PedidoID, Status, DataPedido "
            "FROM dbo.Pedidos "
            "WHERE Status = 'ENTREGUE' "
            "AND DataPedido >= '2026-10-25' AND DataPedido < '2026-11-01' "
            "OPTION (MAXDOP 1);"
        ),
        notes="Indice composto (Status, DataPedido): igualdade primeiro, faixa depois.",
    ),
    QuerySpec(
        code="Q4",
        title="Projecao restrita por ClienteID (Eliminacao de Key Lookup)",
        category="Covering Index (INCLUDE)",
        sql_baseline=(
            "SELECT ClienteID, DataPedido, ValorTotal "
            "FROM dbo.Pedidos "
            "WHERE ClienteID BETWEEN 1000 AND 1050 "
            "OPTION (MAXDOP 1);"
        ),
        sql_intermediate=(
            "SELECT ClienteID, DataPedido, ValorTotal "
            "FROM dbo.Pedidos "
            "WHERE ClienteID BETWEEN 1000 AND 1050 "
            "OPTION (MAXDOP 1);"
        ),
        sql_optimized=(
            "SELECT ClienteID, DataPedido, ValorTotal "
            "FROM dbo.Pedidos "
            "WHERE ClienteID BETWEEN 1000 AND 1050 "
            "OPTION (MAXDOP 1);"
        ),
        notes="Cenario intermediario usa indice simples (ClienteID) gerando Key Lookup antes de aplicar INCLUDE.",
    ),
    QuerySpec(
        code="Q5",
        title="Juncao de 3 tabelas (Clientes, Pedidos, ItensPedido)",
        category="Operadores de Juncao (Hash Match vs Nested Loops)",
        sql_baseline=(
            "SELECT c.ClienteID, c.Nome, p.PedidoID, p.DataPedido, "
            "i.ProdutoID, i.Quantidade, i.PrecoUnitario "
            "FROM dbo.Clientes c "
            "INNER JOIN dbo.Pedidos p ON p.ClienteID = c.ClienteID "
            "INNER JOIN dbo.ItensPedido i ON i.PedidoID = p.PedidoID "
            "WHERE c.ClienteID BETWEEN 1000 AND 1200 "
            "OPTION (MAXDOP 1);"
        ),
        sql_optimized=(
            "SELECT c.ClienteID, c.Nome, p.PedidoID, p.DataPedido, "
            "i.ProdutoID, i.Quantidade, i.PrecoUnitario "
            "FROM dbo.Clientes c "
            "INNER JOIN dbo.Pedidos p ON p.ClienteID = c.ClienteID "
            "INNER JOIN dbo.ItensPedido i ON i.PedidoID = p.PedidoID "
            "WHERE c.ClienteID BETWEEN 1000 AND 1200 "
            "OPTION (MAXDOP 1);"
        ),
        notes="Indices nas FKs eliminam scans e Hash Match sobre 6M de linhas.",
    ),
    QuerySpec(
        code="Q6",
        title="Paginacao dos 50 pedidos mais recentes (TOP 50 ORDER BY DataPedido DESC)",
        category="Eliminacao de Sort",
        sql_baseline=(
            "SELECT TOP 50 PedidoID, ClienteID, DataPedido, Status, ValorTotal "
            "FROM dbo.Pedidos "
            "ORDER BY DataPedido DESC "
            "OPTION (MAXDOP 1);"
        ),
        sql_optimized=(
            "SELECT TOP 50 PedidoID, ClienteID, DataPedido, Status, ValorTotal "
            "FROM dbo.Pedidos "
            "ORDER BY DataPedido DESC "
            "OPTION (MAXDOP 1);"
        ),
        notes="B-Tree em DataPedido permite Backward Scan ordenado sem Sort.",
    ),
    QuerySpec(
        code="Q7",
        title="Agregacao de faturamento por Status (GROUP BY Status)",
        category="Agregacao (Hash Aggregate vs Stream Aggregate)",
        sql_baseline=(
            "SELECT Status, COUNT(*) AS QtdPedidos, SUM(ValorTotal) AS FaturamentoTotal "
            "FROM dbo.Pedidos "
            "GROUP BY Status "
            "OPTION (MAXDOP 1);"
        ),
        sql_optimized=(
            "SELECT Status, COUNT(*) AS QtdPedidos, SUM(ValorTotal) AS FaturamentoTotal "
            "FROM dbo.Pedidos "
            "GROUP BY Status "
            "OPTION (MAXDOP 1);"
        ),
        notes="Covering index (Status) INCLUDE (ValorTotal) habilita Stream Aggregate.",
    ),
    QuerySpec(
        code="Q8",
        title="Busca textual em Produtos (LIKE '%Notebook%' vs LIKE 'Notebook%')",
        category="Sargabilidade Textual",
        sql_baseline=(
            "SELECT ProdutoID, Nome, Categoria, Preco "
            "FROM dbo.Produtos "
            "WHERE Nome LIKE N'%Notebook%' "
            "OPTION (MAXDOP 1);"
        ),
        sql_optimized=(
            "SELECT ProdutoID, Nome, Categoria, Preco "
            "FROM dbo.Produtos "
            "WHERE Nome LIKE N'Notebook%' "
            "OPTION (MAXDOP 1);"
        ),
        notes="Nome e NVARCHAR(150), portanto N'...' evita conversao implicita; reescrita para prefixo habilita Seek.",
    ),
    QuerySpec(
        code="Q9",
        title="Filtro temporal com funcao no WHERE (YEAR(DataPedido) = 2025)",
        category="Sargabilidade Temporal",
        sql_baseline=(
            "SELECT COUNT(*) AS TotalPedidos2025 "
            "FROM dbo.Pedidos "
            "WHERE YEAR(DataPedido) = 2025 "
            "OPTION (MAXDOP 1);"
        ),
        sql_optimized=(
            "SELECT COUNT(*) AS TotalPedidos2025 "
            "FROM dbo.Pedidos "
            "WHERE DataPedido >= '2025-01-01' AND DataPedido < '2026-01-01' "
            "OPTION (MAXDOP 1);"
        ),
        notes="Reescrita sargable em intervalo semiaberto preserva exatidao de COUNT(*).",
    ),
    QuerySpec(
        code="Q10",
        title="Clientes sem pedidos (Subconsulta correlacionada vs NOT EXISTS)",
        category="Otimizacao Logica de Subconsulta",
        sql_baseline=(
            "SELECT c.ClienteID, c.Nome, c.Email "
            "FROM dbo.Clientes c "
            "WHERE (SELECT MAX(p.DataPedido) FROM dbo.Pedidos p WHERE p.ClienteID = c.ClienteID) IS NULL "
            "OPTION (MAXDOP 1);"
        ),
        sql_optimized=(
            "SELECT c.ClienteID, c.Nome, c.Email "
            "FROM dbo.Clientes c "
            "WHERE NOT EXISTS (SELECT 1 FROM dbo.Pedidos p WHERE p.ClienteID = c.ClienteID) "
            "OPTION (MAXDOP 1);"
        ),
        notes="Com Pedidos.ClienteID NOT NULL, subconsulta agregada correlacionada vs NOT EXISTS gera planos distintos.",
    ),
    QuerySpec(
        code="W1",
        title="Insercao massiva em ItensPedido (10.000 linhas com ROLLBACK)",
        category="Trade-off de Escrita (Manutencao de B+ Trees)",
        sql_baseline=(
            "INSERT INTO dbo.ItensPedido (ItemPedidoID, PedidoID, ProdutoID, Quantidade, PrecoUnitario, Desconto) "
            "SELECT ItemPedidoID + 4500000, PedidoID, ProdutoID, Quantidade, PrecoUnitario, Desconto "
            "FROM dbo.ItensPedido "
            "WHERE ItemPedidoID <= 10000 "
            "OPTION (MAXDOP 1);"
        ),
        sql_optimized=(
            "INSERT INTO dbo.ItensPedido (ItemPedidoID, PedidoID, ProdutoID, Quantidade, PrecoUnitario, Desconto) "
            "SELECT ItemPedidoID + 4500000, PedidoID, ProdutoID, Quantidade, PrecoUnitario, Desconto "
            "FROM dbo.ItensPedido "
            "WHERE ItemPedidoID <= 10000 "
            "OPTION (MAXDOP 1);"
        ),
        is_dml_write=True,
        notes="Executada dentro de BEGIN TRAN ... ROLLBACK TRAN; metricas coletadas apenas do INSERT.",
    ),
)

QUERY_MAP: dict[str, QuerySpec] = {q.code: q for q in QUERIES}


def validate_syntax() -> None:
    """Valida sintaxe T-SQL e compilacao (SET NOEXEC ON) de todas as consultas no SQL Server."""
    with get_connection("Ecommerce_Baseline", autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SET NOEXEC ON;")
            try:
                for q in QUERIES:
                    for label, sql in (("baseline", q.sql_baseline), ("optimized", q.sql_optimized)):
                        if "OPTION (MAXDOP 1)" not in sql:
                            raise ValueError(f"{q.code} ({label}) sem OPTION (MAXDOP 1)")
                        cur.execute(sql)
                        while cur.nextset():
                            pass
                    print(f"[OK] {q.code} ({q.title}) validada via NOEXEC.")
            finally:
                cur.execute("SET NOEXEC OFF;")


if __name__ == "__main__":
    validate_syntax()
