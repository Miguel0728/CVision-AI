"""Conexión SQLite compartida por los almacenes de la aplicación."""
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


@contextmanager
def connect(path) -> Iterator[sqlite3.Connection]:
    """Abre una conexión en modo autocommit; las transacciones se abren de forma explícita."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()
