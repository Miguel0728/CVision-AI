"""Almacenamiento persistente del uso de la demostración (SQLite).

Guarda en disco las preguntas por visitante y los tokens del día, así el contador
sobrevive a reinicios del servidor. Si cambias de motor (Redis, Postgres), basta con
otra clase con estos mismos métodos.
"""
import sqlite3
from pathlib import Path
from typing import List, Tuple

from app.database.sqlite_utils import connect


class SqliteUsageStore:
    def __init__(self, path: Path):
        self._path = path
        self._create_schema()

    def _create_schema(self) -> None:
        with connect(self._path) as conn:
            conn.execute("CREATE TABLE IF NOT EXISTS hits (visitor TEXT NOT NULL, ts REAL NOT NULL)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_hits_visitor ON hits (visitor, ts)")
            conn.execute("CREATE TABLE IF NOT EXISTS tokens (day TEXT PRIMARY KEY, total INTEGER NOT NULL)")

    def try_add_hit(self, visitor: str, now: float, window: int, limit: int) -> Tuple[bool, List[float]]:
        """Registra una pregunta si el visitante no superó el límite. Devuelve (permitida, golpes previos)."""
        with connect(self._path) as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("DELETE FROM hits WHERE ts <= ?", (now - window,))
            hits = self._hits_of(conn, visitor)
            allowed = len(hits) < limit
            if allowed:
                conn.execute("INSERT INTO hits (visitor, ts) VALUES (?, ?)", (visitor, now))
            conn.execute("COMMIT")
            return allowed, hits

    @staticmethod
    def _hits_of(conn: sqlite3.Connection, visitor: str) -> List[float]:
        rows = conn.execute("SELECT ts FROM hits WHERE visitor = ? ORDER BY ts", (visitor,))
        return [row[0] for row in rows]

    def recent_hits(self, visitor: str, since: float) -> List[float]:
        with connect(self._path) as conn:
            rows = conn.execute("SELECT ts FROM hits WHERE visitor = ? AND ts > ? ORDER BY ts", (visitor, since))
            return [row[0] for row in rows]

    def get_tokens(self, day: str) -> int:
        with connect(self._path) as conn:
            row = conn.execute("SELECT total FROM tokens WHERE day = ?", (day,)).fetchone()
            return row[0] if row else 0

    def add_tokens(self, day: str, amount: int) -> None:
        with connect(self._path) as conn:
            conn.execute(
                "INSERT INTO tokens (day, total) VALUES (?, ?) "
                "ON CONFLICT(day) DO UPDATE SET total = total + excluded.total",
                (day, amount),
            )
