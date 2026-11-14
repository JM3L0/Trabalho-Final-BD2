"""Executa bateria automatizada de benchmarks (Warm Cache N=30 e Cold Cache N=10)."""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.db import RESULTS_DIR, get_connection
from scripts.metrics import attach_message_collector, execute_measured_query
from scripts.queries import QUERIES, QuerySpec

EXPECTED_COUNTS: dict[str, int] = {
    "Clientes": 200_000,
    "Produtos": 50_000,
    "Pedidos": 1_500_000,
    "ItensPedido": 4_500_000,
}


def verify_environment_state(conn: Any, db_name: str, expected_sec_indexes: int) -> None:
    """Valida contagem exata de linhas e quantidade de indices secundários."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT COUNT(*)
            FROM sys.indexes AS i
            INNER JOIN sys.tables AS t ON t.object_id = i.object_id
            WHERE t.is_ms_shipped = 0
              AND i.is_primary_key = 0
              AND i.type > 0;
            """
        )
        sec_idx_count = int(cur.fetchone()[0])
        if sec_idx_count != expected_sec_indexes:
            raise RuntimeError(
                f"{db_name}: esperado {expected_sec_indexes} indices secundarios, encontrado {sec_idx_count}."
            )

        for table, expected in EXPECTED_COUNTS.items():
            cur.execute(f"SELECT COUNT_BIG(*) FROM dbo.[{table}];")
            actual = int(cur.fetchone()[0])
            if actual != expected:
                raise RuntimeError(
                    f"{db_name}.dbo.{table}: esperado {expected} linhas, encontrado {actual}."
                )


def clear_caches(conn: Any) -> None:
    """Executa CHECKPOINT e limpa buffer pool e plan cache para medicao Cold Cache."""
    with conn.cursor() as cur:
        cur.execute("CHECKPOINT; DBCC DROPCLEANBUFFERS; DBCC FREEPROCCACHE;")
        while cur.nextset():
            pass


def run_single(
    conn: Any,
    messages: list[str],
    query: QuerySpec,
    sql_text: str,
    scenario: str,
    cache_mode: str,
    run_index: int,
) -> dict[str, Any]:
    """Executa uma medicao unica e devolve dicionario serializavel."""
    t0 = time.perf_counter()
    metrics = execute_measured_query(conn, messages, query, sql_text)
    wall_time_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "cache_mode": cache_mode,
        "query_code": query.code,
        "category": query.category,
        "scenario": scenario,
        "run_index": run_index,
        "logical_reads": metrics.logical_reads,
        "physical_reads": metrics.physical_reads,
        "read_ahead_reads": metrics.read_ahead_reads,
        "cpu_time_ms": metrics.cpu_time_ms,
        "elapsed_time_ms": metrics.elapsed_time_ms,
        "wall_time_ms": round(wall_time_ms, 3),
        "row_count": metrics.row_count,
        "table_io": metrics.table_io,
    }


def run_benchmark_suite(
    warmups: int = 2,
    warm_runs: int = 30,
    cold_runs: int = 10,
) -> tuple[Path, Path]:
    """Executa Warm Cache e Cold Cache para todas as 11 consultas em Baseline vs Otimizado."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    records: list[dict[str, Any]] = []

    with (
        get_connection("Ecommerce_Baseline", autocommit=True, timeout=0) as conn_base,
        get_connection("Ecommerce_Otimizado", autocommit=True, timeout=0) as conn_opt,
    ):
        verify_environment_state(conn_base, "Ecommerce_Baseline", expected_sec_indexes=0)
        verify_environment_state(conn_opt, "Ecommerce_Otimizado", expected_sec_indexes=9)

        with conn_base.cursor() as cur:
            cur.execute("SELECT @@VERSION;")
            sql_version = str(cur.fetchone()[0]).splitlines()[0]

        msg_base = attach_message_collector(conn_base)
        msg_opt = attach_message_collector(conn_opt)

        # Garante buffer pool quente inicial antes da bateria Warm
        for query in QUERIES:
            print(f"[WARM] {query.code}: {warmups} warmups + {warm_runs} repeticoes pareadas...")
            for _ in range(warmups):
                _ = execute_measured_query(conn_base, msg_base, query, query.sql_baseline)
                _ = execute_measured_query(conn_opt, msg_opt, query, query.sql_optimized)

            for rep in range(1, warm_runs + 1):
                if rep % 2 == 1:
                    r_base = run_single(
                        conn_base, msg_base, query, query.sql_baseline, "baseline", "warm", rep
                    )
                    r_opt = run_single(
                        conn_opt, msg_opt, query, query.sql_optimized, "optimized", "warm", rep
                    )
                else:
                    r_opt = run_single(
                        conn_opt, msg_opt, query, query.sql_optimized, "optimized", "warm", rep
                    )
                    r_base = run_single(
                        conn_base, msg_base, query, query.sql_baseline, "baseline", "warm", rep
                    )

                if r_base["row_count"] != r_opt["row_count"]:
                    raise RuntimeError(
                        f"Divergencia de resultado em {query.code} (warm rep {rep}): "
                        f"baseline={r_base['row_count']} vs optimized={r_opt['row_count']}"
                    )
                records.append(r_base)
                records.append(r_opt)

        # Bateria Cold Cache (limpando buffer pool e plan cache antes de cada execucao)
        for query in QUERIES:
            print(f"[COLD] {query.code}: {cold_runs} repeticoes com cache limpo...")
            for rep in range(1, cold_runs + 1):
                if rep % 2 == 1:
                    clear_caches(conn_base)
                    r_base = run_single(
                        conn_base, msg_base, query, query.sql_baseline, "baseline", "cold", rep
                    )
                    clear_caches(conn_opt)
                    r_opt = run_single(
                        conn_opt, msg_opt, query, query.sql_optimized, "optimized", "cold", rep
                    )
                else:
                    clear_caches(conn_opt)
                    r_opt = run_single(
                        conn_opt, msg_opt, query, query.sql_optimized, "optimized", "cold", rep
                    )
                    clear_caches(conn_base)
                    r_base = run_single(
                        conn_base, msg_base, query, query.sql_baseline, "baseline", "cold", rep
                    )

                if r_base["row_count"] != r_opt["row_count"]:
                    raise RuntimeError(
                        f"Divergencia de resultado em {query.code} (cold rep {rep}): "
                        f"baseline={r_base['row_count']} vs optimized={r_opt['row_count']}"
                    )
                records.append(r_base)
                records.append(r_opt)

        # Checkpoint final e validacao estrita de rollback apos W1
        for db_name, conn, expected_idx in (
            ("Ecommerce_Baseline", conn_base, 0),
            ("Ecommerce_Otimizado", conn_opt, 9),
        ):
            with conn.cursor() as cur:
                cur.execute("CHECKPOINT;")
                while cur.nextset():
                    pass
            verify_environment_state(conn, db_name, expected_sec_indexes=expected_idx)

    json_path = RESULTS_DIR / "benchmark_runs.json"
    csv_path = RESULTS_DIR / "benchmark_runs.csv"

    payload = {
        "metadata": {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "sql_version": sql_version,
            "warmups_discarded": warmups,
            "warm_runs": warm_runs,
            "cold_runs": cold_runs,
            "queries": [q.code for q in QUERIES],
            "total_records": len(records),
        },
        "runs": records,
    }
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    fieldnames = [
        "cache_mode",
        "query_code",
        "category",
        "scenario",
        "run_index",
        "logical_reads",
        "physical_reads",
        "read_ahead_reads",
        "cpu_time_ms",
        "elapsed_time_ms",
        "wall_time_ms",
        "row_count",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in records:
            writer.writerow({k: row[k] for k in fieldnames})

    return json_path, csv_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Executa benchmarks Warm e Cold Cache BD2.")
    parser.add_argument("--warmups", type=int, default=2, help="Execucoes de aquecimento descartadas.")
    parser.add_argument("--warm-runs", type=int, default=30, help="Repeticoes validas em Warm Cache.")
    parser.add_argument("--cold-runs", type=int, default=10, help="Repeticoes validas em Cold Cache.")
    args = parser.parse_args()

    t0 = time.perf_counter()
    json_path, csv_path = run_benchmark_suite(
        warmups=args.warmups,
        warm_runs=args.warm_runs,
        cold_runs=args.cold_runs,
    )
    elapsed = time.perf_counter() - t0
    print(f"Benchmarks concluidos em {elapsed:.2f}s.")
    print(f"JSON: {json_path}")
    print(f"CSV:  {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
