"""Límites de uso para la demostración pública.

- Presupuesto diario global de tokens: tope duro del gasto total (se reinicia a las 00:00 UTC).
- Preguntas por visitante y hora: evita que una sola persona agote el presupuesto.

El estado se guarda en un almacén persistente (ver app/database/usage_store.py), así que
sobrevive a reinicios del servidor. Como respaldo final, configura además un límite de
gasto mensual en el panel de OpenAI.
"""
import time
from datetime import datetime, timezone
from typing import Dict

from fastapi import HTTPException

from app.config.settings import DEMO_DAILY_TOKEN_BUDGET, DEMO_REQUESTS_PER_HOUR, USAGE_DB_PATH
from app.database.usage_store import SqliteUsageStore

WINDOW_SECONDS = 3600


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _budget_error() -> HTTPException:
    return HTTPException(status_code=429, detail="La demostración alcanzó su límite de uso diario. Vuelve mañana.")


def _rate_error(limit: int, oldest_hit: float, now: float) -> HTTPException:
    wait_seconds = int(WINDOW_SECONDS - (now - oldest_hit)) + 1
    detail = (
        f"Alcanzaste el límite de {limit} preguntas por hora en esta demostración. "
        f"Inténtalo de nuevo en unos {(wait_seconds + 59) // 60} min."
    )
    return HTTPException(status_code=429, detail=detail, headers={"Retry-After": str(wait_seconds)})


class UsageLimiter:
    def __init__(self, requests_per_hour: int, daily_token_budget: int, store: SqliteUsageStore):
        self.requests_per_hour = requests_per_hour
        self.daily_token_budget = daily_token_budget
        self._store = store

    def check(self, visitor: str) -> None:
        """Lanza HTTP 429 si el visitante o la demostración superaron su límite."""
        if self._store.get_tokens(_today()) >= self.daily_token_budget:
            raise _budget_error()

        now = time.time()
        allowed, hits = self._store.try_add_hit(visitor, now, WINDOW_SECONDS, self.requests_per_hour)
        if not allowed:
            raise _rate_error(self.requests_per_hour, hits[0], now)

    def status(self, visitor: str) -> Dict[str, int]:
        """Uso actual del visitante y de la demostración, sin consumir ninguna cuota."""
        recent = self._store.recent_hits(visitor, time.time() - WINDOW_SECONDS)
        return {
            "requests_used": len(recent),
            "requests_limit": self.requests_per_hour,
            "tokens_used": self._store.get_tokens(_today()),
            "tokens_budget": self.daily_token_budget,
        }

    def record(self, tokens: int) -> None:
        """Suma los tokens consumidos al presupuesto diario."""
        self._store.add_tokens(_today(), max(0, int(tokens)))


limiter = UsageLimiter(DEMO_REQUESTS_PER_HOUR, DEMO_DAILY_TOKEN_BUDGET, SqliteUsageStore(USAGE_DB_PATH))
