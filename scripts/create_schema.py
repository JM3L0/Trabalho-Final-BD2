"""Parte 2.1: Cria a base Ecommerce_Baseline e o esquema relacional E-Commerce B2C."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.db import get_connection

SQL_FILE = ROOT_DIR / "scripts" / "sql" / "01_create_baseline_db.sql"


def _split_batches(sql_text: str) -> list[str]:
    """Divide script T-SQL em lotes separados por linhas contendo apenas GO."""
    batches = re.split(r"^\s*GO\s*$", sql_text, flags=re.IGNORECASE | re.MULTILINE)
    return [batch.strip() for batch in batches if batch.strip()]


def create_schema() -> None:
    """Executa o DDL da base Ecommerce_Baseline e valida tabelas, PKs e FKs."""
    sql_text = SQL_FILE.read_text(encoding="utf-8")
    batches = _split_batches(sql_text)

    with get_connection("master", autocommit=True) as conn:
        with conn.cursor() as cur:
            for batch in batches:
                cur.execute(batch)

    with get_connection("Ecommerce_Baseline", autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT t.name, COUNT(c.column_id) AS col_count
                FROM sys.tables t
                JOIN sys.columns c ON t.object_id = c.object_id
                GROUP BY t.name
                ORDER BY t.name;
                """
            )
            tables = cur.fetchall()
            cur.execute(
                """
                SELECT name, type_desc
                FROM sys.indexes
                WHERE object_id IN (SELECT object_id FROM sys.tables)
                  AND type > 0
                ORDER BY name;
                """
            )
            indexes = cur.fetchall()
            cur.execute("SELECT name FROM sys.foreign_keys ORDER BY name;")
            fks = cur.fetchall()

    print("[OK] Tabelas em Ecommerce_Baseline:", tables)
    print("[OK] Indices (somente PKs):", indexes)
    print("[OK] Chaves estrangeiras:", [r[0] for r in fks])


if __name__ == "__main__":
    create_schema()
