"""Menu interativo para demonstracao pratica ao vivo (e contingencia Plano B) da apresentacao."""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.db import DATA_DIR, RESULTS_DIR, get_connection, load_db_config
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

LIVE_MENU_LABELS: dict[str, str] = {
    "Q1": "Scan vs. Seek (Email)",
    "Q3": "Indice Composto (Status + Data)",
    "Q4": "Covering Index (Sem Key Lookup)",
    "W1": "Escrita 10k INSERT + Rollback",
}

ARTICLE_MENU_LABELS: dict[str, str] = {
    "Q1": "Email (Scan vs. Seek)",
    "Q2": "Faixa de datas (DataPedido)",
    "Q3": "Composto (Status + Data)",
    "Q4": "Covering Index (INCLUDE)",
    "Q5": "Juncao 3 tabelas (JOIN)",
    "Q6": "TOP 50 ORDER BY DESC (Sem Sort)",
    "Q7": "GROUP BY (Batch vs. Row Mode)",
    "Q8": "LIKE '%x' vs. LIKE 'x%'",
    "Q9": "YEAR(Data) vs. intervalo",
    "Q10": "Subconsulta vs. NOT EXISTS",
    "W1": "Escrita 10k INSERT + Rollback",
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
    started_container: bool = False
    keep_up: bool = False
    no_docker: bool = False
    verbose: bool = False


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


_NOISE_OPS = {
    "Compute Scalar",
    "Constant Scan",
    "Concatenation",
    "Merge Interval",
    "Table Spool",
    "Row Count Spool",
    "Assert",
    "Top",
    "Filter",
    "Segment",
    "Parallelism",
}


def summarize_plan_ops(analysis: PlanAnalysis) -> str:
    """Resume os operadores fisicos principais de um ShowPlanXML em uma linha limpa."""
    insert_nodes = [
        n
        for n in analysis.nodes
        if "Insert" in n.physical_op or "Update" in n.physical_op or "Delete" in n.physical_op
    ]
    if insert_nodes:
        targets = [n.object_name.split(".")[-1] if n.object_name else n.physical_op for n in insert_nodes]
        has_seq = any(n.physical_op == "Sequence" for n in analysis.nodes)
        if has_seq and len(targets) > 1:
            return f"Sequence -> {len(targets)} B+ Trees ({', '.join(targets)})"
        return " + ".join(
            f"{n.physical_op} ({n.object_name})" if n.object_name else n.physical_op for n in insert_nodes
        )

    meaningful = [n for n in analysis.nodes if n.physical_op not in _NOISE_OPS]
    if not meaningful:
        meaningful = list(analysis.nodes)

    if not analysis.has_lookup:
        non_nl = [n for n in meaningful if n.physical_op != "Nested Loops"]
        if len(non_nl) == 1:
            meaningful = non_nl

    parts: list[str] = []
    for n in meaningful:
        if n.is_lookup:
            label = f"Key Lookup ({n.object_name})" if n.object_name else "Key Lookup"
        elif n.logical_op and n.logical_op != n.physical_op and n.physical_op in {"Hash Match", "Merge Join", "Stream Aggregate"}:
            label = f"{n.physical_op} [{n.logical_op}]"
        else:
            label = f"{n.physical_op} ({n.object_name})" if n.object_name else n.physical_op
        if label not in parts:
            parts.append(label)

    summary = " -> ".join(parts)
    if analysis.primary_mode == "Batch":
        summary += " [Batch]"
    elif any(n.physical_op in {"Stream Aggregate", "Hash Match"} for n in meaningful):
        summary += f" [{analysis.primary_mode}]"
    return summary


def print_sql_compact(spec: QuerySpec) -> None:
    """Exibe a consulta SQL de forma enxuta."""
    if spec.sql_baseline == spec.sql_optimized:
        print(f"SQL: {Ansi.style(spec.sql_baseline, Ansi.CYAN)}")
    else:
        print(f"{Ansi.style('SQL Base:', Ansi.YELLOW)} {spec.sql_baseline}")
        print(f"{Ansi.style('SQL Otim:', Ansi.GREEN)} {spec.sql_optimized}")


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


def show_q4_intermediate_compact() -> None:
    """Exibe em 1 linha o Estagio 2 de Q4 (indice simples sem INCLUDE)."""
    inter_plan = PLANS_DIR / "optimized" / "q4_intermediate_lookup.sqlplan"
    if not Q4_INTERMEDIATE_JSON.exists() and not inter_plan.exists():
        return
    reads_txt = "1.296"
    ms_txt = "1"
    if Q4_INTERMEDIATE_JSON.exists():
        data = json.loads(Q4_INTERMEDIATE_JSON.read_text(encoding="utf-8"))
        m = data.get("metrics", {})
        reads_txt = fmt_int(m.get("logical_reads", 1296))
        ms_txt = str(m.get("elapsed_time_ms", 1))
    print(
        Ansi.style("  Ref. Estagio 2 : ", Ansi.CYAN)
        + f"{reads_txt} pag | {ms_txt} ms | Index Seek + 422 Key Lookups (sem INCLUDE)"
    )


def show_q4_intermediate_stage() -> None:
    """Exibe o estagio intermediario de Q4 (Index Seek + 422 Key Lookups) como ponte didatica."""
    inter_plan = PLANS_DIR / "optimized" / "q4_intermediate_lookup.sqlplan"
    if not Q4_INTERMEDIATE_JSON.exists() and not inter_plan.exists():
        return
    print()
    print(Ansi.style("Estagio 2 de Q4 (referencia pre-capturada; sem DDL ao vivo):", Ansi.CYAN, Ansi.BOLD))
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


def detect_compose_command() -> list[str] | None:
    """Retorna o comando Docker Compose disponivel (v2 ou legado)."""
    if not shutil.which("docker"):
        return None
    v2 = subprocess.run(
        ["docker", "compose", "version"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if v2.returncode == 0:
        return ["docker", "compose"]
    if shutil.which("docker-compose"):
        return ["docker-compose"]
    return None


def is_docker_daemon_ready() -> tuple[bool, str]:
    """Verifica se a CLI Docker e o daemon/Docker Desktop estao ativos."""
    if not shutil.which("docker"):
        return False, "Comando 'docker' nao encontrado no PATH."
    res = subprocess.run(
        ["docker", "info"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    if res.returncode != 0:
        detail = (res.stderr or res.stdout or "").strip().splitlines()
        msg = detail[-1] if detail else "Docker daemon nao esta em execucao."
        return False, f"Docker indisponivel (abra o Docker Desktop / servico docker): {msg}"
    return True, "Docker ativo."


def is_container_running() -> bool:
    """Verifica se o container bd2_sqlserver ja esta em execucao."""
    if not shutil.which("docker"):
        return False
    res = subprocess.run(
        ["docker", "ps", "--filter", "name=^/bd2_sqlserver$", "--format", "{{.Status}}"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    return res.returncode == 0 and bool(res.stdout.strip())


def start_container() -> tuple[bool, str]:
    """Sobe o container SQL Server 2022 via docker compose up -d --wait."""
    daemon_ok, daemon_msg = is_docker_daemon_ready()
    if not daemon_ok:
        return False, daemon_msg

    compose_cmd = detect_compose_command()
    if not compose_cmd:
        return False, "Docker Compose nao encontrado ('docker compose' ou 'docker-compose')."

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if os.name != "nt":
        try:
            DATA_DIR.chmod(0o777)
        except OSError:
            pass

    print(Ansi.style("Subindo container bd2_sqlserver (docker compose up -d --wait)...", Ansi.CYAN, Ansi.BOLD))
    res = subprocess.run(
        [*compose_cmd, "up", "-d", "--wait"],
        cwd=ROOT_DIR,
        check=False,
    )
    if res.returncode != 0:
        return False, f"Falha ao executar {' '.join(compose_cmd)} up -d --wait (codigo {res.returncode})."
    return True, "Container bd2_sqlserver iniciado e saudavel."


def stop_container() -> tuple[bool, str]:
    """Derruba o container bd2_sqlserver preservando o volume mssql_data (sem -v)."""
    daemon_ok, daemon_msg = is_docker_daemon_ready()
    if not daemon_ok:
        return False, daemon_msg

    compose_cmd = detect_compose_command()
    if not compose_cmd:
        return False, "Docker Compose nao encontrado."

    print(Ansi.style("\nDerrubando container bd2_sqlserver (docker compose down, preservando volume)...", Ansi.YELLOW))
    res = subprocess.run(
        [*compose_cmd, "down"],
        cwd=ROOT_DIR,
        check=False,
    )
    if res.returncode != 0:
        return False, f"Falha ao derrubar container (codigo {res.returncode})."
    return True, "Container bd2_sqlserver derrubado com seguranca (dados preservados no volume mssql_data)."


def _can_connect_master() -> tuple[bool, str]:
    """Verifica se o SQL Server aceita conexoes na base master."""
    try:
        with get_connection("master", autocommit=True, timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT @@VERSION;")
                version = str(cur.fetchone()[0]).splitlines()[0].strip()
        return True, version
    except Exception as exc:
        return False, str(exc)


def provision_databases_if_needed(*, interactive: bool) -> bool:
    """Se o container subiu sem as bases prontas, executa o pipeline de carga e indices."""
    master_ok, detail = _can_connect_master()
    if not master_ok:
        print(Ansi.style(f"[AVISO] SQL Server ainda nao respondeu no master: {detail}", Ansi.YELLOW))
        return False

    print()
    print(Ansi.style("[BASES AUSENTES] O container subiu, mas Ecommerce_Baseline / Ecommerce_Otimizado nao estao completas.", Ansi.YELLOW, Ansi.BOLD))
    if interactive:
        ans = input("Deseja gerar/carregar os 6,25M de registros e criar os 9 indices agora? [S/n]: ").strip().lower()
        if ans not in {"", "s", "sim", "y", "yes"}:
            return False

    steps: list[tuple[str, Path]] = []
    required_csvs = ("clientes.csv", "produtos.csv", "pedidos.csv", "itens_pedido.csv")
    if not all((DATA_DIR / csv_name).exists() for csv_name in required_csvs):
        steps.append(("Geracao do dataset sintetico (6,25M linhas)", ROOT_DIR / "scripts" / "generate_data.py"))
    steps.extend(
        [
            ("Criacao do esquema Baseline", ROOT_DIR / "scripts" / "create_schema.py"),
            ("Carga massiva via BULK INSERT", ROOT_DIR / "scripts" / "load_baseline.py"),
            ("Clonagem de Ecommerce_Otimizado (BACKUP/RESTORE)", ROOT_DIR / "scripts" / "clone_optimized.py"),
            ("Aplicacao dos 9 indices secundarios", ROOT_DIR / "scripts" / "apply_optimizations.py"),
        ]
    )

    for label, script_path in steps:
        print(Ansi.style(f"\n>>> Provisionando: {label}...", Ansi.CYAN, Ansi.BOLD))
        res = subprocess.run([sys.executable, str(script_path)], cwd=ROOT_DIR, check=False)
        if res.returncode != 0:
            print(Ansi.style(f"[ERRO] Falha na etapa '{label}' (codigo {res.returncode}).", Ansi.RED, Ansi.BOLD))
            return False
    return True


def ensure_live_startup(config: DemoConfig, *, interactive: bool) -> None:
    """Garante container ativo e ambiente validado ao iniciar, ou ativa Plano B se indisponivel."""
    if config.offline_mode:
        return

    ok, version, info_lines = check_live_environment()
    if ok:
        config.sql_version = version
        return

    if not config.no_docker:
        already_up = is_container_running()
        if not already_up:
            started_ok, start_msg = start_container()
            if started_ok:
                config.started_container = True
                # Pequena espera extra caso o SQL Server tenha acabado de concluir recovery
                for _ in range(5):
                    ok, version, info_lines = check_live_environment()
                    if ok:
                        config.sql_version = version
                        return
                    master_ok, _ = _can_connect_master()
                    if master_ok:
                        break
                    time.sleep(2)
            else:
                print()
                print(Ansi.style(f"[AVISO] {start_msg}", Ansi.YELLOW, Ansi.BOLD))

        ok, version, info_lines = check_live_environment()
        if ok:
            config.sql_version = version
            return

        if is_container_running() and provision_databases_if_needed(interactive=interactive):
            ok, version, info_lines = check_live_environment()
            if ok:
                config.sql_version = version
                return

    print()
    print(Ansi.style("[AVISO INICIAL] SQL Server ao vivo indisponivel no momento:", Ansi.YELLOW, Ansi.BOLD))
    for ln in info_lines:
        print(f"  {ln}")
    print(Ansi.style("Iniciando automaticamente em Modo Contingencia Offline (Plano B).", Ansi.MAGENTA, Ansi.BOLD))
    print(Ansi.style("Quando o Docker estiver pronto, use [3] Controles -> [2] Alternar Modo.", Ansi.DIM))
    config.offline_mode = True


def teardown_on_exit(config: DemoConfig, *, interactive: bool) -> None:
    """Derruba o container ao encerrar se ele foi subido pelo script (ou se o usuario confirmar)."""
    if config.no_docker or config.keep_up:
        if config.started_container:
            print(Ansi.style("Mantendo container bd2_sqlserver em execucao (--keep-up).", Ansi.DIM))
        return

    if config.started_container:
        ok, msg = stop_container()
        color = Ansi.GREEN if ok else Ansi.YELLOW
        print(Ansi.style(msg, color))
        return

    if interactive and not config.offline_mode and is_container_running():
        try:
            ans = input("Container bd2_sqlserver ja estava rodando antes. Deseja derrubar agora? [s/N]: ").strip().lower()
        except EOFError:
            ans = ""
        if ans in {"s", "sim", "y", "yes"}:
            ok, msg = stop_container()
            color = Ansi.GREEN if ok else Ansi.YELLOW
            print(Ansi.style(msg, color))


def run_live_scenario(spec: QuerySpec, cache_mode: str, *, verbose: bool = False) -> None:
    """Executa consulta ao vivo nas duas bases gemeas e exibe metricas + planos reais."""
    print()
    title_line = f"-- [{spec.code}] {spec.title} "
    print(Ansi.style(title_line + "-" * max(4, 74 - len(title_line)), Ansi.BLUE, Ansi.BOLD))
    if verbose:
        print(f"Categoria: {spec.category} | Cache: {cache_mode.upper()} | MAXDOP 1")
        print_sql_block(spec)
    else:
        print_sql_compact(spec)

    with (
        get_connection("Ecommerce_Baseline", autocommit=True, timeout=60) as conn_base,
        get_connection("Ecommerce_Otimizado", autocommit=True, timeout=60) as conn_opt,
    ):
        msg_base = attach_message_collector(conn_base)
        msg_opt = attach_message_collector(conn_opt)

        if cache_mode == "cold":
            print(Ansi.style("Limpando cache (Cold Cache)...", Ansi.YELLOW))
            clear_caches(conn_base)
            clear_caches(conn_opt)
        elif not spec.is_dml_write:
            execute_measured_query(conn_base, msg_base, spec, spec.sql_baseline)
            execute_measured_query(conn_opt, msg_opt, spec, spec.sql_optimized)

        m_base: RunMetrics = execute_measured_query(conn_base, msg_base, spec, spec.sql_baseline)
        m_opt: RunMetrics = execute_measured_query(conn_opt, msg_opt, spec, spec.sql_optimized)

        xml_base = fetch_execution_plan_xml(conn_base, spec, spec.sql_baseline)
        xml_opt = fetch_execution_plan_xml(conn_opt, spec, spec.sql_optimized)
        plan_base = analyze_showplan_xml(xml_base)
        plan_opt = analyze_showplan_xml(xml_opt)

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

        if verbose:
            print()
            print(Ansi.style("Planos de Execucao Reais Capturados Agora (ShowPlanXML):", Ansi.BOLD))
            render_plan_tree("Ecommerce_Baseline ", plan_base, accent=Ansi.YELLOW)
            print()
            render_plan_tree("Ecommerce_Otimizado", plan_opt, accent=Ansi.GREEN)
            if spec.code == "Q4":
                show_q4_intermediate_stage()
        else:
            print()
            print(f"  {Ansi.style('Plano Baseline :', Ansi.YELLOW)} {summarize_plan_ops(plan_base)}")
            print(f"  {Ansi.style('Plano Otimizado:', Ansi.GREEN)} {summarize_plan_ops(plan_opt)}")
            if spec.code == "Q4":
                show_q4_intermediate_compact()

        if spec.is_dml_write:
            with conn_base.cursor() as cur_b, conn_opt.cursor() as cur_o:
                cur_b.execute("SELECT COUNT_BIG(*), @@TRANCOUNT FROM dbo.ItensPedido;")
                cnt_b, tran_b = cur_b.fetchone()
                cur_o.execute("SELECT COUNT_BIG(*), @@TRANCOUNT FROM dbo.ItensPedido;")
                cnt_o, tran_o = cur_o.fetchone()
            print(
                Ansi.style(
                    f"  ROLLBACK OK    : Baseline={fmt_int(cnt_b)} | Otimizado={fmt_int(cnt_o)} (@@TRANCOUNT={tran_b}/{tran_o})",
                    Ansi.GREEN,
                    Ansi.BOLD,
                )
            )


def run_offline_scenario(spec: QuerySpec, cache_mode: str, *, verbose: bool = False) -> None:
    """Plano B: exibe estatisticas reais (summary_stats.json) e planos .sqlplan pre-capturados."""
    print()
    title_line = f"-- [{spec.code}] {spec.title} [PLANO B] "
    print(Ansi.style(title_line + "-" * max(4, 74 - len(title_line)), Ansi.MAGENTA, Ansi.BOLD))
    if verbose:
        print(f"Categoria: {spec.category} | Cache: {cache_mode.upper()} (dados do experimento)")
        print_sql_block(spec)
    else:
        print_sql_compact(spec)

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
    base_plan_path = PLANS_DIR / "baseline" / f"{code_lower}_baseline.sqlplan"
    opt_plan_path = PLANS_DIR / "optimized" / f"{code_lower}_optimized.sqlplan"

    if verbose:
        print()
        print(Ansi.style("Planos de Execucao Pre-Capturados (.sqlplan):", Ansi.BOLD))
        if base_plan_path.exists():
            render_plan_tree(
                f"Baseline  ({base_plan_path.name})",
                analyze_showplan_xml(base_plan_path.read_text(encoding="utf-8")),
                accent=Ansi.YELLOW,
            )
        if opt_plan_path.exists():
            print()
            render_plan_tree(
                f"Otimizado ({opt_plan_path.name})",
                analyze_showplan_xml(opt_plan_path.read_text(encoding="utf-8")),
                accent=Ansi.GREEN,
            )
        if spec.code == "Q4":
            show_q4_intermediate_stage()
    else:
        print()
        if base_plan_path.exists():
            p_base = analyze_showplan_xml(base_plan_path.read_text(encoding="utf-8"))
            print(f"  {Ansi.style('Plano Baseline :', Ansi.YELLOW)} {summarize_plan_ops(p_base)}")
        if opt_plan_path.exists():
            p_opt = analyze_showplan_xml(opt_plan_path.read_text(encoding="utf-8"))
            print(f"  {Ansi.style('Plano Otimizado:', Ansi.GREEN)} {summarize_plan_ops(p_opt)}")
        if spec.code == "Q4":
            show_q4_intermediate_compact()


def execute_scenario(spec: QuerySpec, config: DemoConfig) -> None:
    """Executa no modo atual; se falhar conexao ao vivo, oferece fallback imediato para Plano B."""
    if config.offline_mode:
        run_offline_scenario(spec, config.cache_mode, verbose=config.verbose)
        return
    try:
        run_live_scenario(spec, config.cache_mode, verbose=config.verbose)
    except Exception as exc:
        print()
        print(Ansi.style(f"[ERRO AO VIVO] Nao foi possivel executar no SQL Server: {exc}", Ansi.RED, Ansi.BOLD))
        choice = input("Ativar Modo Contingencia Offline (Plano B) agora para esta consulta? [S/n]: ").strip().lower()
        if choice in {"", "s", "sim", "y", "yes"}:
            config.offline_mode = True
            run_offline_scenario(spec, config.cache_mode, verbose=config.verbose)


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


def print_main_menu() -> None:
    """Exibe o menu principal enxuto."""
    print()
    print(Ansi.style("== DEMO BD II (SQL Server 2022) ==", Ansi.BLUE, Ansi.BOLD))
    print("  [1] Apresentacao ao Vivo")
    print("  [2] Consultas do Artigo")
    print("  [3] Controles")
    print("  [0] Sair")


def live_presentation_menu(config: DemoConfig) -> None:
    """Submenu rapido para execucao durante a apresentacao ao vivo."""
    shortcuts = {str(i): code for i, code in enumerate(OFFICIAL_DEMO_ORDER, start=1)}
    while True:
        print()
        print(Ansi.style("-- Apresentacao ao Vivo --", Ansi.CYAN, Ansi.BOLD))
        for idx, code in shortcuts.items():
            print(f"  [{idx}] {Ansi.style(code, Ansi.CYAN, Ansi.BOLD)} - {LIVE_MENU_LABELS[code]}")
        print(f"  [{Ansi.style('5', Ansi.GREEN, Ansi.BOLD)}] Rodar todos em sequencia")
        print("  [0] Voltar")
        choice = input("Opcao: ").strip().upper()
        if choice in {"0", "V", "VOLTAR", ""}:
            return
        if choice == "5":
            run_guided_official_sequence(config)
            input("\nConcluido. Enter para continuar...")
            continue
        code = shortcuts.get(choice, choice)
        if code in QUERY_MAP:
            execute_scenario(QUERY_MAP[code], config)
            input("\nEnter para continuar...")
        else:
            print(Ansi.style(f"Opcao invalida: {choice}", Ansi.RED))


def article_queries_menu(config: DemoConfig) -> None:
    """Submenu com todas as 11 operacoes do artigo (Q1-Q10 e W1)."""
    shortcuts = {str(i): q.code for i, q in enumerate(QUERIES, start=1)}
    while True:
        print()
        print(Ansi.style("-- Consultas do Artigo --", Ansi.CYAN, Ansi.BOLD))
        for idx, q in enumerate(QUERIES, start=1):
            print(f"  [{idx:>2}] {Ansi.style(f'{q.code:<3}', Ansi.CYAN)} - {ARTICLE_MENU_LABELS[q.code]}")
        print("  [ 0] Voltar")
        choice = input("Opcao: ").strip().upper()
        if choice in {"0", "V", "VOLTAR", ""}:
            return
        code = shortcuts.get(choice, choice)
        if code in QUERY_MAP:
            execute_scenario(QUERY_MAP[code], config)
            input("\nEnter para continuar...")
        else:
            print(Ansi.style(f"Opcao invalida: {choice}", Ansi.RED))


def controls_menu(config: DemoConfig) -> None:
    """Submenu essencial de cache, modo e verificacao do ambiente."""
    while True:
        print()
        print(Ansi.style("-- Controles --", Ansi.BLUE, Ansi.BOLD))
        print("  [1] Alternar Cache (Warm / Cold)")
        print("  [2] Alternar Modo (Ao Vivo / Plano B)")
        print("  [3] Verificar ambiente")
        print("  [0] Voltar")
        choice = input("Opcao: ").strip().upper()
        if choice in {"0", "V", "VOLTAR", ""}:
            return
        if choice == "1":
            config.cache_mode = "cold" if config.cache_mode == "warm" else "warm"
            print(Ansi.style(f"Cache ativo: {config.cache_mode.upper()}", Ansi.CYAN))
            continue
        if choice == "2":
            if config.offline_mode:
                config.offline_mode = False
                config.no_docker = False
                ensure_live_startup(config, interactive=True)
                if not config.offline_mode:
                    print(Ansi.style("Modo ativo: AO VIVO", Ansi.GREEN))
            else:
                config.offline_mode = True
                print(Ansi.style("Modo ativo: PLANO B", Ansi.MAGENTA))
            continue
        if choice == "3":
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
            input("\nEnter para continuar...")
            continue
        print(Ansi.style(f"Opcao invalida: {choice}", Ansi.RED))


def interactive_loop(config: DemoConfig) -> None:
    """Loop principal do menu interativo com ciclo completo do container."""
    ensure_live_startup(config, interactive=True)

    try:
        while True:
            print_main_menu()
            choice = input("Opcao: ").strip().upper()
            if choice in {"0", "Q", "SAIR", "EXIT"}:
                print("Encerrando...")
                return
            if choice == "1":
                live_presentation_menu(config)
            elif choice == "2":
                article_queries_menu(config)
            elif choice == "3":
                controls_menu(config)
            elif choice in QUERY_MAP:
                execute_scenario(QUERY_MAP[choice], config)
                input("\nEnter para continuar...")
            else:
                print(Ansi.style(f"Opcao invalida: {choice}", Ansi.RED))
    except KeyboardInterrupt:
        print("\nEncerrando com seguranca...")
    finally:
        teardown_on_exit(config, interactive=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Menu interativo para demonstracao pratica ao vivo (e Plano B) de BD II."
    )
    parser.add_argument("--offline", action="store_true", help="Inicia diretamente em Modo Plano B offline.")
    parser.add_argument("--cold", action="store_true", help="Inicia com Cold Cache ativo.")
    parser.add_argument("--keep-up", action="store_true", help="Nao derruba o container ao sair.")
    parser.add_argument("--no-docker", action="store_true", help="Nao tenta subir nem derrubar o container via Docker.")
    parser.add_argument("--check", action="store_true", help="Executa apenas verificacao de saude e sai.")
    parser.add_argument(
        "--run",
        metavar="CODE",
        help="Executa diretamente um cenario (Q1..Q10, W1 ou ALL) sem abrir o menu.",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Exibe arvore completa de planos e I/O por tabela.")
    parser.add_argument("--no-color", action="store_true", help="Desativa cores ANSI no terminal.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    Ansi.configure(use_color=not args.no_color)
    config = DemoConfig(
        offline_mode=args.offline,
        cache_mode="cold" if args.cold else "warm",
        keep_up=args.keep_up,
        no_docker=args.no_docker,
        verbose=args.verbose,
    )

    if args.check:
        ok, _ver, lines = check_live_environment()
        for ln in lines:
            print(ln)
        return 0 if ok else 1

    if args.run:
        target = args.run.strip().upper()
        if target != "ALL" and target not in QUERY_MAP:
            valid = ", ".join([q.code for q in QUERIES] + ["ALL"])
            print(f"Codigo invalido: {target}. Use um de: {valid}")
            return 2

        ensure_live_startup(config, interactive=False)
        try:
            if target == "ALL":
                for code in OFFICIAL_DEMO_ORDER:
                    execute_scenario(QUERY_MAP[code], config)
            else:
                execute_scenario(QUERY_MAP[target], config)
        finally:
            teardown_on_exit(config, interactive=False)
        return 0

    interactive_loop(config)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
