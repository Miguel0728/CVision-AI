"""Vacantes ficticias de la demostración.

required: requisitos eliminatorios. nice_to_have: suman pero no descartan.
Las habilidades se comparan por nombre exacto; las certificaciones, por coincidencia parcial.
"""
from typing import Any, Dict, List

MOCK_JOBS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "Desarrollador Full Stack",
        "department": "Ingeniería de Software",
        "modalities": ["Híbrido", "Remoto"],
        "description": "Construirá APIs y aplicaciones web para la plataforma de clientes.",
        "required": {"min_experience": 4, "skills": ["Python", "JavaScript"], "english": "B2"},
        "nice_to_have": {"skills": ["Docker", "React", "PostgreSQL"], "certifications": ["AWS"]},
    },
    {
        "id": 2,
        "title": "Ingeniero DevOps / Cloud",
        "department": "Infraestructura & Operaciones",
        "modalities": ["Remoto", "Híbrido"],
        "description": "Automatizará despliegues y operará la infraestructura en la nube.",
        "required": {"min_experience": 4, "skills": ["Docker", "Kubernetes"], "english": "B2"},
        "nice_to_have": {"skills": ["Terraform", "CI/CD", "AWS"], "certifications": ["CKA"]},
    },
    {
        "id": 3,
        "title": "Ingeniero de Datos",
        "department": "Datos & Inteligencia de Negocios",
        "modalities": ["Remoto", "Híbrido"],
        "description": "Diseñará y mantendrá los pipelines que alimentan los tableros de la empresa.",
        "required": {"min_experience": 4, "skills": ["Python", "SQL"], "english": "B2"},
        "nice_to_have": {"skills": ["Apache Airflow", "dbt", "Snowflake"], "certifications": ["Snowflake"]},
    },
    {
        "id": 4,
        "title": "Ingeniero de Machine Learning",
        "department": "Datos & Inteligencia de Negocios",
        "modalities": ["Remoto", "Híbrido"],
        "description": "Llevará modelos de lenguaje y predicción desde el prototipo a producción.",
        "required": {"min_experience": 3, "skills": ["Python", "Scikit-Learn"], "english": "C1"},
        "nice_to_have": {"skills": ["PyTorch", "NLP", "MLflow"], "certifications": ["TensorFlow"]},
    },
    {
        "id": 5,
        "title": "Analista de Ciberseguridad",
        "department": "Seguridad de la Información",
        "modalities": ["Presencial", "Híbrido"],
        "description": "Monitoreará incidentes en el SOC y fortalecerá los controles de seguridad.",
        "required": {"min_experience": 3, "skills": ["SIEM", "ISO 27001"], "english": "B2"},
        "nice_to_have": {"skills": ["Splunk", "Wireshark"], "certifications": ["Security+"]},
    },
    {
        "id": 6,
        "title": "Product Owner",
        "department": "Diseño & Producto",
        "modalities": ["Híbrido", "Remoto"],
        "description": "Definirá la hoja de ruta del producto y priorizará el trabajo de los equipos.",
        "required": {"min_experience": 5, "skills": ["Scrum", "Product Roadmap"], "english": "C1"},
        "nice_to_have": {"skills": ["Jira", "SQL", "Análisis de Métricas"], "certifications": ["PMP"]},
    },
]
