"""Clasificación determinista de candidatos contra los requisitos de una vacante.

Solo usa criterios laborales (experiencia, habilidades, idioma, modalidad). Nunca usa
nombre, ubicación ni otros datos personales para descartar a alguien.

Niveles:
- cumple:    cumple todos los requisitos obligatorios.
- parcial:   falla un único requisito y por poco (1 año, 1 habilidad o 1 nivel de inglés).
- no_cumple: cualquier otro caso.
"""
from collections import Counter
from typing import Any, Dict, List

ENGLISH_LEVELS = ["A1", "A2", "B1", "B2", "C1", "C2"]
LEVEL_ORDER = {"cumple": 0, "parcial": 1, "no_cumple": 2}

Job = Dict[str, Any]
Candidate = Dict[str, Any]


def _check(key: str, label: str, ok: bool, detail: str, near: bool = False) -> Dict[str, Any]:
    return {"key": key, "label": label, "ok": ok, "detail": detail, "near": near and not ok}


def check_experience(job: Job, candidate: Candidate) -> Dict[str, Any]:
    needed = job["required"]["min_experience"]
    have = candidate.get("experience_years", 0)
    return _check("experience", "Experiencia", have >= needed, f"{have} años (mín. {needed})", needed - have == 1)


def check_skills(job: Job, candidate: Candidate) -> Dict[str, Any]:
    owned = {skill.lower() for skill in candidate.get("skills", [])}
    missing = [s for s in job["required"]["skills"] if s.lower() not in owned]
    detail = "Todas" if not missing else "Falta: " + ", ".join(missing)
    return _check("skills", "Habilidades clave", not missing, detail, len(missing) == 1)


def _english_index(candidate: Candidate) -> int:
    code = candidate.get("english_level", "")[:2].upper()
    return ENGLISH_LEVELS.index(code) if code in ENGLISH_LEVELS else -1


def check_english(job: Job, candidate: Candidate) -> Dict[str, Any]:
    needed = job["required"]["english"]
    have, needed_index = _english_index(candidate), ENGLISH_LEVELS.index(needed)
    shown = ENGLISH_LEVELS[have] if have >= 0 else "N/D"
    return _check("english", "Inglés", have >= needed_index, f"{shown} (mín. {needed})", have == needed_index - 1)


def check_modality(job: Job, candidate: Candidate) -> Dict[str, Any]:
    modality = candidate.get("modality", "")
    accepted = job["modalities"]
    ok = any(option.lower() in modality.lower() for option in accepted)
    return _check("modality", "Modalidad", ok, f"{modality} (acepta {' / '.join(accepted)})")


def evaluate_nice_to_have(job: Job, candidate: Candidate) -> Dict[str, List[str]]:
    wanted = job["nice_to_have"]
    owned = {skill.lower() for skill in candidate.get("skills", [])}
    certs = " | ".join(candidate.get("certifications", [])).lower()
    matched = [s for s in wanted["skills"] if s.lower() in owned]
    matched += [c for c in wanted["certifications"] if c.lower() in certs]
    everything = wanted["skills"] + wanted["certifications"]
    return {"matched": matched, "missing": [item for item in everything if item not in matched]}


def classify(checks: List[Dict[str, Any]]) -> str:
    failed = [check for check in checks if not check["ok"]]
    if not failed:
        return "cumple"
    return "parcial" if len(failed) == 1 and failed[0]["near"] else "no_cumple"


def evaluate_candidate(job: Job, candidate: Candidate) -> Dict[str, Any]:
    checks = [
        check_experience(job, candidate),
        check_skills(job, candidate),
        check_english(job, candidate),
        check_modality(job, candidate),
    ]
    return {
        "id": candidate["id"],
        "name": candidate["name"],
        "position": candidate["position"],
        "level": classify(checks),
        "checks": checks,
        "nice": evaluate_nice_to_have(job, candidate),
    }


def _sort_key(result: Dict[str, Any]) -> tuple:
    return (LEVEL_ORDER[result["level"]], -len(result["nice"]["matched"]))


def summarize_requirements(job: Job) -> List[str]:
    required = job["required"]
    return [
        f"Mín. {required['min_experience']} años",
        ", ".join(required["skills"]),
        f"Inglés {required['english']}",
        " / ".join(job["modalities"]),
    ]


def evaluate_all(job: Job, candidates: List[Candidate]) -> Dict[str, Any]:
    results = sorted((evaluate_candidate(job, c) for c in candidates), key=_sort_key)
    counts = Counter(result["level"] for result in results)
    return {
        "job": {"id": job["id"], "title": job["title"], "requirements": summarize_requirements(job)},
        "counts": {level: counts.get(level, 0) for level in LEVEL_ORDER},
        "results": results,
    }
