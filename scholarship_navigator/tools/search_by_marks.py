from typing import List, Dict
from tools.scholarship_repository import load_scholarships

def search_by_marks(marks_percentage: float) -> List[Dict[str, str]]:
    """
    Search for scholarships where the student's marks percentage meets or exceeds the minimum required.

    Args:
        marks_percentage: The student's academic marks percentage (e.g. 92).

    Returns:
        List of matching scholarships containing 'id'.
    """
    scholarships = load_scholarships()
    results = []
    for s in scholarships:
        if marks_percentage >= s.get("min_marks", 0):
            results.append({
                "id": s["id"]
            })
    return results
