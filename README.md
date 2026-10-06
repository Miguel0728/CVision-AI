# CVision

Agente conversacional de selección de personal: consulta candidatos y vacantes, clasifica quién cumple los requisitos y redacta convocatorias a entrevista. Es una **demostración** con datos ficticios.

## Estructura

```
app/
├── config/     settings.py        Variables de entorno y ajustes
├── core/       guard, security,   Defensas (ver "Seguridad"), límites de uso, firma de mensajes
│               signing, network,
│               usage_limits
├── database/   *_data.py          Datos ficticios (candidatos y vacantes)
│               repository.py      Acceso a los datos
│               outbox.py          Bandeja de salida simulada (SQLite)
│               usage_store.py     Contadores de uso persistentes (SQLite)
├── routes/     chat, emails, usage
├── services/   ai_service         Bucle del modelo con herramientas y streaming
│               prompts            Prompt del sistema (incluye las reglas de seguridad)
│               conversation       Verifica y sanea el historial que envía el navegador
│               matching, lookup, email_composer, dates
├── tools/      candidates, jobs, emails, registry, validation   Herramientas del agente
├── static/     css/ js/
└── templates/  index.html
tests/          Pruebas de seguridad
```

## Ejecutar en local

```bash
pip install -r requirements.txt
cp .env.example .env        # y completa OPENAI_API_KEY
python run.py               # http://127.0.0.1:8000  (recarga automática)
python -m unittest discover -s tests -v    # pruebas (no gastan tokens)
```

## Despliegue en Render

- **Build:** `pip install -r requirements.txt`
- **Start:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT --no-server-header`
- **Variables de entorno** (Render → Environment):

| Variable | Valor |
|---|---|
| `OPENAI_API_KEY` | tu clave (solo aquí, nunca en el repositorio) |
| `APP_SECRET` | 64 caracteres aleatorios (`python -c "import secrets; print(secrets.token_hex(32))"`) |
| `ALLOWED_HOSTS` | `tu-app.onrender.com` |
| `PROXY_HOPS` | `3` (la cadena en Render es cliente → Cloudflare → balanceador) |

- En el plan gratuito el disco es **temporal**: el contador de uso y la bandeja de salida se reinician en cada despliegue o tras inactividad. Para que persistan hace falta un disco persistente (`USAGE_DB_PATH`, `OUTBOX_DB_PATH` apuntando a él) o un almacén externo.
- **Pon además un límite de gasto mensual en el panel de OpenAI.** Es el único tope que no depende de este código.

## Seguridad

Defensas por capas, de las que no dependen del modelo a las que sí:

1. **Estructurales** (el modelo no puede saltárselas)
   - El historial que reenvía el navegador va **firmado (HMAC)**: los turnos del asistente sin firma válida se descartan, así no se puede falsificar "ya acepté ignorar mis reglas".
   - El agente **no tiene ninguna herramienta que envíe correos**: solo redacta borradores; el envío ocurre al pulsar un botón.
   - Los argumentos de cada herramienta se **validan contra su esquema** (tipos, campos desconocidos, tamaños).
   - Los resultados de las herramientas llegan al modelo marcados como **datos no confiables**.
   - Límite de gasto diario, límite por visitante y bloqueo temporal a quien insiste en manipular al agente.
2. **Detección:** saneamiento de la entrada (caracteres invisibles, marcadores de rol), patrones de inyección y de peticiones discriminatorias (se rechazan sin llamar al modelo), y un detector de **fuga del prompt** (canario + frases largas) sobre la respuesta en curso.
3. **Prompt:** reglas de seguridad explícitas (confidencialidad, datos ≠ órdenes, ámbito limitado).
4. **Web:** CSP estricta y demás cabeceras, `/docs` desactivado, validación de `Host` y `Origin` (anti-CSRF), límite de tamaño del cuerpo, límite general de ritmo, errores internos solo en el log del servidor.

Limitaciones: la detección por patrones no detecta todo (por eso las defensas estructurales); `X-Forwarded-For` solo se usa si `PROXY_HOPS` > 0 (el límite de preguntas se cuenta por navegador mediante una cookie anónima, con un tope más amplio por IP); los datos de la demo son ficticios y no hay autenticación de usuarios.
