import os
import secrets
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_FILE = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_FILE)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gpt-5.6-luna")
# gpt-5.6-luna solo admite function calling en chat/completions con reasoning_effort="none"
AI_REASONING_EFFORT = os.getenv("AI_REASONING_EFFORT", "none")

# Límites de uso de la demostración (protegen el gasto de la cuenta de OpenAI)
DEMO_DAILY_TOKEN_BUDGET = int(os.getenv("DEMO_DAILY_TOKEN_BUDGET", "300000"))
DEMO_REQUESTS_PER_HOUR = int(os.getenv("DEMO_REQUESTS_PER_HOUR", "20"))
MAX_COMPLETION_TOKENS = int(os.getenv("MAX_COMPLETION_TOKENS", "700"))
# Archivo donde se guarda el uso para que sobreviva a reinicios (en Render: ruta de un disco persistente)
USAGE_DB_PATH = Path(os.getenv("USAGE_DB_PATH") or BASE_DIR / "app" / "database" / "usage.db")
# Bandeja de salida simulada (borradores y correos "enviados")
OUTBOX_DB_PATH = Path(os.getenv("OUTBOX_DB_PATH") or BASE_DIR / "app" / "database" / "outbox.db")

# ---------- Seguridad ----------
SECRET_FILE = BASE_DIR / "app" / "database" / ".app_secret"


def _load_app_secret() -> str:
    """Clave para firmar las respuestas del agente. En producción define APP_SECRET como variable de entorno."""
    from_env = os.getenv("APP_SECRET", "").strip()
    if len(from_env) >= 32:
        return from_env
    if not SECRET_FILE.exists():
        SECRET_FILE.parent.mkdir(parents=True, exist_ok=True)
        SECRET_FILE.write_text(secrets.token_hex(32), encoding="utf-8")
    return SECRET_FILE.read_text(encoding="utf-8").strip()


APP_SECRET = _load_app_secret()
# Hosts que la app acepta (separados por comas). En Render: tu-app.onrender.com
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]
# Cuántos proxies de confianza hay delante de la app (Render: 1). 0 = sin proxy; se ignora X-Forwarded-For.
PROXY_HOPS = int(os.getenv("PROXY_HOPS", "0"))
# La documentación interactiva (/docs) expone la API; solo se activa si se pide expresamente.
ENABLE_DOCS = os.getenv("ENABLE_DOCS", "false").lower() == "true"
MAX_BODY_BYTES = int(os.getenv("MAX_BODY_BYTES", "65536"))
API_REQUESTS_PER_MINUTE = int(os.getenv("API_REQUESTS_PER_MINUTE", "120"))
# Tope de preguntas por IP y hora (más amplio que el de cada navegador): frena a quien cambia de cookie para saltarse el límite.
IP_REQUESTS_PER_HOUR = int(os.getenv("IP_REQUESTS_PER_HOUR", "60"))
