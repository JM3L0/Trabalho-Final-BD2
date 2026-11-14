"""Parte 4.1: Aplica indices em Ecommerce_Otimizado, captura Q4 intermediario e valida planos reais."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.db import RESULTS_DIR, get_connection
from scripts.metrics import (
    attach_message_collector,
    capture_execution_plan_xml,
    execute_measured_query,
)
from scripts.queries import QUERIES, QUERY_MAP

SQL_FILE = ROOT_DIR / "scripts" / "sql" / "04_create_indexes_optimized.sql"


def _split_batches(sql_text: str) -> list[str]:
    batches = re.split(r"^\s*GO\s*$", sql_text, flags=re.IGNORECASE | re.MULTILINE)
    return [batch.strip() for batch in batches if batch.strip()]


def apply_and_validate() -> None:
    """Captura Q4 com Key Lookup (indice simples), aplica indices finais e valida planos Q1-Q10/W1."""
    t0 = time.perf_counter()
    plans_opt_dir = RESULTS_DIR / "plans" / "optimized"
    plans_opt_dir.mkdir(parents=True, exist_ok=True)

    # Garante que Ecommerce_Baseline nao tem indices secundarios
    with get_connection("Ecommerce_Baseline", autocommit=True) as conn_base:
        with conn_base.cursor() as cur:
            cur.execute(
                "SELECT COUNT(*) FROM sys.indexes "
                "WHERE object_id IN (SELECT object_id FROM sys.tables) AND type > 0 AND is_primary_key = 0;"
            )
            sec_base = cur.fetchone()[0]
            if sec_base != 0:
                raise RuntimeError(f"Ecommerce_Baseline foi alterada! Indices secundarios={sec_base}")

    # Etapa intermediaria Q4: indice simples em Pedidos(ClienteID) para demonstrar Seek + Key Lookup
    with get_connection("Ecommerce_Otimizado", autocommit=True, timeout=0) as conn:
        messages = attach_message_collector(conn)
        with conn.cursor() as cur:
            cur.execute("DROP INDEX IF EXISTS IX_Pedidos_ClienteID_Cov ON dbo.Pedidos;")
            cur.execute("DROP INDEX IF EXISTS IX_Pedidos_ClienteID ON dbo.Pedidos;")
            cur.execute("CREATE NONCLUSTERED INDEX IX_Pedidos_ClienteID ON dbo.Pedidos (ClienteID);")
            cur.execute("UPDATE STATISTICS dbo.Pedidos IX_Pedidos_ClienteID;")

        q4 = QUERY_MAP["Q4"]
        assert q4.sql_intermediate is not None
        q4_inter_plan = plans_opt_dir / "q4_intermediate_lookup.sqlplan"
        ops_inter = capture_execution_plan_xml(conn, q4, q4.sql_intermediate, q4_inter_plan)
        _ = execute_measured_query(conn, messages, q4, q4.sql_intermediate)
        m_inter = execute_measured_query(conn, messages, q4, q4.sql_intermediate)
        (RESULTS_DIR / "q4_intermediate.json").write_text(
            json.dumps(
                {
                    "code": "Q4_INTERMEDIATE",
                    "operators": ops_inter,
                    "metrics": m_inter.to_dict(),
                    "plan_file": str(q4_inter_plan.relative_to(ROOT_DIR).as_posix()),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
            newline="\n",
        )
        print(
            f"[OK] Q4_INTERMEDIATE | rows={m_inter.row_count} | logical_reads={m_inter.logical_reads} | "
            f"elapsed={m_inter.elapsed_time_ms}ms | ops={ops_inter}"
        )

        # Aplica o script completo de indices finais em Ecommerce_Otimizado
        batches = _split_batches(SQL_FILE.read_text(encoding="utf-8"))
        with conn.cursor() as cur:
            for batch in batches:
                cur.execute(batch)
                while cur.nextset():
                    pass

            cur.execute(
                """
                SELECT OBJECT_NAME(i.object_id) AS tabela, i.name, i.type_desc, i.has_filter
                FROM sys.indexes i
                JOIN sys.tables t ON i.object_id = t.object_id
                WHERE i.is_primary_key = 0 AND i.type > 0
                ORDER BY tabela, i.name;
                """
            )
            created_indexes = cur.fetchall()
            print(f"[OK] Indices secundarios em Ecommerce_Otimizado ({len(created_indexes)}):")
            for row in created_indexes:
                print("  -", row)

        # Valida 1x todos os planos XML e metricas finais de Ecommerce_Otimizado
        summary_opt: dict[str, object] = {}
        for q in QUERIES:
            plan_file = plans_opt_dir / f"{q.code.lower()}_optimized.sqlplan"
            ops = capture_execution_plan_xml(conn, q, q.sql_optimized, plan_file)
            _ = execute_measured_query(conn, messages, q, q.sql_optimized)
            m = execute_measured_query(conn, messages, q, q.sql_optimized)

            summary_opt[q.code] = {
                "title": q.title,
                "category": q.category,
                "operators": ops,
                "metrics": m.to_dict(),
                "plan_file": str(plan_file.relative_to(ROOT_DIR).as_posix()),
            }
            print(
                f"[OK] {q.code:3s} | rows={m.row_count:7d} | logical_reads={m.logical_reads:8d} | "
                f"cpu={m.cpu_time_ms:5d}ms | elapsed={m.elapsed_time_ms:5d}ms | ops={ops[:4]}"
            )

        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM dbo.ItensPedido;")
            itens_count = cur.fetchone()[0]
            if itens_count != 4_500_000:
                raise RuntimeError(f"ItensPedido alterada apos W1! Contagem={itens_count}")

    (RESULTS_DIR / "optimized_initial.json").write_text(
        json.dumps(summary_opt, indent=2, ensure_ascii=False),
        encoding="utf-8",
        newline="\n",
    )
    print(f"[OK] Parte 4.1 concluida em {time.perf_counter() - t0:.2f}s")


if __name__ == "__main__":
    apply_and_validate()
