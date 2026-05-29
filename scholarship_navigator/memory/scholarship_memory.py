import json
from typing import Dict, Any, List

class SessionMemoryStore:
    """
    Session-based memory store for the Scholarship Navigator agent.
    Keeps track of student profile, recommendations, excluded categories/items,
    and conversation history for each unique session.
    """
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """Retrieves or initializes a session's memory state."""
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "student_profile": {},
                "recommended_scholarships": [],
                "excluded_scholarships": [],
                "conversation_history": [],
                "preferences": {}
            }
        return self.sessions[session_id]

    def update_profile(self, session_id: str, profile: Dict[str, Any]):
        """Updates the student profile in memory."""
        session = self.get_session(session_id)
        # Deep merge/update dictionary values
        for k, v in profile.items():
            if v is not None and str(v).strip() != "":
                session["student_profile"][k] = v

    def set_recommendations(self, session_id: str, scholarships: List[str]):
        """Saves current scholarship recommendations in memory."""
        session = self.get_session(session_id)
        session["recommended_scholarships"] = scholarships

    def add_excluded_scholarship(self, session_id: str, scholarship: str):
        """Adds a specific scholarship or category to exclusion list."""
        session = self.get_session(session_id)
        if scholarship not in session["excluded_scholarships"]:
            session["excluded_scholarships"].append(scholarship)

    def set_preference(self, session_id: str, key: str, value: Any):
        """Sets user preference context variables."""
        session = self.get_session(session_id)
        session["preferences"][key] = value

    def add_history(self, session_id: str, role: str, text: str):
        """Adds a message turn to conversation history."""
        session = self.get_session(session_id)
        session["conversation_history"].append({"role": role, "text": text})

    def clear_session(self, session_id: str):
        """Clears memory for a specific session."""
        if session_id in self.sessions:
            del self.sessions[session_id]

# Singleton memory store instance
memory_store = SessionMemoryStore()
