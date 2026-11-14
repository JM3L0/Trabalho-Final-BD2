"""Subparte 6.2: Validacao automatizada dos scripts SQL de demonstracao ao vivo."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.db import get_connection
from scripts.metrics import (
    attach_message_collector,
    extract_physical_operators,
    fetch_execution_plan_xml,
    has_key_lookup,
    parse_statistics_messages,
)
from scripts.queries import QUERY_MAP

DEMO_DIR = ROOT_DIR / "scripts" / "demo"
GO_SPLIT_RE = re.compile(r"^\s*GO\s*$", re.IGNORECASE | re.MULTILINE)
EXPECTED_ITEMS_COUNT = 4_500_000


def split_batches(sql_text: str) -> list[str]:
    """Divide um script T-SQL em lotes executaveis pelos separadores GO."""
    return [chunk.strip() for chunk in GO_SPLIT_RE.split(sql_text) if chunk.strip()]


def run_demo_script(filename: str, *, is_write: bool = False) -> dict[str, Any]:
    """Executa todos os lotes GO de um arquivo de demo em sessao unica."""
    path = DEMO_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Script de demo nao encontrado: {path}")

    batches = split_batches(path.read_text(encoding="utf-8"))
    db_metrics: dict[str, dict[str, Any]] = {}
    current_db = "master"

    with get_connection("master", autocommit=True) as conn:
        messages = attach_message_collector(conn)
        with conn.cursor() as cur:
            for batch in batches:
                lines = [ln for ln in batch.splitlines() if ln.strip() and not ln.strip().startswith("--")]
                if not lines:
                    continue
                upper_batch = "\n".join(lines).upper()
                if upper_batch.startswith("USE "):
                    current_db = lines[0].split()[1].rstrip(";")
                    cur.execute(batch)
                    continue

                if "SELECT " in upper_batch or "INSERT " in upper_batch:
                    messages.clear()
                    cur.execute(batch)
                    rows: list[tuple[Any, ...]] = []
                    if cur.description is not None:
                        rows = cur.fetchall()
                    while cur.nextset():
                        if cur.description is not None:
                            rows = cur.fetchall()

                    if is_write and "INSERT " in upper_batch:
                        parsed = parse_statistics_messages(messages, row_count=int(rows[0][0]))
                        db_metrics[current_db] = {
                            "logical_reads": parsed.logical_reads,
                            "elapsed_ms": parsed.elapsed_time_ms,
                            "count_after_rollback": int(rows[0][0]),
                        }
                    elif not is_write:
                        parsed = parse_statistics_messages(messages, row_count=len(rows))
                        db_metrics[current_db] = {
                            "logical_reads": parsed.logical_reads,
                            "elapsed_ms": parsed.elapsed_time_ms,
                            "row_count": len(rows),
                        }
                else:
                    cur.execute(batch)

            cur.execute("SELECT @@TRANCOUNT;")
            trancount = int(cur.fetchone()[0])
            if trancount != 0:
                raise RuntimeError(f"Transacao aberta apos {filename}: @@TRANCOUNT={trancount}")

    return db_metrics


def inspect_actual_operators() -> dict[str, dict[str, dict[str, Any]]]:
    """Captura ShowPlanXML dos 4 cenarios via metrics.fetch_execution_plan_xml."""
    codes = ("Q1", "Q3", "Q4", "W1")
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for code in codes:
        spec = QUERY_MAP[code]
        result[code] = {}
        for db_name, sql in (
            ("Ecommerce_Baseline", spec.sql_baseline),
            ("Ecommerce_Otimizado", spec.sql_optimized),
        ):
            with get_connection(db_name, autocommit=True) as conn:
                xml_plan = fetch_execution_plan_xml(conn, spec, sql)
                result[code][db_name] = {
                    "operators": extract_physical_operators(xml_plan),
                    "has_lookup": has_key_lookup(xml_plan),
                }
    return result


def verify_all() -> None:
    """Executa e valida todos os 4 scripts do kit de demonstracao."""
    r1 = run_demo_script("01_q1_seek_vs_scan.sql")
    assert r1["Ecommerce_Baseline"]["row_count"] == r1["Ecommerce_Otimizado"]["row_count"] == 1
    assert r1["Ecommerce_Otimizado"]["logical_reads"] < r1["Ecommerce_Baseline"]["logical_reads"] / 100

    r2 = run_demo_script("02_q3_indice_composto.sql")
    assert r2["Ecommerce_Baseline"]["row_count"] == r2["Ecommerce_Otimizado"]["row_count"] == 3198
    assert r2["Ecommerce_Otimizado"]["logical_reads"] < r2["Ecommerce_Baseline"]["logical_reads"] / 100

    r3 = run_demo_script("03_q4_eliminacao_key_lookup.sql")
    assert r3["Ecommerce_Baseline"]["row_count"] == r3["Ecommerce_Otimizado"]["row_count"] == 422
    assert r3["Ecommerce_Otimizado"]["logical_reads"] <= 10

    r4 = run_demo_script("04_w1_tradeoff_escrita.sql", is_write=True)
    assert r4["Ecommerce_Baseline"]["count_after_rollback"] == EXPECTED_ITEMS_COUNT
    assert r4["Ecommerce_Otimizado"]["count_after_rollback"] == EXPECTED_ITEMS_COUNT
    assert r4["Ecommerce_Otimizado"]["logical_reads"] > r4["Ecommerce_Baseline"]["logical_reads"]

    plans = inspect_actual_operators()
    assert any(op.startswith("Clustered Index Scan") for op in plans["Q1"]["Ecommerce_Baseline"]["operators"])
    assert any(op.startswith("Index Seek") for op in plans["Q1"]["Ecommerce_Otimizado"]["operators"])
    assert plans["Q1"]["Ecommerce_Otimizado"]["has_lookup"] is True

    assert any("Index Seek (Pedidos.IX_Pedidos_Status_Data)" in op for op in plans["Q3"]["Ecommerce_Otimizado"]["operators"])
    assert plans["Q3"]["Ecommerce_Otimizado"]["has_lookup"] is False

    assert plans["Q4"]["Ecommerce_Otimizado"]["operators"] == ["Index Seek (Pedidos.IX_Pedidos_ClienteID_Cov)"]
    assert plans["Q4"]["Ecommerce_Otimizado"]["has_lookup"] is False

    assert any(op.startswith("Sequence") for op in plans["W1"]["Ecommerce_Otimizado"]["operators"])

    print("[OK] Kit da demonstracao ao vivo validado com sucesso:")
    print(f"  01_q1: Baseline={r1['Ecommerce_Baseline']} | Optimized={r1['Ecommerce_Otimizado']}")
    print(f"  02_q3: Baseline={r2['Ecommerce_Baseline']} | Optimized={r2['Ecommerce_Otimizado']}")
    print(f"  03_q4: Baseline={r3['Ecommerce_Baseline']} | Optimized={r3['Ecommerce_Otimizado']}")
    print(f"  04_w1: Baseline={r4['Ecommerce_Baseline']} | Optimized={r4['Ecommerce_Otimizado']}")
    for code, per_db in plans.items():
        print(f"  Plan {code}: Base={per_db['Ecommerce_Baseline']} | Opt={per_db['Ecommerce_Otimizado']}")


if __name__ == "__main__":
    verify_all()
