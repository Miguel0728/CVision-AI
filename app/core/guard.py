"""Defensas contra la manipulación del agente.

Ninguna defensa basada en patrones es infalible, por eso son una capa más:
  1. Estructural: el historial va firmado, las herramientas validan argumentos y el envío de
     correos solo ocurre con un clic del usuario (nada depende de que el modelo "obedezca").
  2. Esta capa: saneamiento, detección de intentos conocidos y de fugas del prompt.
  3. El prompt del sistema, que trata todo contenido externo como datos y no como órdenes.
"""
import re
import threading
import time
import unicodedata
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Pattern

INJECTION_REPLY = (
    "No puedo cambiar mis instrucciones ni revelar mi configuración interna. "
    "Sí puedo ayudarte con los candidatos, las vacantes y las convocatorias a entrevista: ¿qué necesitas?"
)
POLICY_REPLY = (
    "La selección se basa solo en criterios laborales: experiencia, habilidades, idioma y modalidad. "
    "No puedo filtrar ni descartar candidatos por género, edad, origen, religión, discapacidad u otras "
    "características personales. Si quieres, evalúo a los candidatos frente a los requisitos de una vacante."
)

_INVISIBLE = dict.fromkeys(map(ord, "​‌‍‎‏⁠⁦⁧⁨⁩﻿­"), None)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_MODEL_TOKENS = re.compile(r"<\|[^|>]{0,40}\|>|\[/?INST\]|<</?SYS>>")
_URL = re.compile(r"(?:https?://|www\.)\S+", re.IGNORECASE)


def sanitize(text: str) -> str:
    """Normaliza el texto y elimina caracteres invisibles, de control y marcadores de rol de modelos."""
    cleaned = unicodedata.normalize("NFKC", text).translate(_INVISIBLE)
    cleaned = _MODEL_TOKENS.sub("", _CONTROL.sub("", cleaned))
    return cleaned.strip()


def strip_urls(text: str) -> str:
    return _URL.sub("[enlace eliminado]", text)


def _fold(text: str) -> str:
    """Minúsculas y sin acentos, para comparar patrones."""
    decomposed = unicodedata.normalize("NFD", sanitize(text).lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


def _compile(patterns: List[str]) -> List[Pattern]:
    return [re.compile(p, re.IGNORECASE | re.DOTALL) for p in patterns]


_INJECTION = _compile([
    r"\b(ignor\w*|olvid\w*|omit\w*|salt\w*|forget|disregard|override|bypass|desactiv\w*)\b.{0,40}\b(instrucc\w*|regla\w*|indicacion\w*|directric\w*|restriccion\w*|instruction\w*|rules?|guidelines?|prompts?|restrictions?)\b",
    r"\b(revel\w*|muestr\w*|imprim\w*|repit\w*|dime|dame|copia\w*|escrib\w*|show|reveal|print|repeat|leak|output|display)\b.{0,50}\b(prompt|instrucciones|reglas|configuracion)\b.{0,30}\b(sistema|system|internas?|iniciales?|ocultas?|originales?|secret\w*)\b",
    r"\b(system|developer)\s*prompt\b",
    r"\b(prompt|instrucciones|reglas)\s+(del\s+)?(sistema|desarrollador)\b",
    r"\b(modo|mode)\s+(desarrollador|developer|dios|god|dan|jailbreak|sin\s+restricciones|sin\s+filtros)\b",
    r"\bjailbreak\b|\bdo\s+anything\s+now\b|\bdan\b.{0,30}\b(mode|modo)\b",
    r"\b(a\s+partir\s+de\s+ahora|from\s+now\s+on)\b.{0,60}\b(eres|seras|actua|ignora|you\s+are|act\s+as|ignore)\b",
    r"\b(nuevas?\s+instrucciones|new\s+instructions?|updated\s+instructions?)\s*:",
    r"\b(eres|actua|actúa|compórtate|comportate|pretend|act|you\s+are)\b.{0,40}\b(sin|without|no)\s+(restriccion\w*|filtros?|reglas|limites?|restrictions?|limits?|rules)\b",
    r"^\s*(system|assistant|developer|sistema|asistente)\s*:",
    r"<\s*/?\s*(system|assistant|instructions?)\s*>",
])

_PROTECTED = (
    r"(mujer\w*|hombres?|femenin\w*|masculin\w*|genero|sexo|embaraz\w*|jovenes?|viej\w*|personas\s+mayores|"
    r"edad|anos\s+de\s+edad|religi\w*|raza|etnia|origen|nacionalidad|extranjer\w*|discapacidad|orientacion\s+sexual|estado\s+civil|hijos)"
)
_SELECTION_VERB = r"(solo|solamente|descart\w*|excluy\w*|exclu\w*|elimin\w*|prefier\w*|prioriz\w*|filtr\w*|rechaz\w*|contrat\w*|evit\w*|only|exclude|reject|filter)"
_POLICY = _compile([
    rf"\b{_SELECTION_VERB}\b.{{0,60}}\b{_PROTECTED}\b",
    rf"\b{_PROTECTED}\b.{{0,60}}\b{_SELECTION_VERB}\b",
])


@dataclass(frozen=True)
class Verdict:
    allowed: bool
    category: Optional[str] = None
    reply: str = ""


ALLOWED = Verdict(True)


def inspect_message(text: str) -> Verdict:
    """Evalúa el último mensaje del usuario ANTES de llegar al modelo."""
    folded = _fold(text)
    if any(pattern.search(folded) for pattern in _INJECTION):
        return Verdict(False, "injection", INJECTION_REPLY)
    if any(pattern.search(folded) for pattern in _POLICY):
        return Verdict(False, "policy", POLICY_REPLY)
    return ALLOWED


class LeakDetector:
    """Detecta si la respuesta en curso reproduce el prompt del sistema (canario o frases largas)."""

    WINDOW_WORDS = 12

    def __init__(self, secret_prompt: str, canary: str):
        self._canary = canary.lower()
        self._shingles = self._shingles_of(_fold(secret_prompt))
        self._buffer = ""

    @classmethod
    def _shingles_of(cls, text: str) -> set:
        words = re.findall(r"\w+", text)
        return {" ".join(words[i:i + cls.WINDOW_WORDS]) for i in range(max(len(words) - cls.WINDOW_WORDS + 1, 0))}

    def feed(self, chunk: str) -> bool:
        """Añade texto y devuelve True si ya hay una fuga."""
        self._buffer = (self._buffer + chunk)[-1500:]
        folded = _fold(self._buffer)
        if self._canary in folded:
            return True
        return bool(self._shingles_of(folded) & self._shingles)


class StrikeTracker:
    """Bloquea temporalmente a quien insiste en intentos de manipulación."""

    def __init__(self, max_strikes: int = 3, window_seconds: int = 600, block_seconds: int = 900):
        self._max, self._window, self._block = max_strikes, window_seconds, block_seconds
        self._strikes: Dict[str, Deque[float]] = defaultdict(deque)
        self._blocked_until: Dict[str, float] = {}
        self._lock = threading.Lock()

    def record(self, visitor: str) -> None:
        now = time.time()
        with self._lock:
            strikes = self._strikes[visitor]
            strikes.append(now)
            while strikes and now - strikes[0] > self._window:
                strikes.popleft()
            if len(strikes) >= self._max:
                self._blocked_until[visitor] = now + self._block
                strikes.clear()

    def seconds_blocked(self, visitor: str) -> int:
        with self._lock:
            remaining = self._blocked_until.get(visitor, 0) - time.time()
            if remaining <= 0:
                self._blocked_until.pop(visitor, None)
                return 0
            return int(remaining) + 1


strikes = StrikeTracker()
