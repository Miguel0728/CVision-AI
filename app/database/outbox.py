"""Bandeja de salida simulada: guarda los borradores de correo y marca cuáles se "enviaron".

Ningún correo real sale de aquí. Solo el servidor crea borradores (la herramienta del agente)
y solo un clic del usuario los marca como enviados.
"""
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.config.settings import OUTBOX_DB_PATH
from app.database.sqlite_utils import connect

COLUMNS = ("id", "candidate_id", "job_id", "to_name", "to_email", "subject", "body", "status", "created_at", "sent_at")


class SqliteOutbox:
    def __init__(self, path):
        self._path = path
        self._create_schema()

    def _create_schema(self) -> None:
        with connect(self._path) as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS emails ("
                "id TEXT PRIMARY KEY, candidate_id INTEGER, job_id INTEGER, to_name TEXT, to_email TEXT, "
                "subject TEXT, body TEXT, status TEXT, created_at REAL, sent_at REAL)"
            )

    def save_draft(self, email: Dict[str, Any]) -> Dict[str, Any]:
        record = {**email, "id": uuid.uuid4().hex, "status": "draft", "created_at": time.time(), "sent_at": None}
        placeholders = ", ".join("?" for _ in COLUMNS)
        with connect(self._path) as conn:
            conn.execute(f"INSERT INTO emails ({', '.join(COLUMNS)}) VALUES ({placeholders})", [record[c] for c in COLUMNS])
        return record

    def get(self, email_id: str) -> Optional[Dict[str, Any]]:
        with connect(self._path) as conn:
            row = conn.execute("SELECT * FROM emails WHERE id = ?", (email_id,)).fetchone()
        return dict(row) if row else None

    def mark_sent(self, email_id: str) -> Optional[Dict[str, Any]]:
        """Marca el borrador como enviado (una sola vez) y devuelve el registro actualizado."""
        with connect(self._path) as conn:
            conn.execute("UPDATE emails SET status = 'sent', sent_at = ? WHERE id = ? AND status = 'draft'", (time.time(), email_id))
        return self.get(email_id)


def public_view(record: Dict[str, Any]) -> Dict[str, Any]:
    """Lo que ve la interfaz de un correo (sin identificadores internos)."""
    sent_at = record.get("sent_at")
    return {
        "id": record["id"],
        "status": record["status"],
        "sent_at": datetime.fromtimestamp(sent_at, timezone.utc).isoformat() if sent_at else None,
        "to": {"name": record["to_name"], "email": record["to_email"]},
        "subject": record["subject"],
        "body": record["body"],
    }


outbox = SqliteOutbox(OUTBOX_DB_PATH)
