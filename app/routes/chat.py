import hashlib
import json
import logging
from typing import List, Literal, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, model_validator

from app.core.guard import inspect_message, strikes
from app.core.network import get_visitor_id
from app.core.signing import sign_message
from app.core.usage_limits import limiter
from app.services.ai_service import chat_stream, static_reply_stream
from app.services.conversation import prepare_messages

router = APIRouter(prefix="/api/chat", tags=["Chat"])
logger = logging.getLogger("cvision.security")

MAX_USER_CHARS = 2000
MAX_ASSISTANT_CHARS = 8000
MAX_MESSAGES = 40


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=MAX_ASSISTANT_CHARS)
    sig: Optional[str] = Field(default=None, max_length=128)

    @model_validator(mode="after")
    def _limit_user_length(self):
        if self.role == "user" and len(self.content) > MAX_USER_CHARS:
            raise ValueError("Mensaje demasiado largo")
        return self


class ChatRequest(BaseModel):
    messages: List[ChatMessage] = Field(min_length=1, max_length=MAX_MESSAGES)


def _anonymous(visitor: str) -> str:
    return hashlib.sha256(visitor.encode("utf-8")).hexdigest()[:10]


def _sse(events):
    """Emite los eventos y firma la respuesta completa al terminar."""
    text = ""
    for event in events:
        if event["type"] == "token":
            text += event["text"]
        elif event["type"] == "done":
            event = {**event, "sig": sign_message(text)}
        yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


def _reject_if_blocked(visitor: str) -> None:
    wait = strikes.seconds_blocked(visitor)
    if wait:
        raise HTTPException(
            status_code=429,
            detail="Detectamos actividad sospechosa. Inténtalo de nuevo más tarde.",
            headers={"Retry-After": str(wait)},
        )


@router.post("")
def chat(request: ChatRequest, http_request: Request):
    visitor = get_visitor_id(http_request)
    _reject_if_blocked(visitor)
    limiter.check(visitor)

    messages = prepare_messages([m.model_dump() for m in request.messages])
    if not messages or messages[-1]["role"] != "user":
        raise HTTPException(status_code=400, detail="Mensaje no válido.")

    verdict = inspect_message(messages[-1]["content"])
    if verdict.allowed:
        events = chat_stream(messages)
    else:
        strikes.record(visitor)
        logger.warning("guard_blocked category=%s visitor=%s", verdict.category, _anonymous(visitor))
        events = static_reply_stream(verdict.reply)

    return StreamingResponse(
        _sse(events),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
