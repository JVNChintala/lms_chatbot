from typing import Dict, Optional

class UserStore:
    """Store demo users created through Canvas API"""
    def __init__(self):
        self.users: Dict[str, dict] = {
            "admin": {"password": "admin123", "role": "admin", "canvas_user_id": None}
        }
    
    def add_user(self, login_id: str, password: str, role: str, canvas_user_id: int):
        self.users[login_id] = {
            "password": password,
            "role": role,
            "canvas_user_id": canvas_user_id
        }
    
    def authenticate(self, login_id: str, password: str) -> Optional[dict]:
        user = self.users.get(login_id)
        if user and user["password"] == password:
            return {
                "login_id": login_id, 
                "role": user["role"], 
                "canvas_user_id": user["canvas_user_id"]
            }
        return None
    
    def get_user(self, login_id: str) -> Optional[dict]:
        return self.users.get(login_id)

user_store = UserStore()
