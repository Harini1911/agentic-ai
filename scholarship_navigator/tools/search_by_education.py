from typing import List, Dict
from tools.scholarship_repository import load_scholarships

def search_by_education(education_level: str) -> List[Dict[str, str]]:
    """
    Search for scholarships applicable to a specific education level.

    Args:
        education_level: The student's current education level (e.g. 'Class 12').

    Returns:
        List of matching scholarships containing 'id' and 'name'.
    """
    scholarships = load_scholarships()
    results = []
    for s in scholarships:
        if s.get("education_level", "").strip().lower() == education_level.strip().lower():
            results.append({
                "id": s["id"],
                "name": s["name"]
            })
    return results
