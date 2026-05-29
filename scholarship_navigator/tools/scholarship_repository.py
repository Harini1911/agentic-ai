import os
import json
import contextvars
from typing import List, Dict, Any

# ContextVar to maintain active source safely during async execution
active_source_var = contextvars.ContextVar("active_source", default="nsp")

def set_active_source(source: str):
    """Set the active source for the current async execution context."""
    active_source_var.set(source)

def load_scholarships() -> List[Dict[str, Any]]:
    """
    Load scholarships dynamically from the active source JSON file.
    Uses ContextVar to ensure thread/async task safety during concurrent runs.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    source = active_source_var.get()
    filename = f"{source}_scholarships.json"
    dataset_path = os.path.join(current_dir, "..", "data", filename)
    
    if not os.path.exists(dataset_path):
        dataset_path = os.path.abspath(os.path.join("data", filename))
        
    try:
        with open(dataset_path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading scholarships dataset from {dataset_path}: {e}")
        return []
