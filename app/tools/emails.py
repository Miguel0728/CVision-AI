"""Herramientas de correo. El agente solo REDACTA borradores; el envío lo hace el usuario con un botón."""
from typing import List, Optional

from app.database.outbox import outbox, public_view
from app.services.email_composer import compose_interview_email
from app.services.lookup import find_candidate, find_job
from app.tools.registry import tool


@tool(
    name="draft_interview_email",
    description=(
        "Redacta el BORRADOR de un correo que convoca a un candidato a entrevista para una vacante. "
        "No envía nada: la interfaz muestra el borrador y el usuario decide si lo envía. "
        "Úsala solo después de que el usuario confirme que quiere convocar a esa persona. "
        "Si el usuario pide cambios (otros horarios, una nota), llámala de nuevo con 'slots' o 'note'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "candidate_name": {"type": "string", "description": "Nombre del candidato a convocar, p. ej. 'Diego Fernández'"},
            "job_title": {"type": "string", "description": "Título de la vacante, p. ej. 'Ingeniero DevOps / Cloud' (basta una parte, como 'DevOps')"},
            "slots": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "date": {"type": "string", "description": "Fecha en formato AAAA-MM-DD"},
                        "hour": {"type": "integer", "description": "Hora en formato 24 h (0-23)"},
                        "minute": {"type": "integer", "description": "Minutos (0-59). Opcional."},
                    },
                    "required": ["date", "hour"],
                },
                "description": "Horarios propuestos. Úsalo SOLO si el usuario pidió horarios concretos; si no, omítelo y se proponen automáticamente.",
            },
            "note": {"type": "string", "description": "Nota adicional para el candidato. Opcional."},
        },
        "required": ["candidate_name", "job_title"],
    },
    label="Redactando el correo de convocatoria",
    card="email_draft",
)
def draft_interview_email(candidate_name: str, job_title: str, slots: Optional[List[dict]] = None, note: str = ""):
    candidate, error = find_candidate(candidate_name)
    if error:
        return {"error": error}
    job, error = find_job(job_title)
    if error:
        return {"error": error}

    content = compose_interview_email(candidate, job, slots, note)
    record = outbox.save_draft({
        "candidate_id": candidate["id"],
        "job_id": job["id"],
        "to_name": candidate["name"],
        "to_email": candidate["email"],
        **content,
    })
    return {**public_view(record), "job_title": job["title"]}
