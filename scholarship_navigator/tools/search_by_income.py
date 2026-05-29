from typing import List, Dict
from tools.scholarship_repository import load_scholarships

def search_by_income(annual_income: float) -> List[Dict[str, str]]:
    """
    Search for scholarships where the student's family annual income is within the allowed limit.

    Args:
        annual_income: The student's family annual income in INR (e.g. 250000).

    Returns:
        List of matching scholarships containing 'id'.
    """
    scholarships = load_scholarships()
    results = []
    for s in scholarships:
        if annual_income <= s.get("max_income", float('inf')):
            results.append({
                "id": s["id"]
            })
    return results
