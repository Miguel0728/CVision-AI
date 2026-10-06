"""Búsqueda de candidatos y vacantes por nombre, tolerante a acentos y mayúsculas.

El modelo conversa con nombres ("Diego", "DevOps"), no con IDs: este módulo los resuelve.
"""
import unicodedata
from typing import Any, Dict, List, Optional, Tuple

from app.database.repository import get_all_applications, get_all_jobs

Match = Tuple[Optional[Dict[str, Any]], Optional[str]]


def normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.strip().lower())
    return "".join(char for char in decomposed if unicodedata.category(char) != "Mn")


def _matches(items: List[Dict[str, Any]], key: str, query: str) -> List[Dict[str, Any]]:
    needle = normalize(query)
    exact = [item for item in items if normalize(item[key]) == needle]
    return exact or [item for item in items if needle and needle in normalize(item[key])]


def _resolve(items: List[Dict[str, Any]], key: str, query: str, label: str) -> Match:
    found = _matches(items, key, query)
    if len(found) == 1:
        return found[0], None
    if not found:
        return None, f"No hay {label} que coincidan con '{query}'"
    return None, f"Hay varias coincidencias para '{query}'; especifica una de: " + ", ".join(item[key] for item in found)


def find_candidate(query: str) -> Match:
    return _resolve(get_all_applications(), "name", query, "candidatos")


def find_job(query: str) -> Match:
    return _resolve(get_all_jobs(), "title", query, "vacantes")
