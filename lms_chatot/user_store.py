from typing import Dict, Optional

class UserStore:
    """Store demo users created through Canvas API"""
    def __init__(self):
        self.users: Dict[str, dict] = {
            "admin": {"password": "admin123", "role": "admin", "canvas_user_id": None, "canvas_token": None}
        }
    
    def add_user(self, login_id: str, password: str, role: str, canvas_user_id: int, canvas_token: str = None):
        self.users[login_id] = {
            "password": password,
            "role": role,
            "canvas_user_id": canvas_user_id,
            "canvas_token": canvas_token
        }
    
    def authenticate(self, login_id: str, password: str) -> Optional[dict]:
        user = self.users.get(login_id)
        if user and user["password"] == password:
            return {
                "login_id": login_id, 
                "role": user["role"], 
                "canvas_user_id": user["canvas_user_id"],
                "canvas_token": user.get("canvas_token")
            }
        return None
    
    def get_user(self, login_id: str) -> Optional[dict]:
        return self.users.get(login_id)

user_store = UserStore()
