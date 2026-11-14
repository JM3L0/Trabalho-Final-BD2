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
