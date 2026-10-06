"""Herramientas sobre vacantes y la clasificación de candidatos por requisitos."""
from app.database.repository import get_all_applications, get_all_jobs
from app.services.lookup import find_job
from app.services.matching import evaluate_all, summarize_requirements
from app.tools.registry import tool


@tool(
    name="list_jobs",
    description="Lista las vacantes abiertas con su id, título, departamento y requisitos principales.",
    parameters={"type": "object", "properties": {}},
    label="Consultando las vacantes abiertas",
    card="jobs_list",
)
def list_jobs():
    return [
        {
            "id": job["id"],
            "title": job["title"],
            "department": job["department"],
            "requirements": summarize_requirements(job),
        }
        for job in get_all_jobs()
    ]


@tool(
    name="get_job",
    description="Obtiene el detalle completo de una vacante por su título: descripción, requisitos obligatorios y deseables.",
    parameters={
        "type": "object",
        "properties": {"job_title": {"type": "string", "description": "Título de la vacante; basta una parte, como 'DevOps'"}},
        "required": ["job_title"],
    },
    label="Revisando los requisitos de la vacante",
)
def get_job(job_title: str):
    job, error = find_job(job_title)
    return {"error": error} if error else job


@tool(
    name="match_candidates_to_job",
    description=(
        "Clasifica a TODOS los candidatos frente a una vacante: cumple, cumple parcialmente o no cumple, "
        "con el detalle requisito por requisito. La interfaz ya muestra el resultado en una tarjeta."
    ),
    parameters={
        "type": "object",
        "properties": {"job_title": {"type": "string", "description": "Título de la vacante; basta una parte, como 'DevOps'"}},
        "required": ["job_title"],
    },
    label="Comparando candidatos con los requisitos",
    card="job_match",
)
def match_candidates_to_job(job_title: str):
    job, error = find_job(job_title)
    return {"error": error} if error else evaluate_all(job, get_all_applications())
