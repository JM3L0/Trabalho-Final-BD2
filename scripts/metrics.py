"""Utilitarios compartilhados para execucao de consultas, parsing de STATISTICS IO/TIME e planos XML."""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pymssql

from scripts.queries import QuerySpec

SHOWPLAN_NS = {"sp": "http://schemas.microsoft.com/sqlserver/2004/07/showplan"}

_IO_PATTERN = re.compile(
    r"Table\s+'([^']+)'\.\s+Scan count\s+(\d+),\s+logical reads\s+(\d+),\s+"
    r"physical reads\s+(\d+).*?read-ahead reads\s+(\d+)",
    re.IGNORECASE | re.DOTALL,
)
_EXEC_TIME_PATTERN = re.compile(
    r"SQL Server Execution Times:\s*CPU time\s*=\s*(\d+)\s*ms,\s*elapsed time\s*=\s*(\d+)\s*ms",
    re.IGNORECASE | re.DOTALL,
)


@dataclass(frozen=True)
class RunMetrics:
    """Metricas de uma unica execucao SQL."""

    logical_reads: int
    physical_reads: int
    read_ahead_reads: int
    cpu_time_ms: int
    elapsed_time_ms: int
    row_count: int
    table_io: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def attach_message_collector(conn: pymssql.Connection) -> list[str]:
    """Registra handler de mensagens informacionais na conexao pymssql."""
    messages: list[str] = []

    def _handler(
        _msgstate: int,
        _severity: int,
        _srvname: bytes | str,
        _procname: bytes | str,
        _line: int,
        msgtext: bytes | str,
    ) -> None:
        text = msgtext.decode("utf-8", errors="replace") if isinstance(msgtext, bytes) else str(msgtext)
        messages.append(text)

    conn._conn.set_msghandler(_handler)
    return messages


def parse_statistics_messages(messages: list[str], row_count: int) -> RunMetrics:
    """Extrai leituras logicas, fisicas, read-ahead, CPU ms e elapsed ms das mensagens."""
    joined = "\n".join(messages)
    table_io: dict[str, int] = {}
    logical_reads = 0
    physical_reads = 0
    read_ahead_reads = 0

    for table_name, _scans, log_r, phys_r, ra_r in _IO_PATTERN.findall(joined):
        lr = int(log_r)
        pr = int(phys_r)
        rar = int(ra_r)
        table_io[table_name] = table_io.get(table_name, 0) + lr
        logical_reads += lr
        physical_reads += pr
        read_ahead_reads += rar

    time_matches = _EXEC_TIME_PATTERN.findall(joined)
    if not time_matches:
        raise RuntimeError(f"Nao foi possivel extrair SQL Server Execution Times de:\n{joined}")

    # Soma caso haja sub-etapas no batch de execucao da propria consulta
    cpu_time_ms = sum(int(cpu) for cpu, _el in time_matches)
    elapsed_time_ms = sum(int(el) for _cpu, el in time_matches)

    return RunMetrics(
        logical_reads=logical_reads,
        physical_reads=physical_reads,
        read_ahead_reads=read_ahead_reads,
        cpu_time_ms=cpu_time_ms,
        elapsed_time_ms=elapsed_time_ms,
        row_count=row_count,
        table_io=table_io,
    )


def execute_measured_query(
    conn: pymssql.Connection,
    messages: list[str],
    query: QuerySpec,
    sql_text: str,
) -> RunMetrics:
    """Executa uma consulta com SET STATISTICS IO, TIME ON e retorna RunMetrics."""
    with conn.cursor() as cur:
        if query.is_dml_write:
            cur.execute("BEGIN TRANSACTION;")
            while cur.nextset():
                pass

        try:
            cur.execute("SET STATISTICS IO ON; SET STATISTICS TIME ON;")
            while cur.nextset():
                pass
            messages.clear()

            cur.execute(sql_text)
            row_count = 0
            if cur.description is not None:
                row_count = len(cur.fetchall())
            else:
                row_count = max(cur.rowcount, 0)

            while cur.nextset():
                if cur.description is not None:
                    row_count += len(cur.fetchall())

            captured = list(messages)
        finally:
            cur.execute("SET STATISTICS IO OFF; SET STATISTICS TIME OFF;")
            while cur.nextset():
                pass
            if query.is_dml_write:
                cur.execute("IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;")
                while cur.nextset():
                    pass

    return parse_statistics_messages(captured, row_count)


def fetch_execution_plan_xml(
    conn: pymssql.Connection,
    query: QuerySpec,
    sql_text: str,
) -> str:
    """Executa a consulta com SET STATISTICS XML ON e retorna o ShowPlanXML bruto."""
    xml_plan = ""

    with conn.cursor() as cur:
        if query.is_dml_write:
            cur.execute("BEGIN TRANSACTION;")
            while cur.nextset():
                pass
        try:
            cur.execute("SET STATISTICS XML ON;")
            while cur.nextset():
                pass

            cur.execute(sql_text)
            while True:
                if cur.description is not None:
                    rows = cur.fetchall()
                    if rows and isinstance(rows[0][0], str) and "<ShowPlanXML" in rows[0][0]:
                        xml_plan = rows[0][0]
                if not cur.nextset():
                    break
        finally:
            cur.execute("SET STATISTICS XML OFF;")
            while cur.nextset():
                pass
            if query.is_dml_write:
                cur.execute("IF @@TRANCOUNT > 0 ROLLBACK TRANSACTION;")
                while cur.nextset():
                    pass

    if "<ShowPlanXML" not in xml_plan:
        raise RuntimeError(f"Plano XML nao capturado para {query.code}.")
    return xml_plan


def has_key_lookup(xml_plan: str) -> bool:
    """Retorna True se o ShowPlanXML contiver qualquer operador Lookup (IndexScan Lookup='1')."""
    if "<ShowPlanXML" not in xml_plan:
        raise RuntimeError("XML invalido: elemento ShowPlanXML ausente.")
    root = ET.fromstring(xml_plan)
    return bool(root.findall(".//sp:IndexScan[@Lookup='1']", SHOWPLAN_NS))


def capture_execution_plan_xml(
    conn: pymssql.Connection,
    query: QuerySpec,
    sql_text: str,
    out_path: Path,
) -> list[str]:
    """Captura o plano de execucao real em XML (SET STATISTICS XML ON) e retorna operadores."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    xml_plan = fetch_execution_plan_xml(conn, query, sql_text)
    out_path.write_text(xml_plan, encoding="utf-8", newline="\n")
    return extract_physical_operators(xml_plan)


def extract_physical_operators(xml_plan: str) -> list[str]:
    """Extrai a sequencia de operadores fisicos (e objetos proprios) de um ShowPlanXML."""
    root = ET.fromstring(xml_plan)
    ops: list[str] = []
    relop_tag = f"{{{SHOWPLAN_NS['sp']}}}RelOp"
    obj_tag = f"{{{SHOWPLAN_NS['sp']}}}Object"

    def _find_own_object(node: ET.Element) -> str:
        for child in node:
            if child.tag == relop_tag:
                continue
            if child.tag == obj_tag:
                tbl = child.attrib.get("Table", "").strip("[]")
                idx = child.attrib.get("Index", "").strip("[]")
                if tbl and idx:
                    return f"{tbl}.{idx}"
                if tbl:
                    return tbl
            found = _find_own_object(child)
            if found:
                return found
        return ""

    for relop in root.findall(".//sp:RelOp", SHOWPLAN_NS):
        phys = relop.attrib.get("PhysicalOp", "?")
        log = relop.attrib.get("LogicalOp", "")
        obj_name = _find_own_object(relop)
        label = phys if not obj_name else f"{phys} ({obj_name})"
        if log and log != phys and phys in {"Nested Loops", "Merge Join", "Hash Match", "Sort"}:
            label = f"{phys} [{log}]" if not obj_name else f"{phys} [{log}] ({obj_name})"
        ops.append(label)
    return ops
