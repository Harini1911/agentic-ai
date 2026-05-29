from typing import Dict, Any, Optional
from tools.scholarship_repository import load_scholarships

def get_scholarship_details(scholarship_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve the full details of a specific scholarship by its unique ID.

    Args:
        scholarship_id: The unique identifier of the scholarship (e.g. 'SCH001').

    Returns:
        A dictionary containing the name, amount, and state of the scholarship if found, otherwise None.
    """
    scholarships = load_scholarships()
    for s in scholarships:
        if s["id"] == scholarship_id:
            return {
                "name": s["name"],
                "amount": s["amount"],
                "state": s["state"]
            }
    return None
