"""Utilitarios compartilhados de configuracao e conexao com o SQL Server."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

import pymssql
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
PAPER_DIR = ROOT_DIR / "paper"
RESULTS_DIR = ROOT_DIR / "results"


@dataclass(frozen=True)
class DbConfig:
    """Parametros de conexao com o Microsoft SQL Server."""

    host: str
    port: int
    user: str
    password: str


def load_db_config() -> DbConfig:
    """Carrega configuracao do .env (se existir) com defaults compativeis com docker-compose.yml."""
    env_path = ROOT_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    return DbConfig(
        host=os.getenv("MSSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MSSQL_PORT", "1433")),
        user=os.getenv("MSSQL_USER", "sa"),
        password=os.getenv("MSSQL_SA_PASSWORD", "Bd2Trabalho!2026"),
    )


def get_connection(
    database: str = "master",
    *,
    autocommit: bool = True,
    timeout: int = 30,
) -> pymssql.Connection:
    """Abre conexao pymssql para o banco informado."""
    cfg = load_db_config()
    try:
        return pymssql.connect(
            server=cfg.host,
            port=cfg.port,
            user=cfg.user,
            password=cfg.password,
            database=database,
            autocommit=autocommit,
            timeout=timeout,
            charset="UTF-8",
        )
    except pymssql.OperationalError as exc:
        # No SQL Server, tentar conectar diretamente a um banco inexistente gera erro 18456 (Login failed).
        # Validamos se o banco realmente existe conectando em master para emitir mensagem amigavel.
        if database != "master" and "18456" in str(exc):
            try:
                with pymssql.connect(
                    server=cfg.host,
                    port=cfg.port,
                    user=cfg.user,
                    password=cfg.password,
                    database="master",
                    autocommit=True,
                    timeout=5,
                    charset="UTF-8",
                ) as master_conn:
                    with master_conn.cursor() as cur:
                        cur.execute("SELECT COUNT(*) FROM sys.databases WHERE name = %s;", (database,))
                        if cur.fetchone()[0] == 0:
                            raise RuntimeError(
                                f"\n[ERRO DE CONEXAO] O banco de dados '{database}' ainda nao foi criado!\n"
                                f"No SQL Server, tentar conectar em uma base inexistente retorna 'Login failed for user sa' (18456).\n"
                                f"Para resolver, execute os passos anteriores do pipeline na ordem correta:\n"
                                f"  - Se for 'Ecommerce_Baseline': execute 'python scripts/create_schema.py' e 'python scripts/load_baseline.py'\n"
                                f"  - Se for 'Ecommerce_Otimizado': execute o Passo 6 antes deste: 'python scripts/clone_optimized.py'\n"
                            ) from exc
            except RuntimeError:
                raise
            except Exception:
                pass
        raise
