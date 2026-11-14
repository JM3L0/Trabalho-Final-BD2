"""Smoke test da Parte 1.3: valida pymssql, @@VERSION, STATISTICS IO/TIME e STATISTICS XML."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.db import get_connection


def run_smoke_test() -> None:
    """Executa validacoes basicas de conexao e captura de metricas no SQL Server."""
    conn = get_connection("master", autocommit=True)
    messages: list[tuple[int, str]] = []

    def msg_handler(
        msgstate: int,
        severity: int,
        srvname: bytes | str,
        procname: bytes | str,
        line: int,
        msgtext: bytes | str,
    ) -> None:
        text = msgtext.decode("utf-8", errors="replace") if isinstance(msgtext, bytes) else str(msgtext)
        messages.append((severity, text))

    # pymssql expoe o manipulador de mensagens informacionais via _conn.set_msghandler
    conn._conn.set_msghandler(msg_handler)

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT @@VERSION;")
            version_row = cur.fetchone()
            print("[OK] @@VERSION:", version_row[0].splitlines()[0])

            # 1) Teste separado de SET STATISTICS IO, TIME ON
            cur.execute("SET STATISTICS IO ON; SET STATISTICS TIME ON;")
            while cur.nextset():
                pass
            messages.clear()

            cur.execute("SELECT TOP 50 object_id, name FROM sys.objects ORDER BY object_id;")
            rows = cur.fetchall()
            while cur.nextset():
                pass
            captured_messages = list(messages)
            cur.execute("SET STATISTICS IO OFF; SET STATISTICS TIME OFF;")
            while cur.nextset():
                pass
            print(f"[OK] Consulta IO/TIME retornou {len(rows)} linhas.")

            joined = "\n".join(text for _, text in captured_messages)
            has_io = bool(re.search(r"logical reads\s+\d+", joined))
            has_time = bool(re.search(r"SQL Server Execution Times:\s*CPU time\s*=\s*\d+\s*ms,\s*elapsed time\s*=\s*\d+\s*ms", joined))
            print(f"[OK] Mensagens capturadas ({len(captured_messages)}): has_io={has_io}, has_time={has_time}")
            if not (has_io and has_time):
                raise RuntimeError(f"Falha ao capturar STATISTICS IO/TIME. Mensagens recebidas:\n{joined}")

            # 2) Teste separado de SET STATISTICS XML ON
            try:
                cur.execute("SET STATISTICS XML ON;")
                while cur.nextset():
                    pass
                cur.execute("SELECT TOP 5 object_id, name FROM sys.objects ORDER BY object_id;")
                _data_rows = cur.fetchall()
                has_next = cur.nextset()
                xml_row = cur.fetchone() if has_next else None
                while cur.nextset():
                    pass
                xml_str = xml_row[0] if xml_row else ""
                if "<ShowPlanXML" not in str(xml_str):
                    raise RuntimeError("Falha ao capturar plano XML via SET STATISTICS XML ON.")
                print(f"[OK] Plano XML capturado com sucesso ({len(xml_str)} chars).")
            finally:
                cur.execute("SET STATISTICS XML OFF;")
                while cur.nextset():
                    pass
    finally:
        conn.close()


if __name__ == "__main__":
    run_smoke_test()
