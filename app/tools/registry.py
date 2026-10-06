"""Registro de herramientas (function calling).

Para añadir una herramienta: crea o edita un módulo en app/tools/ y decora la
función con @tool(...). El modelo la verá automáticamente y el chat mostrará
su paso en el streaming.
"""
import logging
from typing import Any, Callable, Dict, List, Optional

from app.tools.validation import validate_arguments

logger = logging.getLogger("cvision.tools")

_REGISTRY: Dict[str, Dict[str, Any]] = {}


def tool(name: str, description: str, parameters: Dict[str, Any], label: str, card: Optional[str] = None):
    """label: texto en español para mostrar al usuario mientras se ejecuta.
    card: tipo de tarjeta visual con la que la interfaz muestra el resultado (opcional)."""
    def decorator(fn: Callable[..., Any]):
        _REGISTRY[name] = {
            "fn": fn,
            "label": label,
            "card": card,
            "schema": {
                "type": "function",
                "function": {"name": name, "description": description, "parameters": parameters},
            },
        }
        return fn
    return decorator


def get_tool_schemas() -> List[Dict[str, Any]]:
    return [t["schema"] for t in _REGISTRY.values()]


def get_tool_label(name: str) -> str:
    return _REGISTRY[name]["label"] if name in _REGISTRY else name


def get_tool_card(name: str) -> Optional[str]:
    return _REGISTRY[name]["card"] if name in _REGISTRY else None


def run_tool(name: str, arguments: Any) -> Any:
    entry = _REGISTRY.get(name)
    if entry is None:
        return {"error": "Herramienta desconocida"}
    error = validate_arguments(entry["schema"]["function"]["parameters"], arguments)
    if error:
        return {"error": error}
    try:
        return entry["fn"](**arguments)
    except Exception:
        logger.exception("tool_error name=%s", name)  # el detalle queda en el log, no en la respuesta
        return {"error": "No se pudo completar la herramienta"}
