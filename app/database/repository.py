from typing import List, Dict, Any, Optional
from app.database.jobs_data import MOCK_JOBS
from app.database.mock_data import MOCK_APPLICATIONS


def get_all_applications() -> List[Dict[str, Any]]:
    return MOCK_APPLICATIONS


def get_application_by_id(app_id: int) -> Optional[Dict[str, Any]]:
    return next((app for app in MOCK_APPLICATIONS if app.get("id") == app_id), None)


def filter_applications(
    skill: str = "",
    department: str = "",
    min_experience: int = 0
) -> List[Dict[str, Any]]:
    results = []
    for app in MOCK_APPLICATIONS:
        if skill and not any(skill.lower() in s.lower() for s in app.get("skills", [])):
            continue
        if department and department.lower() not in app.get("department", "").lower():
            continue
        if app.get("experience_years", 0) < min_experience:
            continue
        results.append(app)
    return results


def get_all_jobs() -> List[Dict[str, Any]]:
    return MOCK_JOBS
