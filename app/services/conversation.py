"""Prepara el historial que envía el navegador antes de dárselo al modelo.

El navegador no es de confianza: puede falsificar turnos del asistente o esconder instrucciones
en mensajes antiguos. Aquí se verifica, se sanea y se limita todo lo que llega.
"""
from typing import Any, Dict, List, Optional

from app.core.guard import inspect_message, sanitize
from app.core.signing import verify_message

MAX_HISTORY_MESSAGES = 20
REDACTED = "[mensaje omitido por seguridad]"

Message = Dict[str, Any]


def _clean(message: Message) -> Optional[Message]:
    if message["role"] == "assistant":
        # Solo se acepta lo que el servidor firmó; cualquier otro turno "del asistente" es falso.
        return {"role": "assistant", "content": message["content"]} if verify_message(message["content"], message.get("sig")) else None
    content = sanitize(message["content"])
    return {"role": "user", "content": content} if content else None


def _neutralize(message: Message) -> Message:
    """Un mensaje antiguo con un intento de manipulación no vuelve a llegar al modelo."""
    if message["role"] == "user" and not inspect_message(message["content"]).allowed:
        return {"role": "user", "content": REDACTED}
    return message


def prepare_messages(raw: List[Message]) -> List[Message]:
    cleaned = [m for m in map(_clean, raw) if m][-MAX_HISTORY_MESSAGES:]
    return [_neutralize(m) for m in cleaned[:-1]] + cleaned[-1:]
