from fastapi import APIRouter, Request
from app.core.network import get_visitor_id
from app.core.usage_limits import limiter

router = APIRouter(prefix="/api/usage", tags=["Usage"])


@router.get("")
def usage(request: Request):
    return limiter.status(get_visitor_id(request))
