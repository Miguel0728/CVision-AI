from fastapi import APIRouter, HTTPException, Path
from app.core.signing import sign_message
from app.database.outbox import outbox, public_view

router = APIRouter(prefix="/api/emails", tags=["Emails"])


def _sent_notice(record: dict) -> dict:
    """Aviso que el chat añade al historial; va firmado para que el modelo pueda confiar en él."""
    content = f"Correo de convocatoria enviado a {record['to_name']} (simulado)."
    return {"content": content, "sig": sign_message(content)}


@router.post("/{email_id}/send")
def send_email(email_id: str = Path(pattern=r"^[0-9a-f]{32}$")):
    """Envío SIMULADO: marca el borrador como enviado. Solo lo invoca el botón de la tarjeta."""
    record = outbox.mark_sent(email_id)
    if not record:
        raise HTTPException(
            status_code=404,
            detail="Ese borrador ya no está disponible. Pídele al agente que genere uno nuevo.",
        )
    return {**public_view(record), "notice": _sent_notice(record)}
