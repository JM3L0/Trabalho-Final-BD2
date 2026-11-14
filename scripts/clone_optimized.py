"""Parte 2.4: Realiza backup da Ecommerce_Baseline e restaura a base gemea Ecommerce_Otimizado."""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.db import DATA_DIR, get_connection

SQL_FILE = ROOT_DIR / "scripts" / "sql" / "03_backup_and_clone.sql"


def _split_batches(sql_text: str) -> list[str]:
    """Divide script T-SQL em lotes separados por GO."""
    batches = re.split(r"^\s*GO\s*$", sql_text, flags=re.IGNORECASE | re.MULTILINE)
    return [batch.strip() for batch in batches if batch.strip()]


def _fetch_counts(database: str) -> dict[str, int]:
    """Retorna contagem exata das 4 tabelas da base informada."""
    with get_connection(database, autocommit=True, timeout=0) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 'Clientes' AS Tabela, COUNT(*) AS Total FROM dbo.Clientes
                UNION ALL SELECT 'Produtos', COUNT(*) FROM dbo.Produtos
                UNION ALL SELECT 'Pedidos', COUNT(*) FROM dbo.Pedidos
                UNION ALL SELECT 'ItensPedido', COUNT(*) FROM dbo.ItensPedido;
                """
            )
            return dict(cur.fetchall())


def clone_optimized(cleanup_csv: bool = False) -> None:
    """Executa BACKUP/RESTORE nativo e valida igualdade entre Baseline e Otimizado."""
    t0 = time.perf_counter()
    sql_text = SQL_FILE.read_text(encoding="utf-8")
    batches = _split_batches(sql_text)

    with get_connection("master", autocommit=True, timeout=0) as conn:
        with conn.cursor() as cur:
            for batch in batches:
                cur.execute(batch)
                while cur.nextset():
                    pass

    bak_path = DATA_DIR / "ecommerce_init.bak"
    if not bak_path.exists():
        raise FileNotFoundError(f"Backup esperado nao encontrado no host: {bak_path}")

    counts_base = _fetch_counts("Ecommerce_Baseline")
    counts_opt = _fetch_counts("Ecommerce_Otimizado")
    if counts_base != counts_opt:
        raise RuntimeError(f"Contagens divergem entre bases: base={counts_base}, opt={counts_opt}")

    with get_connection("Ecommerce_Otimizado", autocommit=True, timeout=0) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT name, is_not_trusted, is_disabled FROM sys.foreign_keys ORDER BY name;")
            fks = cur.fetchall()
            cur.execute("SELECT TOP 2 ClienteID, Cidade FROM dbo.Clientes ORDER BY ClienteID;")
            sample = cur.fetchall()
            cur.execute(
                "SELECT recovery_model_desc, state_desc FROM sys.databases WHERE name = 'Ecommerce_Otimizado';"
            )
            db_state = cur.fetchone()

    if cleanup_csv:
        for csv_name in ("clientes.csv", "produtos.csv", "pedidos.csv", "itens_pedido.csv"):
            csv_path = DATA_DIR / csv_name
            if csv_path.exists():
                csv_path.unlink()

    elapsed = time.perf_counter() - t0
    print(f"[OK] Clone Ecommerce_Otimizado concluido em {elapsed:.2f}s")
    print(f"[OK] Backup gerado: {bak_path} ({bak_path.stat().st_size / (1024**2):.2f} MiB)")
    print("[OK] Contagens identicas:", counts_opt)
    print("[OK] Estado Ecommerce_Otimizado:", db_state)
    print("[OK] FKs:", fks)
    print("[OK] Amostra acentuacao:", sample)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clona Ecommerce_Baseline para Ecommerce_Otimizado.")
    parser.add_argument(
        "--cleanup-csv",
        action="store_true",
        help="Remove os CSVs intermediarios de data/ apos validar o backup e a restauracao.",
    )
    args = parser.parse_args()
    clone_optimized(cleanup_csv=args.cleanup_csv)
