"""Redacta correos de convocatoria a entrevista a partir de una plantilla.

Usa solo datos laborales: el candidato, la vacante y los horarios propuestos.
"""
from datetime import date
from typing import Any, Dict, List, Optional

from app.core.guard import sanitize, strip_urls
from app.services.dates import format_slot, next_business_days

COMPANY = "CVision (demostración)"
MAX_SLOTS = 5
MAX_NOTE_LENGTH = 300


def default_slots(today: date) -> List[str]:
    first, second, third = next_business_days(today, 3)
    return [format_slot(first, 10), format_slot(second, 14), format_slot(third, 10)]


def parse_slot(slot: Any, today: date) -> Optional[str]:
    """Convierte {date, hour, minute?} en texto; ignora fechas inválidas o pasadas."""
    try:
        day = date.fromisoformat(str(slot["date"]))
        hour, minute = int(slot["hour"]), int(slot.get("minute", 0))
    except (KeyError, TypeError, ValueError, AttributeError):
        return None
    valid = day >= today and 0 <= hour <= 23 and 0 <= minute <= 59
    return format_slot(day, hour, minute) if valid else None


def parse_slots(slots: Optional[List[Any]], today: date) -> List[str]:
    parsed = [text for text in (parse_slot(slot, today) for slot in slots or []) if text]
    return parsed[:MAX_SLOTS]


def interview_format(candidate: Dict[str, Any]) -> str:
    remote = "remoto" in candidate.get("modality", "").lower()
    return "por videollamada" if remote else "presencial en nuestras oficinas"


def build_body(candidate: Dict[str, Any], job: Dict[str, Any], slots: List[str], note: str) -> str:
    first_name = candidate["name"].split()[0]
    options = "\n".join(f"- {slot}" for slot in slots)
    parts = [
        f"Hola {first_name},",
        f"Gracias por tu interés en la vacante de {job['title']}. Revisamos tu perfil y nos gustaría "
        f"invitarte a una entrevista {interview_format(candidate)}.",
        f"Estas son las opciones disponibles:\n{options}",
        "Responde a este correo con el horario que prefieras y te enviaremos la confirmación con los detalles.",
    ]
    if note:
        parts.append(note)
    parts.append(f"Saludos cordiales,\nEquipo de Talento\n{COMPANY}")
    return "\n\n".join(parts)


def compose_interview_email(
    candidate: Dict[str, Any], job: Dict[str, Any], slots: Optional[List[Any]] = None, note: str = ""
) -> Dict[str, str]:
    today = date.today()
    options = parse_slots(slots, today) or default_slots(today)
    return {
        "subject": f"Invitación a entrevista — {job['title']}",
        "body": build_body(candidate, job, options, strip_urls(sanitize(note))[:MAX_NOTE_LENGTH]),
    }
