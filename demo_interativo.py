"""Menu interativo para demonstracao pratica ao vivo (e contingencia Plano B) da apresentacao."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.db import RESULTS_DIR, get_connection, load_db_config
from scripts.metrics import (
    SHOWPLAN_NS,
    RunMetrics,
    attach_message_collector,
    execute_measured_query,
    fetch_execution_plan_xml,
    has_key_lookup,
)
from scripts.queries import QUERIES, QUERY_MAP, QuerySpec
from scripts.run_benchmarks import EXPECTED_COUNTS, clear_caches, verify_environment_state

DEMO_DIR = ROOT_DIR / "scripts" / "demo"
PLANS_DIR = RESULTS_DIR / "plans"
SUMMARY_STATS_PATH = RESULTS_DIR / "summary_stats.json"
Q4_INTERMEDIATE_JSON = RESULTS_DIR / "q4_intermediate.json"

OFFICIAL_DEMO_ORDER: tuple[str, ...] = ("Q1", "Q3", "Q4", "W1")
DEMO_SQL_FILES: dict[str, str] = {
    "Q1": "01_q1_seek_vs_scan.sql",
    "Q3": "02_q3_indice_composto.sql",
    "Q4": "03_q4_eliminacao_key_lookup.sql",
    "W1": "04_w1_tradeoff_escrita.sql",
}
EXTRA_QUERY_ORDER: tuple[str, ...] = ("Q2", "Q5", "Q6", "Q7", "Q8", "Q9", "Q10")

MENU_SHORTCUTS: dict[str, str] = {
    "1": "Q1",
    "2": "Q3",
    "3": "Q4",
    "4": "W1",
    "5": "Q2",
    "6": "Q5",
    "7": "Q6",
    "8": "Q7",
    "9": "Q8",
    "10": "Q9",
    "11": "Q10",
}

DEMO_HIGHLIGHTS: dict[str, str] = {
    "Q1": "Custo O(N) vs. O(log N): Clustered Index Scan (2.856 pag.) -> Index Seek + 1 Key Lookup (6 pag.).",
    "Q3": "Indice composto (Status, DataPedido): igualdade a esquerda e faixa a direita (8.090 -> 17 pag.).",
    "Q4": "Eliminacao de 422 Key Lookups com Covering Index INCLUDE (8.090 -> 1.296 -> 5 pag.).",
    "W1": "Trade-off de escrita: operador Sequence mantem 4 B+ Trees (+85,33% E/S); seguro via ROLLBACK.",
    "Q2": "Range Seek em DataPedido coberto por (PedidoID, DataPedido) sem Key Lookup.",
    "Q5": "Juncao de 3 tabelas: dois Hash Match substituidos por Merge Join + Nested Loops.",
    "Q6": "Paginacao TOP 50 ORDER BY DESC: leitura Backward ordenada sem operador Sort.",
    "Q7": "Trade-off de CPU: Batch Mode (Hash Match) vs. Row Mode (Stream Aggregate) sob MAXDOP 1.",
    "Q8": "Sargabilidade textual: LIKE '%Notebook%' (Scan) vs. LIKE 'Notebook%' (Index Seek).",
    "Q9": "Sargabilidade temporal: YEAR(DataPedido) = 2025 vs. intervalo semiaberto.",
    "Q10": "Otimizacao logica: subconsulta agregada correlacionada vs. NOT EXISTS (Anti Semi Join).",
}


class Ansi:
    """Codigos ANSI com suporte a Windows Terminal/PowerShell e modo sem cor."""

    enabled: bool = True

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"

    @classmethod
    def configure(cls, *, use_color: bool) -> None:
        if not use_color or not sys.stdout.isatty():
            cls.enabled = False
            return
        if os.name == "nt":
            try:
                kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
                handle = kernel32.GetStdHandle(-11)
                mode = ctypes.c_ulong()
                if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                    kernel32.SetConsoleMode(handle, mode.value | 0x0004)
            except Exception:
                pass
        cls.enabled = True

    @classmethod
    def style(cls, text: str, *codes: str) -> str:
        if not cls.enabled or not codes:
            return text
        return f"{''.join(codes)}{text}{cls.RESET}"


@dataclass(frozen=True)
class PlanNode:
    """No hierarquico extraido de um ShowPlanXML."""

    depth: int
    physical_op: str
    logical_op: str
    object_name: str
    execution_mode: str
    actual_rows: int | None
    estimate_rows: float | None
    subtree_cost: float | None
    is_lookup: bool


@dataclass(frozen=True)
class PlanAnalysis:
    """Resumo estruturado de um plano de execucao real."""

    total_cost: float | None
    primary_mode: str
    has_lookup: bool
    nodes: list[PlanNode]


@dataclass
class DemoConfig:
    """Estado de execucao da sessao interativa."""

    offline_mode: bool = False
    cache_mode: str = "warm"  # "warm" | "cold"
    sql_version: str = ""


def fmt_int(value: int | float) -> str:
    """Formata inteiro no padrao brasileiro (separador de milhar '.')."""
    return f"{int(round(value)):,}".replace(",", ".")


def fmt_float(value: float, decimals: int = 1) -> str:
    """Formata decimal com separador ','."""
    return f"{value:.{decimals}f}".replace(".", ",")


def _find_direct_object(relop: ET.Element) -> tuple[str, bool]:
    """Localiza objeto/indice proprio do RelOp e indica se o operador e Lookup."""
    relop_tag = f"{{{SHOWPLAN_NS['sp']}}}RelOp"
    obj_tag = f"{{{SHOWPLAN_NS['sp']}}}Object"
    idx_scan_tag = f"{{{SHOWPLAN_NS['sp']}}}IndexScan"
    is_lookup = False
    found_name = ""

    def _walk(elem: ET.Element) -> None:
        nonlocal is_lookup, found_name
        for child in elem:
            if child.tag == relop_tag:
                continue
            if child.tag == idx_scan_tag and child.attrib.get("Lookup") == "1":
                is_lookup = True
            if child.tag == obj_tag and not found_name:
                tbl = child.attrib.get("Table", "").strip("[]")
                idx = child.attrib.get("Index", "").strip("[]")
                found_name = f"{tbl}.{idx}" if (tbl and idx) else tbl
            _walk(child)

    _walk(relop)
    return found_name, is_lookup


def analyze_showplan_xml(xml_text: str) -> PlanAnalysis:
    """Extrai arvore completa de operadores fisicos, custo e modo de execucao."""
    if "<ShowPlanXML" not in xml_text:
        raise RuntimeError("Conteudo XML invalido: tag ShowPlanXML ausente.")
    root = ET.fromstring(xml_text)
    relop_tag = f"{{{SHOWPLAN_NS['sp']}}}RelOp"

    first_relop = root.find(f".//{relop_tag}")
    total_cost: float | None = None
    primary_mode = "?"
    if first_relop is not None:
        raw_cost = first_relop.attrib.get("EstimatedTotalSubtreeCost")
        total_cost = float(raw_cost) if raw_cost is not None else None

    nodes: list[PlanNode] = []

    def _visit(elem: ET.Element, depth: int) -> None:
        nonlocal primary_mode
        for child in elem:
            if child.tag == relop_tag:
                phys = child.attrib.get("PhysicalOp", "?")
                log = child.attrib.get("LogicalOp", "")
                obj_name, is_lookup = _find_direct_object(child)
                rts = child.findall("./sp:RunTimeInformation/sp:RunTimeCountersPerThread", SHOWPLAN_NS)
                mode = (
                    rts[0].attrib.get("ActualExecutionMode", "")
                    if rts
                    else ""
                ) or child.attrib.get("EstimatedExecutionMode", "?")
                actual_rows = sum(int(rt.attrib.get("ActualRows", 0)) for rt in rts) if rts else None
                est_raw = child.attrib.get("EstimateRows")
                est_rows = float(est_raw) if est_raw is not None else None
                cost_raw = child.attrib.get("EstimatedTotalSubtreeCost")
                sub_cost = float(cost_raw) if cost_raw is not None else None

                if primary_mode == "?" and mode != "?":
                    primary_mode = mode
                if mode == "Batch":
                    primary_mode = "Batch"

                nodes.append(
                    PlanNode(
                        depth=depth,
                        physical_op=phys,
                        logical_op=log,
                        object_name=obj_name,
                        execution_mode=mode,
                        actual_rows=actual_rows,
                        estimate_rows=est_rows,
                        subtree_cost=sub_cost,
                        is_lookup=is_lookup,
                    )
                )
                _visit(child, depth + 1)
            else:
                _visit(child, depth)

    stmt = root.find(".//sp:QueryPlan", SHOWPLAN_NS)
    _visit(stmt if stmt is not None else root, 0)

    return PlanAnalysis(
        total_cost=total_cost,
        primary_mode=primary_mode,
        has_lookup=has_key_lookup(xml_text),
        nodes=nodes,
    )


def render_plan_tree(label: str, analysis: PlanAnalysis, *, accent: str) -> None:
    """Imprime arvore de operadores de forma visualmente limpa no terminal."""
    cost_str = fmt_float(analysis.total_cost, 4) if analysis.total_cost is not None else "?"
    lookup_badge = (
        Ansi.style("SIM (Key Lookup presente)", Ansi.YELLOW, Ansi.BOLD)
        if analysis.has_lookup
        else Ansi.style("NAO (0 lookups)", Ansi.GREEN)
    )
    mode_badge = (
        Ansi.style("Batch", Ansi.MAGENTA, Ansi.BOLD)
        if analysis.primary_mode == "Batch"
        else Ansi.style(analysis.primary_mode, Ansi.CYAN)
    )
    print(
        f"  {Ansi.style(label, accent, Ansi.BOLD)} "
        f"| Custo est.: {cost_str} | Modo: {mode_badge} | Lookup: {lookup_badge}"
    )
    for node in analysis.nodes:
        indent = "    " + ("│   " * max(node.depth - 1, 0)) + ("├─ " if node.depth > 0 else "")
        op_title = node.physical_op
        if node.is_lookup:
            op_title = f"Key Lookup [{node.physical_op}]"
        elif node.logical_op and node.logical_op != node.physical_op:
            op_title = f"{node.physical_op} [{node.logical_op}]"
        obj = f" ({node.object_name})" if node.object_name else ""
        rows_info = (
            f" | linhas={fmt_int(node.actual_rows)}"
            if node.actual_rows is not None
            else (f" | est={fmt_int(node.estimate_rows)}" if node.estimate_rows is not None else "")
        )
        mode_info = f" | {node.execution_mode}" if node.execution_mode and node.execution_mode != "?" else ""
        print(f"    {indent}{Ansi.style(op_title + obj, Ansi.BOLD)}{Ansi.style(rows_info + mode_info, Ansi.DIM)}")


def print_sql_block(spec: QuerySpec) -> None:
    """Exibe o SQL executado (e indica se houve reescrita sargable/logica)."""
    print(Ansi.style("SQL Executado:", Ansi.BOLD))
    if spec.sql_baseline == spec.sql_optimized:
        print(f"  {Ansi.style('(Mesma consulta nas duas bases — diferenca apenas nos indices)', Ansi.DIM)}")
        print(f"  {Ansi.style(spec.sql_baseline, Ansi.CYAN)}")
    else:
        print(f"  {Ansi.style('[Baseline ]', Ansi.YELLOW)} {spec.sql_baseline}")
        print(f"  {Ansi.style('[Otimizado]', Ansi.GREEN)} {spec.sql_optimized}")


def compute_io_and_speedup(
    base_reads: float,
    opt_reads: float,
    base_ms: float,
    opt_ms: float,
    *,
    is_write: bool,
) -> tuple[str, str]:
    """Calcula reducao/aumento de E/S e fator de aceleracao (Speedup)."""
    if base_reads > 0:
        diff_pct = ((base_reads - opt_reads) / base_reads) * 100.0
        if is_write or diff_pct < 0:
            io_str = Ansi.style(f"+{fmt_float(abs(diff_pct), 2)}% (overhead escrita)", Ansi.RED, Ansi.BOLD)
        else:
            io_str = Ansi.style(f"-{fmt_float(diff_pct, 2)}% de leituras", Ansi.GREEN, Ansi.BOLD)
    else:
        io_str = "N/A"

    if opt_ms <= 0.0:
        if base_ms <= 0.0:
            spd_str = Ansi.style("~1,0x (<1 ms)", Ansi.CYAN)
        else:
            spd_str = Ansi.style(f">{fmt_float(base_ms, 1)}x (<1 ms)", Ansi.GREEN, Ansi.BOLD)
    else:
        ratio = base_ms / opt_ms
        color = Ansi.GREEN if ratio >= 1.0 else Ansi.YELLOW
        spd_str = Ansi.style(f"{fmt_float(ratio, 2)}x", color, Ansi.BOLD)
    return io_str, spd_str


def print_metrics_comparison(
    spec: QuerySpec,
    base_label: str,
    opt_label: str,
    base_reads: float,
    opt_reads: float,
    base_phys: float,
    opt_phys: float,
    base_cpu: float,
    opt_cpu: float,
    base_ms: float,
    opt_ms: float,
    row_count: int,
    base_table_io: dict[str, int] | None = None,
    opt_table_io: dict[str, int] | None = None,
) -> None:
    """Imprime tabela comparativa formatada entre Baseline e Otimizado."""
    io_summary, speedup_summary = compute_io_and_speedup(
        base_reads,
        opt_reads,
        base_ms,
        opt_ms,
        is_write=spec.is_dml_write,
    )
    print()
    print(Ansi.style("Comparativo de Desempenho:", Ansi.BOLD))
    print(f"  {'Metrica':<28} | {base_label:>18} | {opt_label:>18}")
    print(f"  {'-' * 28}-+-{'-' * 18}-+-{'-' * 18}")
    print(f"  {'Leituras logicas (pag 8KB)':<28} | {fmt_int(base_reads):>18} | {fmt_int(opt_reads):>18}")
    print(f"  {'Leituras fisicas (pag 8KB)':<28} | {fmt_int(base_phys):>18} | {fmt_int(opt_phys):>18}")
    print(f"  {'Tempo de CPU (ms)':<28} | {fmt_float(base_cpu, 1):>18} | {fmt_float(opt_cpu, 1):>18}")
    opt_time_txt = "< 1 (0)" if opt_ms <= 0.0 else fmt_float(opt_ms, 1)
    print(f"  {'Tempo decorrido (ms)':<28} | {fmt_float(base_ms, 1):>18} | {opt_time_txt:>18}")
    print(f"  {'Linhas retornadas/afetadas':<28} | {fmt_int(row_count):>18} | {fmt_int(row_count):>18}")

    if base_table_io or opt_table_io:
        tables = sorted(set((base_table_io or {}).keys()) | set((opt_table_io or {}).keys()))
        if tables:
            print(f"  {'-' * 28}-+-{'-' * 18}-+-{'-' * 18}")
            for tbl in tables:
                b_val = fmt_int((base_table_io or {}).get(tbl, 0))
                o_val = fmt_int((opt_table_io or {}).get(tbl, 0))
                print(f"  {'  I/O tabela ' + tbl:<28} | {b_val:>18} | {o_val:>18}")

    print()
    print(f"  Resultado E/S : {io_summary}")
    print(f"  Speedup       : {speedup_summary}")


def show_q4_intermediate_stage() -> None:
    """Exibe o estagio intermediario de Q4 (Index Seek + 422 Key Lookups) como ponte didatica."""
    inter_plan = PLANS_DIR / "optimized" / "q4_intermediate_lookup.sqlplan"
    if not Q4_INTERMEDIATE_JSON.exists() and not inter_plan.exists():
        return
    print()
    print(Ansi.style("Progressao Completa em 3 Estagios de Q4 (Referencia Capturada):", Ansi.CYAN, Ansi.BOLD))
    if Q4_INTERMEDIATE_JSON.exists():
        data = json.loads(Q4_INTERMEDIATE_JSON.read_text(encoding="utf-8"))
        m = data.get("metrics", {})
        print(
            "  Estagio 2 (Indice simples em ClienteID, sem INCLUDE): "
            f"{fmt_int(m.get('logical_reads', 1296))} leituras logicas | "
            f"{m.get('elapsed_time_ms', 1)} ms | "
            "422 Key Lookups em PK_Pedidos"
        )
    if inter_plan.exists():
        analysis = analyze_showplan_xml(inter_plan.read_text(encoding="utf-8"))
        render_plan_tree("Estagio 2 [Q4_INTERMEDIATE]", analysis, accent=Ansi.CYAN)


def check_live_environment() -> tuple[bool, str, list[str]]:
    """Valida conexao, versao, contagem de 6,25M tuplas e 0 vs 9 indices secundarios."""
    lines: list[str] = []
    cfg = load_db_config()
    try:
        with (
            get_connection("Ecommerce_Baseline", autocommit=True, timeout=5) as conn_base,
            get_connection("Ecommerce_Otimizado", autocommit=True, timeout=5) as conn_opt,
        ):
            with conn_base.cursor() as cur:
                cur.execute("SELECT @@VERSION;")
                version = str(cur.fetchone()[0]).splitlines()[0].strip()

            verify_environment_state(conn_base, "Ecommerce_Baseline", expected_sec_indexes=0)
            verify_environment_state(conn_opt, "Ecommerce_Otimizado", expected_sec_indexes=9)

            lines.append(f"Servidor: {cfg.host}:{cfg.port} | {version}")
            lines.append("Ecommerce_Baseline : 0 indices secundarios | 6.250.000 linhas intactas")
            lines.append("Ecommerce_Otimizado: 9 indices secundarios | 6.250.000 linhas intactas")
            for tbl, expected in EXPECTED_COUNTS.items():
                lines.append(f"  - dbo.{tbl:<12}: {fmt_int(expected)} registros em ambas as bases")
            return True, version, lines
    except Exception as exc:
        lines.append(f"Falha ao conectar em {cfg.host}:{cfg.port} -> {exc}")
        return False, "", lines


def run_live_scenario(spec: QuerySpec, cache_mode: str) -> None:
    """Executa consulta ao vivo nas duas bases gemeas e exibe metricas + planos reais."""
    print()
    print(Ansi.style("=" * 78, Ansi.BLUE))
    demo_tag = f" | Script: scripts/demo/{DEMO_SQL_FILES[spec.code]}" if spec.code in DEMO_SQL_FILES else ""
    print(Ansi.style(f"[{spec.code}] {spec.title}", Ansi.BOLD, Ansi.CYAN) + Ansi.style(demo_tag, Ansi.DIM))
    print(f"Categoria: {spec.category} | Cache: {cache_mode.upper()} | MAXDOP 1")
    if spec.code in DEMO_HIGHLIGHTS:
        print(f"Foco     : {DEMO_HIGHLIGHTS[spec.code]}")
    print(Ansi.style("-" * 78, Ansi.BLUE))
    print_sql_block(spec)

    with (
        get_connection("Ecommerce_Baseline", autocommit=True, timeout=60) as conn_base,
        get_connection("Ecommerce_Otimizado", autocommit=True, timeout=60) as conn_opt,
    ):
        msg_base = attach_message_collector(conn_base)
        msg_opt = attach_message_collector(conn_opt)

        if cache_mode == "cold":
            print(Ansi.style("\nLimpando buffer pool e cache de planos (Cold Cache)...", Ansi.YELLOW))
            clear_caches(conn_base)
            clear_caches(conn_opt)
        elif not spec.is_dml_write:
            # 1x aquecimento rapido para assegurar buffer pool quente em leitura ao vivo
            execute_measured_query(conn_base, msg_base, spec, spec.sql_baseline)
            execute_measured_query(conn_opt, msg_opt, spec, spec.sql_optimized)

        m_base: RunMetrics = execute_measured_query(conn_base, msg_base, spec, spec.sql_baseline)
        m_opt: RunMetrics = execute_measured_query(conn_opt, msg_opt, spec, spec.sql_optimized)

        xml_base = fetch_execution_plan_xml(conn_base, spec, spec.sql_baseline)
        xml_opt = fetch_execution_plan_xml(conn_opt, spec, spec.sql_optimized)

        print_metrics_comparison(
            spec,
            "Baseline (ao vivo)",
            "Otimizado (ao vivo)",
            m_base.logical_reads,
            m_opt.logical_reads,
            m_base.physical_reads,
            m_opt.physical_reads,
            m_base.cpu_time_ms,
            m_opt.cpu_time_ms,
            m_base.elapsed_time_ms,
            m_opt.elapsed_time_ms,
            m_opt.row_count,
            m_base.table_io,
            m_opt.table_io,
        )

        print()
        print(Ansi.style("Planos de Execucao Reais Capturados Agora (ShowPlanXML):", Ansi.BOLD))
        render_plan_tree("Ecommerce_Baseline ", analyze_showplan_xml(xml_base), accent=Ansi.YELLOW)
        print()
        render_plan_tree("Ecommerce_Otimizado", analyze_showplan_xml(xml_opt), accent=Ansi.GREEN)

        if spec.code == "Q4":
            show_q4_intermediate_stage()

        if spec.is_dml_write:
            with conn_base.cursor() as cur_b, conn_opt.cursor() as cur_o:
                cur_b.execute("SELECT COUNT_BIG(*), @@TRANCOUNT FROM dbo.ItensPedido;")
                cnt_b, tran_b = cur_b.fetchone()
                cur_o.execute("SELECT COUNT_BIG(*), @@TRANCOUNT FROM dbo.ItensPedido;")
                cnt_o, tran_o = cur_o.fetchone()
            print()
            print(
                Ansi.style(
                    f"[SEGURO] Pos-ROLLBACK: Baseline={fmt_int(cnt_b)} linhas (@@TRANCOUNT={tran_b}) | "
                    f"Otimizado={fmt_int(cnt_o)} linhas (@@TRANCOUNT={tran_o})",
                    Ansi.GREEN,
                    Ansi.BOLD,
                )
            )


def run_offline_scenario(spec: QuerySpec, cache_mode: str) -> None:
    """Plano B: exibe estatisticas reais (summary_stats.json) e planos .sqlplan pre-capturados."""
    print()
    print(Ansi.style("=" * 78, Ansi.MAGENTA))
    print(
        Ansi.style(f"[{spec.code}] {spec.title}", Ansi.BOLD, Ansi.CYAN)
        + Ansi.style(" [PLANO B OFFLINE]", Ansi.MAGENTA, Ansi.BOLD)
    )
    print(f"Categoria: {spec.category} | Cache: {cache_mode.upper()} (dados do experimento)")
    if spec.code in DEMO_HIGHLIGHTS:
        print(f"Foco     : {DEMO_HIGHLIGHTS[spec.code]}")
    print(Ansi.style("-" * 78, Ansi.MAGENTA))
    print_sql_block(spec)

    if SUMMARY_STATS_PATH.exists():
        stats = json.loads(SUMMARY_STATS_PATH.read_text(encoding="utf-8"))
        entry = stats["cache_modes"][cache_mode][spec.code]
        b = entry["baseline"]
        o = entry["optimized"]
        print_metrics_comparison(
            spec,
            f"Baseline ({cache_mode})",
            f"Otimizado ({cache_mode})",
            b["logical_reads"]["median"],
            o["logical_reads"]["median"],
            b["physical_reads"]["median"],
            o["physical_reads"]["median"],
            b["cpu_time_ms"]["median"],
            o["cpu_time_ms"]["median"],
            b["elapsed_time_ms"]["median"],
            o["elapsed_time_ms"]["median"],
            int(entry["row_count"]),
        )
    else:
        print(Ansi.style("Aviso: results/summary_stats.json nao encontrado.", Ansi.YELLOW))

    code_lower = spec.code.lower()
    base_plan = PLANS_DIR / "baseline" / f"{code_lower}_baseline.sqlplan"
    opt_plan = PLANS_DIR / "optimized" / f"{code_lower}_optimized.sqlplan"

    print()
    print(Ansi.style("Planos de Execucao Pre-Capturados (.sqlplan):", Ansi.BOLD))
    if base_plan.exists():
        render_plan_tree(
            f"Baseline  ({base_plan.name})",
            analyze_showplan_xml(base_plan.read_text(encoding="utf-8")),
            accent=Ansi.YELLOW,
        )
    if opt_plan.exists():
        print()
        render_plan_tree(
            f"Otimizado ({opt_plan.name})",
            analyze_showplan_xml(opt_plan.read_text(encoding="utf-8")),
            accent=Ansi.GREEN,
        )
    if spec.code == "Q4":
        show_q4_intermediate_stage()


def execute_scenario(spec: QuerySpec, config: DemoConfig) -> None:
    """Executa no modo atual; se falhar conexao ao vivo, oferece fallback imediato para Plano B."""
    if config.offline_mode:
        run_offline_scenario(spec, config.cache_mode)
        return
    try:
        run_live_scenario(spec, config.cache_mode)
    except Exception as exc:
        print()
        print(Ansi.style(f"[ERRO AO VIVO] Nao foi possivel executar no SQL Server: {exc}", Ansi.RED, Ansi.BOLD))
        choice = input("Ativar Modo Contingencia Offline (Plano B) agora para esta consulta? [S/n]: ").strip().lower()
        if choice in {"", "s", "sim", "y", "yes"}:
            config.offline_mode = True
            run_offline_scenario(spec, config.cache_mode)


def open_sqlplan_in_vscode() -> None:
    """Abre arquivos .sqlplan pre-capturados no VS Code (ou exibe os caminhos)."""
    print()
    print(Ansi.style("Planos .sqlplan disponiveis (Plano B grafico):", Ansi.BOLD))
    for idx, code in enumerate(OFFICIAL_DEMO_ORDER, start=1):
        print(f"  [{idx}] {code} ({DEMO_SQL_FILES[code]})")
    print("  [5] Escolher outro codigo (Q2, Q5..Q10)")
    sel = input("Qual cenario abrir? [1-5 ou Enter p/ voltar]: ").strip().upper()
    if not sel:
        return
    if sel in {"1", "2", "3", "4"}:
        code = OFFICIAL_DEMO_ORDER[int(sel) - 1]
    elif sel == "5":
        code = input("Digite o codigo (ex.: Q7): ").strip().upper()
    else:
        code = sel

    if code not in QUERY_MAP:
        print(Ansi.style(f"Codigo desconhecido: {code}", Ansi.RED))
        return

    c_low = code.lower()
    files = [
        PLANS_DIR / "baseline" / f"{c_low}_baseline.sqlplan",
        PLANS_DIR / "optimized" / f"{c_low}_optimized.sqlplan",
    ]
    if code == "Q4":
        files.insert(1, PLANS_DIR / "optimized" / "q4_intermediate_lookup.sqlplan")

    existing = [p for p in files if p.exists()]
    for p in existing:
        print(f"  -> {p.relative_to(ROOT_DIR)}")

    code_bin = shutil.which("code")
    if code_bin and existing:
        subprocess.run([code_bin, *[str(p) for p in existing]], check=False)
        print(Ansi.style("Arquivos enviados para abertura no VS Code.", Ansi.GREEN))
    elif not code_bin:
        print(Ansi.style("CLI 'code' nao encontrada no PATH; abra os caminhos acima manualmente.", Ansi.YELLOW))


def run_guided_official_sequence(config: DemoConfig) -> None:
    """Roda os 4 cenarios do roteiro oficial em sequencia, pausando entre cada um."""
    for pos, code in enumerate(OFFICIAL_DEMO_ORDER, start=1):
        spec = QUERY_MAP[code]
        execute_scenario(spec, config)
        if pos < len(OFFICIAL_DEMO_ORDER):
            print()
            resp = input(
                Ansi.style(
                    f"[{pos}/4 concluido] Pressione Enter para o proximo ({OFFICIAL_DEMO_ORDER[pos]}) ou 'q' p/ menu: ",
                    Ansi.CYAN,
                    Ansi.BOLD,
                )
            ).strip().lower()
            if resp == "q":
                break


def print_menu(config: DemoConfig) -> None:
    """Exibe o menu interativo compacto e claro para uso em apresentacao."""
    mode_txt = (
        Ansi.style("PLANO B OFFLINE (.sqlplan + stats)", Ansi.MAGENTA, Ansi.BOLD)
        if config.offline_mode
        else Ansi.style("AO VIVO (SQL Server 2022 Docker)", Ansi.GREEN, Ansi.BOLD)
    )
    cache_txt = (
        Ansi.style("WARM CACHE", Ansi.CYAN, Ansi.BOLD)
        if config.cache_mode == "warm"
        else Ansi.style("COLD CACHE", Ansi.YELLOW, Ansi.BOLD)
    )

    print()
    print(Ansi.style("==============================================================================", Ansi.BLUE))
    print(Ansi.style("  DEMO INTERATIVA — TRABALHO FINAL BD II (SQL SERVER 2022 | 6,25M LINHAS)", Ansi.BOLD))
    print(f"  Modo: {mode_txt}  |  Cache: {cache_txt}")
    if config.sql_version:
        print(f"  Motor: {Ansi.style(config.sql_version, Ansi.DIM)}")
    print(Ansi.style("==============================================================================", Ansi.BLUE))
    print(Ansi.style(" ROTEIRO PRINCIPAL DA APRESENTACAO (4 CENARIOS-CHAVE):", Ansi.BOLD))
    for i, code in enumerate(OFFICIAL_DEMO_ORDER, start=1):
        spec = QUERY_MAP[code]
        print(f"   [{i}] {Ansi.style(code, Ansi.CYAN, Ansi.BOLD)} - {spec.title}")
    print(f"   [{Ansi.style('A', Ansi.GREEN, Ansi.BOLD)}] Executar roteiro oficial completo em sequencia (1 -> 2 -> 3 -> 4)")
    print()
    print(Ansi.style(" CONSULTAS EXTRAS DO ARTIGO (ARGUICAO DA BANCA):", Ansi.BOLD))
    for idx, code in enumerate(EXTRA_QUERY_ORDER, start=5):
        spec = QUERY_MAP[code]
        print(f"   [{idx:>2}] {Ansi.style(code, Ansi.CYAN)} - {spec.title}")
    print()
    print(Ansi.style(" CONTROLES E CONTINGENCIA:", Ansi.BOLD))
    print("   [C] Alternar Warm / Cold Cache   [V] Verificar container e bases (6,25M)")
    print("   [B] Alternar Online / Plano B    [O] Abrir .sqlplan grafico no VS Code")
    print("   [0] Sair")
    print(Ansi.style("------------------------------------------------------------------------------", Ansi.BLUE))


def interactive_loop(config: DemoConfig) -> None:
    """Loop principal do menu interativo."""
    if not config.offline_mode:
        ok, version, info_lines = check_live_environment()
        if ok:
            config.sql_version = version
        else:
            print()
            print(Ansi.style("[AVISO INICIAL] SQL Server ao vivo indisponivel no momento:", Ansi.YELLOW, Ansi.BOLD))
            for ln in info_lines:
                print(f"  {ln}")
            print(Ansi.style("Iniciando automaticamente em Modo Contingencia Offline (Plano B).", Ansi.MAGENTA, Ansi.BOLD))
            print(Ansi.style("Quando subir o Docker, pressione [B] no menu para voltar ao modo Ao Vivo.", Ansi.DIM))
            config.offline_mode = True

    while True:
        print_menu(config)
        choice = input("Escolha uma opcao: ").strip().upper()
        if choice in {"0", "Q", "SAIR", "EXIT"}:
            print("Encerrando demo interativa.")
            return
        if choice == "A":
            run_guided_official_sequence(config)
            input("\nRoteiro finalizado. Pressione Enter para voltar ao menu...")
            continue
        if choice == "C":
            config.cache_mode = "cold" if config.cache_mode == "warm" else "warm"
            continue
        if choice == "B":
            if config.offline_mode:
                ok, version, info_lines = check_live_environment()
                if ok:
                    config.sql_version = version
                    config.offline_mode = False
                else:
                    print()
                    for ln in info_lines:
                        print(f"  {Ansi.style(ln, Ansi.RED)}")
                    input("\nNao foi possivel ativar o modo Ao Vivo. Pressione Enter...")
            else:
                config.offline_mode = True
            continue
        if choice == "V":
            print()
            ok, version, info_lines = check_live_environment()
            if ok:
                config.sql_version = version
                config.offline_mode = False
                for ln in info_lines:
                    print(f"  {Ansi.style(ln, Ansi.GREEN)}")
            else:
                for ln in info_lines:
                    print(f"  {Ansi.style(ln, Ansi.RED)}")
            input("\nPressione Enter para voltar ao menu...")
            continue
        if choice == "O":
            open_sqlplan_in_vscode()
            input("\nPressione Enter para voltar ao menu...")
            continue

        code = MENU_SHORTCUTS.get(choice, choice)
        if code in QUERY_MAP:
            execute_scenario(QUERY_MAP[code], config)
            input("\nPressione Enter para voltar ao menu...")
        else:
            print(Ansi.style(f"Opcao invalida: {choice}", Ansi.RED))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Menu interativo para demonstracao pratica ao vivo (e Plano B) de BD II."
    )
    parser.add_argument("--offline", action="store_true", help="Inicia diretamente em Modo Plano B offline.")
    parser.add_argument("--cold", action="store_true", help="Inicia com Cold Cache ativo.")
    parser.add_argument("--check", action="store_true", help="Executa apenas verificacao de saude e sai.")
    parser.add_argument(
        "--run",
        metavar="CODE",
        help="Executa diretamente um cenario (Q1..Q10, W1 ou ALL) sem abrir o menu.",
    )
    parser.add_argument("--no-color", action="store_true", help="Desativa cores ANSI no terminal.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    Ansi.configure(use_color=not args.no_color)
    config = DemoConfig(
        offline_mode=args.offline,
        cache_mode="cold" if args.cold else "warm",
    )

    if args.check:
        ok, _ver, lines = check_live_environment()
        for ln in lines:
            print(ln)
        return 0 if ok else 1

    if args.run:
        target = args.run.strip().upper()
        if target == "ALL":
            for code in OFFICIAL_DEMO_ORDER:
                execute_scenario(QUERY_MAP[code], config)
            return 0
        if target not in QUERY_MAP:
            valid = ", ".join([q.code for q in QUERIES] + ["ALL"])
            print(f"Codigo invalido: {target}. Use um de: {valid}")
            return 2
        execute_scenario(QUERY_MAP[target], config)
        return 0

    interactive_loop(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
