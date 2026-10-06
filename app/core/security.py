"""Protecciones de la capa web: cabeceras, origen de las peticiones, tamaño del cuerpo y ritmo de uso."""
import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict
from urllib.parse import urlparse

from fastapi import Request
from fastapi.responses import JSONResponse

from app.config.settings import ALLOWED_HOSTS, API_REQUESTS_PER_MINUTE
from app.core.network import get_visitor_id

STATE_CHANGING = {"POST", "PUT", "PATCH", "DELETE"}

CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self'",
    "style-src-attr 'unsafe-inline'",  # solo atributos style="--i: n" generados por la interfaz
    "img-src 'self' data:",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'none'",
    "form-action 'self'",
    "frame-ancestors 'none'",
])

SECURITY_HEADERS = {
    "Content-Security-Policy": CSP,
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-origin",
}


def _is_https(request: Request) -> bool:
    return request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https"


def add_security_headers(request: Request, response) -> None:
    for name, value in SECURITY_HEADERS.items():
        response.headers[name] = value
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    if _is_https(request):
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if "server" in response.headers:
        del response.headers["server"]


def _origin_allowed(origin: str, request: Request) -> bool:
    host = urlparse(origin).netloc.lower()
    return host == request.headers.get("host", "").lower() or host.split(":")[0] in ALLOWED_HOSTS


def is_cross_origin(request: Request) -> bool:
    """Una petición que cambia datos y viene de otra web (CSRF) lleva un Origin ajeno."""
    origin = request.headers.get("origin")
    if request.method not in STATE_CHANGING or not origin:
        return False
    return not _origin_allowed(origin, request)


class ApiRateLimiter:
    """Ritmo general de la API por visitante (independiente del límite de gasto del modelo)."""

    WINDOW_SECONDS = 60
    MAX_TRACKED = 5000

    def __init__(self, per_minute: int):
        self._per_minute = per_minute
        self._hits: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, visitor: str) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[visitor]
            while hits and now - hits[0] > self.WINDOW_SECONDS:
                hits.popleft()
            if len(hits) >= self._per_minute:
                return False
            hits.append(now)
            if len(self._hits) > self.MAX_TRACKED:
                self._prune(now)
            return True

    def _prune(self, now: float) -> None:
        stale = [v for v, hits in self._hits.items() if not hits or now - hits[-1] > self.WINDOW_SECONDS]
        for visitor in stale:
            del self._hits[visitor]


api_limiter = ApiRateLimiter(API_REQUESTS_PER_MINUTE)


def reject(status: int, message: str) -> JSONResponse:
    return JSONResponse({"detail": message}, status_code=status)


class _TooLarge(Exception):
    pass


class BodyLimitMiddleware:
    """Corta las peticiones cuyo cuerpo supera el máximo, aunque no declaren su tamaño."""

    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def _send_413(self, send) -> None:
        body = b'{"detail":"La petici\\u00f3n es demasiado grande."}'
        headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]
        await send({"type": "http.response.start", "status": 413, "headers": headers})
        await send({"type": "http.response.body", "body": body})

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        declared = dict(scope["headers"]).get(b"content-length")
        if declared and declared.isdigit() and int(declared) > self.max_bytes:
            return await self._send_413(send)

        received = 0

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _TooLarge()
            return message

        try:
            await self.app(scope, limited_receive, send)
        except _TooLarge:
            await self._send_413(send)


async def security_middleware(request: Request, call_next):
    """Origen → ritmo de la API → respuesta con cabeceras seguras."""
    if is_cross_origin(request):
        response = reject(403, "Origen no permitido.")
    elif request.url.path.startswith("/api/") and not api_limiter.allow(get_visitor_id(request)):
        response = reject(429, "Demasiadas peticiones. Espera un momento.")
    else:
        response = await call_next(request)
    add_security_headers(request, response)
    return response
