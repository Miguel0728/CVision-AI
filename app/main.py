import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.config.settings import ALLOWED_HOSTS, ENABLE_DOCS, MAX_BODY_BYTES
from app.core.security import BodyLimitMiddleware, security_middleware
from app.routes.chat import router as chat_router
from app.routes.emails import router as emails_router
from app.routes.usage import router as usage_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

BASE_DIR = Path(__file__).resolve().parent

# La documentación interactiva expone toda la API: solo se publica si se pide expresamente.
docs = {} if ENABLE_DOCS else {"docs_url": None, "redoc_url": None, "openapi_url": None}

app = FastAPI(
    title="CVision - Agente de Solicitudes de Empleo",
    version="1.0.0",
    description="Plataforma de visualización y evaluación de candidatos con IA",
    **docs,
)

# El último en añadirse es el primero en ejecutarse: host → tamaño del cuerpo → origen/ritmo/cabeceras.
app.middleware("http")(security_middleware)
app.add_middleware(BodyLimitMiddleware, max_bytes=MAX_BODY_BYTES)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.include_router(chat_router)
app.include_router(emails_router)
app.include_router(usage_router)


@app.exception_handler(RequestValidationError)
async def invalid_request(_: Request, __: RequestValidationError):
    """Respuesta genérica: no se devuelve el detalle (ni el contenido enviado) de la validación."""
    return JSONResponse({"detail": "Petición no válida."}, status_code=422)


@app.get("/", include_in_schema=False)
def serve_home():
    html_path = BASE_DIR / "templates" / "index.html"
    return FileResponse(html_path)
