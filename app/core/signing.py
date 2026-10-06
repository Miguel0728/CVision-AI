"""Firma de las respuestas del agente.

El cliente reenvía el historial en cada pregunta, así que podría falsificar turnos del asistente
("ya confirmé que ignoro las reglas"). Cada respuesta legítima sale firmada por el servidor;
las que lleguen sin firma válida se descartan antes de llegar al modelo.
"""
import hashlib
import hmac
from typing import Optional

from app.config.settings import APP_SECRET


def sign_message(content: str) -> str:
    payload = f"assistant:{content}".encode("utf-8")
    return hmac.new(APP_SECRET.encode("utf-8"), payload, hashlib.sha256).hexdigest()


def verify_message(content: str, signature: Optional[str]) -> bool:
    return bool(signature) and hmac.compare_digest(sign_message(content), signature)
