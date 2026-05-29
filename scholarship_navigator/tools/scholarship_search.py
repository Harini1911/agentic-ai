import os
import json
from typing import List, Dict, Any

def search_scholarships(education_level: str, annual_income: float, marks_percentage: float) -> List[Dict[str, Any]]:
    """
    Search for eligible scholarships from the local dataset based on student profile.

    Args:
        education_level: The student's education level (e.g. 'Class 12', 'Graduate').
        annual_income: The student's family annual income in INR (e.g. 250000).
        marks_percentage: The student's marks percentage out of 100 (e.g. 92).

    Returns:
        A list of matching scholarships with name, amount, and eligibility reason.
    """
    # Resolve file path relative to this file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, "..", "data", "scholarships.json")
    
    if not os.path.exists(dataset_path):
        # Fallback to local data folder if file relative path fails
        dataset_path = os.path.abspath(os.path.join("data", "scholarships.json"))
        
    try:
        with open(dataset_path, "r") as f:
            scholarships = json.load(f)
    except Exception as e:
        print(f"Error loading scholarship dataset from {dataset_path}: {e}")
        return []
        
    eligible = []
    for s in scholarships:
        # Check education level (case-insensitive)
        if s.get("education_level", "").strip().lower() != education_level.strip().lower():
            continue
        
        # Check max income
        if annual_income > s.get("max_income", float('inf')):
            continue
            
        # Check min marks
        if marks_percentage < s.get("min_marks", 0):
            continue
            
        # If all criteria are met
        eligible.append({
            "name": s["name"],
            "amount": s["amount"],
            "reason": "Marks and income criteria satisfied"
        })
        
    return eligible
