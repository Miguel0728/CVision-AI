"""Validación estricta de los argumentos que el modelo envía a las herramientas.

El modelo puede equivocarse o ser manipulado: se rechaza todo lo que no encaje con el esquema
(argumentos desconocidos, tipos erróneos, textos o listas desmesurados).
"""
from typing import Any, Dict, Optional

MAX_STRING_LENGTH = 300
MAX_LIST_ITEMS = 10
_TYPES = {"string": str, "integer": int, "array": list, "object": dict}


def _check_list(value: list, spec: Dict[str, Any], path: str) -> Optional[str]:
    if len(value) > MAX_LIST_ITEMS:
        return f"'{path}' tiene demasiados elementos"
    for index, item in enumerate(value):
        error = _check_value(item, spec.get("items", {}), f"{path}[{index}]")
        if error:
            return error
    return None


def _check_value(value: Any, spec: Dict[str, Any], path: str) -> Optional[str]:
    expected = _TYPES.get(spec.get("type"))
    if expected is None:
        return None
    if isinstance(value, bool) or not isinstance(value, expected):
        return f"'{path}' debe ser de tipo {spec['type']}"
    if isinstance(value, str) and len(value) > MAX_STRING_LENGTH:
        return f"'{path}' es demasiado largo"
    if isinstance(value, list):
        return _check_list(value, spec, path)
    if isinstance(value, dict) and "properties" in spec:
        return validate_arguments(spec, value, path)
    return None


def validate_arguments(schema: Dict[str, Any], arguments: Any, path: str = "argumentos") -> Optional[str]:
    """Devuelve un mensaje de error, o None si los argumentos son válidos."""
    if not isinstance(arguments, dict):
        return f"{path} debe ser un objeto"
    properties = schema.get("properties", {})
    unknown = sorted(set(arguments) - set(properties))
    if unknown:
        return f"Argumentos no permitidos: {', '.join(unknown)}"
    missing = [key for key in schema.get("required", []) if key not in arguments]
    if missing:
        return f"Faltan argumentos obligatorios: {', '.join(missing)}"
    for key, value in arguments.items():
        error = _check_value(value, properties[key], key)
        if error:
            return error
    return None
