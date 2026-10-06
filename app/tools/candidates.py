"""Herramientas sobre candidatos y solicitudes de empleo."""
from app.database.repository import (
    get_all_applications,
    get_application_by_id,
    filter_applications,
)
from app.tools.registry import tool


@tool(
    name="list_candidates",
    description="Lista todos los candidatos con id, nombre, puesto, departamento, modalidad, años de experiencia, estado y fecha de postulación.",
    parameters={"type": "object", "properties": {}},
    label="Consultando la lista de candidatos",
)
def list_candidates():
    fields = ("id", "name", "position", "department", "modality", "experience_years", "status", "applied_date")
    return [
        {k: a.get(k) for k in fields if k in a}
        for a in get_all_applications()
    ]


@tool(
    name="get_candidate",
    description="Obtiene el perfil corporativo completo de un candidato por su id (contacto, educación, habilidades, certificaciones, empresas anteriores, expectativa salarial, resumen).",
    parameters={
        "type": "object",
        "properties": {"candidate_id": {"type": "integer", "description": "ID del candidato"}},
        "required": ["candidate_id"],
    },
    label="Revisando el perfil del candidato",
)
def get_candidate(candidate_id: int):
    return get_application_by_id(candidate_id) or {"error": "Candidato no encontrado"}


@tool(
    name="search_candidates",
    description="Busca candidatos filtrando por habilidad técnica, departamento y/o años mínimos de experiencia.",
    parameters={
        "type": "object",
        "properties": {
            "skill": {"type": "string", "description": "Habilidad a buscar, ej. Docker, Python, Figma"},
            "department": {"type": "string", "description": "Departamento, ej. Ingeniería de Software, Datos & Inteligencia de Negocios"},
            "min_experience": {"type": "integer", "description": "Años mínimos de experiencia"},
        },
    },
    label="Buscando candidatos",
)
def search_candidates(skill: str = "", department: str = "", min_experience: int = 0):
    return filter_applications(skill=skill, department=department, min_experience=min_experience)
