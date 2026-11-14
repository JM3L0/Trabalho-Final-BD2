"""Parte 2.3: Executa a carga massiva na base Ecommerce_Baseline e valida contagens e FKs."""

from __future__ import annotations

import re
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.db import DATA_DIR, get_connection

SQL_FILE = ROOT_DIR / "scripts" / "sql" / "02_bulk_load_baseline.sql"


def _split_batches(sql_text: str) -> list[str]:
    """Divide script T-SQL em lotes separados por GO."""
    batches = re.split(r"^\s*GO\s*$", sql_text, flags=re.IGNORECASE | re.MULTILINE)
    return [batch.strip() for batch in batches if batch.strip()]


def _prepare_utf16_temp(src: Path, dst: Path) -> None:
    """Converte CSV UTF-8 com LF para UTF-16 (com BOM) para carga widechar fiel no SQL Server Linux."""
    text = src.read_text(encoding="utf-8")
    dst.write_bytes(text.encode("utf-16"))
    try:
        dst.chmod(0o644)
    except OSError:
        pass


def load_baseline() -> None:
    """Executa BULK INSERT e valida totais de linhas, FKs confiaveis, acentuacao e espaco."""
    t0 = time.perf_counter()
    sql_text = SQL_FILE.read_text(encoding="utf-8")
    batches = _split_batches(sql_text)

    temp_files = [
        (DATA_DIR / "clientes.csv", DATA_DIR / "_clientes_u16.csv"),
        (DATA_DIR / "produtos.csv", DATA_DIR / "_produtos_u16.csv"),
    ]
    for src, dst in temp_files:
        _prepare_utf16_temp(src, dst)

    try:
        with get_connection("master", autocommit=True, timeout=0) as conn:
            with conn.cursor() as cur:
                for batch in batches:
                    is_check_batch = "DBCC CHECKCONSTRAINTS" in batch.upper()
                    cur.execute(batch)
                    if is_check_batch and cur.description is not None:
                        violations = cur.fetchall()
                        if violations:
                            raise RuntimeError(f"Violacoes de integridade encontradas: {violations}")
                    while cur.nextset():
                        if is_check_batch and cur.description is not None:
                            violations = cur.fetchall()
                            if violations:
                                raise RuntimeError(f"Violacoes de integridade encontradas: {violations}")
    finally:
        for _src, dst in temp_files:
            if dst.exists():
                dst.unlink()

    with get_connection("Ecommerce_Baseline", autocommit=True, timeout=0) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT 'Clientes' AS Tabela, COUNT(*) AS Total FROM dbo.Clientes
                UNION ALL SELECT 'Produtos', COUNT(*) FROM dbo.Produtos
                UNION ALL SELECT 'Pedidos', COUNT(*) FROM dbo.Pedidos
                UNION ALL SELECT 'ItensPedido', COUNT(*) FROM dbo.ItensPedido;
                """
            )
            counts = dict(cur.fetchall())

            cur.execute("SELECT name, is_not_trusted FROM sys.foreign_keys ORDER BY name;")
            fks = cur.fetchall()

            cur.execute(
                "SELECT TOP 3 ClienteID, Nome, Cidade, UNICODE(SUBSTRING(Cidade, 4, 1)) "
                "FROM dbo.Clientes ORDER BY ClienteID;"
            )
            sample_clientes = cur.fetchall()

            cur.execute(
                "SELECT TOP 3 ProdutoID, Nome, Categoria, UNICODE(SUBSTRING(Categoria, 2, 1)) "
                "FROM dbo.Produtos ORDER BY ProdutoID;"
            )
            sample_produtos = cur.fetchall()

            cur.execute("EXEC sp_spaceused;")
            space_summary = cur.fetchall()
            space_details = cur.fetchall() if cur.nextset() else []

    expected = {
        "Clientes": 200_000,
        "Produtos": 50_000,
        "Pedidos": 1_500_000,
        "ItensPedido": 4_500_000,
    }
    if counts != expected:
        raise RuntimeError(f"Contagens divergentes! Esperado={expected}, Obtido={counts}")

    # Valida acento exato de 'Goiânia' (4o char = 'â' -> U+00E2 = 226) e 'Móveis' (2o char = 'ó' -> U+00F3 = 243)
    if sample_clientes[0][3] != 226 or sample_produtos[0][3] != 243:
        raise RuntimeError(f"Falha na codificacao de acentos: clientes={sample_clientes}, produtos={sample_produtos}")

    elapsed = time.perf_counter() - t0
    print(f"[OK] Carga massiva concluida em {elapsed:.2f}s")
    print("[OK] Contagens exatas:", counts, f"(Total = {sum(counts.values()):,})")
    print("[OK] FKs (name, is_not_trusted):", fks)
    print("[OK] Amostra Clientes (UTF-16 widechar -> NVARCHAR):", sample_clientes)
    print("[OK] Amostra Produtos (UTF-16 widechar -> NVARCHAR):", sample_produtos)
    print("[OK] sp_spaceused:", space_summary, space_details)


if __name__ == "__main__":
    load_baseline()
