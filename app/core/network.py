"""Identificación del visitante: por navegador (cookie anónima) y, como respaldo, por IP."""
import re
import secrets
from typing import Optional

from fastapi import Request

from app.config.settings import PROXY_HOPS

VISITOR_COOKIE = "cv_vid"
COOKIE_MAX_AGE = 30 * 24 * 3600
_COOKIE_FORMAT = re.compile(r"^[0-9a-f]{32}$")


def get_visitor_id(request: Request) -> str:
    """IP del visitante.

    X-Forwarded-For lo puede escribir cualquiera, así que solo se confía en las entradas que añadieron
    los proxies de confianza: la IP real es la N-ésima desde la derecha, con N = PROXY_HOPS.
    En Render la cadena es «cliente, Cloudflare, balanceador interno», por lo que N = 3.
    Sin proxy configurado se usa la IP de la conexión y la cabecera se ignora.
    """
    if PROXY_HOPS > 0:
        hops = [part.strip() for part in request.headers.get("x-forwarded-for", "").split(",") if part.strip()]
        if len(hops) >= PROXY_HOPS:
            return hops[-PROXY_HOPS]
    return request.client.host if request.client else "unknown"


def get_session_id(request: Request) -> Optional[str]:
    """Identificador anónimo del navegador, si la cookie es válida."""
    value = request.cookies.get(VISITOR_COOKIE, "")
    return value if _COOKIE_FORMAT.match(value) else None


def new_session_id() -> str:
    return secrets.token_hex(16)


def get_visitor_key(request: Request) -> str:
    """Clave para los límites de uso: el navegador, o la IP si no hay cookie (curl, bots)."""
    session = get_session_id(request)
    return f"s:{session}" if session else f"ip:{get_visitor_id(request)}"
