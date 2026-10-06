"""Identificación del visitante a partir de la conexión."""
from fastapi import Request

from app.config.settings import PROXY_HOPS


def get_visitor_id(request: Request) -> str:
    """IP del visitante.

    X-Forwarded-For lo puede escribir cualquiera, así que solo se confía en la entrada que añadió
    el último proxy de confianza (la N-ésima desde la derecha, con N = PROXY_HOPS). Sin proxy
    configurado se usa la IP de la conexión y la cabecera se ignora.
    """
    if PROXY_HOPS > 0:
        hops = [part.strip() for part in request.headers.get("x-forwarded-for", "").split(",") if part.strip()]
        if len(hops) >= PROXY_HOPS:
            return hops[-PROXY_HOPS]
    return request.client.host if request.client else "unknown"
