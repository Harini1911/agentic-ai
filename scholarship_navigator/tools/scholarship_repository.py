import os
import json
from typing import List, Dict, Any

def load_scholarships() -> List[Dict[str, Any]]:
    """
    Load all scholarships from the local data/scholarships.json file.

    Returns:
        List of all scholarships.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, "..", "data", "scholarships.json")
    
    if not os.path.exists(dataset_path):
        dataset_path = os.path.abspath(os.path.join("data", "scholarships.json"))
        
    try:
        with open(dataset_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading scholarships dataset from {dataset_path}: {e}")
        return []
