from typing import Dict, Optional
import uuid

class SessionManager:
    def __init__(self):
        self.sessions: Dict[str, dict] = {}
    
    def create_session(self, user_role: Optional[str] = None, canvas_user_id: Optional[int] = None, user_token: Optional[str] = None, username: Optional[str] = None) -> str:
        session_id = str(uuid.uuid4())
        self.sessions[session_id] = {
            "role": user_role,
            "conversation_history": [],
            "canvas_user_id": canvas_user_id,
            "user_token": user_token,
            "username": username
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        return self.sessions.get(session_id)
    
    def update_session(self, session_id: str, role: str = None, history: list = None, canvas_user_id: int = None, user_token: str = None, username: str = None):
        if session_id in self.sessions:
            if role:
                self.sessions[session_id]["role"] = role
            if history is not None:
                self.sessions[session_id]["conversation_history"] = history
            if canvas_user_id:
                self.sessions[session_id]["canvas_user_id"] = canvas_user_id
            if user_token:
                self.sessions[session_id]["user_token"] = user_token
            if username:
                self.sessions[session_id]["username"] = username
    
    def set_role(self, session_id: str, role: str):
        if session_id in self.sessions:
            self.sessions[session_id]["role"] = role

session_manager = SessionManager()
