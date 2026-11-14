"""Parte 3.2: Coleta de metricas iniciais e planos XML reais na base Ecommerce_Baseline."""

from __future__ import annotations

import json
import sys
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
from scripts.queries import QUERIES


def collect_baseline() -> None:
    """Coleta planos XML reais (1x) e metricas de IO/TIME (1x Warm) em Ecommerce_Baseline."""
    plans_dir = RESULTS_DIR / "plans" / "baseline"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    plans_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, object] = {}

    with get_connection("Ecommerce_Baseline", autocommit=True, timeout=0) as conn:
        messages = attach_message_collector(conn)

        with conn.cursor() as cur:
            cur.execute("SELECT @@VERSION;")
            version_str = cur.fetchone()[0]
            cur.execute("EXEC sp_spaceused;")
            space_summary = cur.fetchall()
            space_details = cur.fetchall() if cur.nextset() else []

        env_info = {
            "sql_server_version": version_str,
            "ecommerce_baseline_space_summary": [list(r) for r in space_summary],
            "ecommerce_baseline_space_details": [list(r) for r in space_details],
        }
        (RESULTS_DIR / "environment_info.json").write_text(
            json.dumps(env_info, indent=2, ensure_ascii=False),
            encoding="utf-8",
            newline="\n",
        )

        for q in QUERIES:
            # 1) Captura do plano real em XML (etapa separada)
            plan_file = plans_dir / f"{q.code.lower()}_baseline.sqlplan"
            ops = capture_execution_plan_xml(conn, q, q.sql_baseline, plan_file)

            # 2) Aquecimento + medicao unica do baseline com SET STATISTICS IO, TIME ON
            _ = execute_measured_query(conn, messages, q, q.sql_baseline)
            m = execute_measured_query(conn, messages, q, q.sql_baseline)

            summary[q.code] = {
                "title": q.title,
                "category": q.category,
                "operators": ops,
                "metrics": m.to_dict(),
                "plan_file": str(plan_file.relative_to(ROOT_DIR).as_posix()),
            }
            print(
                f"[OK] {q.code:3s} | rows={m.row_count:7d} | logical_reads={m.logical_reads:8d} | "
                f"cpu={m.cpu_time_ms:5d}ms | elapsed={m.elapsed_time_ms:5d}ms | ops={ops[:3]}"
            )

        # Confirma que W1 ROLLBACK manteve ItensPedido exatamente em 4.500.000 linhas
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM dbo.ItensPedido;")
            itens_count = cur.fetchone()[0]
            if itens_count != 4_500_000:
                raise RuntimeError(f"ItensPedido alterada apos W1! Contagem={itens_count}")
            print(f"[OK] Integridade pos-W1 confirmada: ItensPedido = {itens_count:,} linhas.")

    out_json = RESULTS_DIR / "baseline_initial.json"
    out_json.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
        newline="\n",
    )
    print(f"[OK] Resumo baseline salvo em {out_json}")


if __name__ == "__main__":
    collect_baseline()
