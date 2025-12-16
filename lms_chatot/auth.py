import requests
from typing import Optional, Dict
import jwt
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

class CanvasAuth:
    def __init__(self, canvas_url: str):
        self.canvas_url = canvas_url.rstrip('/').replace('/api/v1', '')
    
    def get_user_profile(self, access_token: str) -> Dict:
        """Get user profile from Canvas using access token"""
        url = f"{self.canvas_url}/api/v1/users/self"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    
    def get_user_roles(self, access_token: str) -> list:
        """Get user roles from Canvas"""
        url = f"{self.canvas_url}/api/v1/users/self/enrollments"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        enrollments = response.json()
        
        roles = set()
        for enrollment in enrollments:
            role_type = enrollment.get('type', '').lower()
            if 'teacher' in role_type or 'instructor' in role_type:
                roles.add('teacher')
            elif 'student' in role_type:
                roles.add('student')
            elif 'ta' in role_type:
                roles.add('teacher')
        
        return list(roles)
    
    def determine_primary_role(self, access_token: str) -> str:
        """Determine primary role (teacher takes precedence)"""
        roles = self.get_user_roles(access_token)
        if 'teacher' in roles:
            return 'teacher'
        elif 'student' in roles:
            return 'student'
        return 'student'
    
    def authenticate_user(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user with Canvas (OAuth flow simulation)"""
        # Canvas doesn't support direct username/password auth via API
        # This requires OAuth2 flow or access token
        # For demo: check if user exists and return mock token
        try:
            url = f"{self.canvas_url}/api/v1/users/self"
            # In real implementation, you'd use OAuth2 flow
            # For now, we'll use the admin token to verify user exists
            return None
        except:
            return None

def create_demo_token(user_id: str, role: str, secret_key: str = "demo_secret_key") -> str:
    """Create demo JWT token for testing"""
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

def verify_demo_token(token: str, secret_key: str = "demo_secret_key") -> Optional[Dict]:
    """Verify demo JWT token"""
    try:
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except:
        return None

def get_user_by_login(canvas_url: str, admin_token: str, login_id: str) -> Optional[Dict]:
    """Get user from Canvas by login ID using admin token"""
    try:
        # First check if login_id matches the token owner
        self_url = f"{canvas_url.rstrip('/').replace('/api/v1', '')}/api/v1/users/self"
        headers = {"Authorization": f"Bearer {admin_token}"}
        self_response = requests.get(self_url, headers=headers)
        if self_response.ok:
            self_user = self_response.json()
            if self_user.get('login_id') == login_id or self_user.get('email') == login_id:
                print(f"Found token owner: {self_user.get('name')}")
                return self_user
        
        # Search all users
        url = f"{canvas_url.rstrip('/').replace('/api/v1', '')}/api/v1/accounts/1/users"
        response = requests.get(url, headers=headers, params={"search_term": login_id})
        print(f"User search response: {response.status_code}")
        response.raise_for_status()
        users = response.json()
        print(f"Found {len(users)} users matching '{login_id}'")
        
        for user in users:
            user_login = user.get('login_id', '')
            user_email = user.get('email', '')
            print(f"Checking user: {user.get('name')} - login: {user_login}, email: {user_email}")
            if user_login == login_id or user_email == login_id or user.get('sis_user_id') == login_id:
                print(f"Match found: {user.get('name')}")
                return user
        
        print(f"No user found for login_id: {login_id}")
        return None
    except Exception as e:
        print(f"Error in get_user_by_login: {e}")
        import traceback
        traceback.print_exc()
        return None

def create_user_access_token(canvas_url: str, admin_token: str, user_id: int) -> Optional[str]:
    """Create an access token for a specific user (admin operation)"""
    try:
        # Canvas API: POST /api/v1/users/:user_id/tokens (as admin)
        url = f"{canvas_url.rstrip('/').replace('/api/v1', '')}/api/v1/users/{user_id}/tokens"
        headers = {"Authorization": f"Bearer {admin_token}"}
        data = {
            "access_token[purpose]": "LMS Chatbot Access",
            "access_token[expires_at]": "",  # Never expires
        }
        response = requests.post(url, headers=headers, data=data)
        print(f"Token creation response: {response.status_code}, {response.text[:200]}")
        response.raise_for_status()
        token_data = response.json()
        return token_data.get('token') or token_data.get('visible_token')
    except Exception as e:
        print(f"Failed to create user token: {e}")
        # If token creation fails, return admin token as fallback
        print(f"Using admin token as fallback for user {user_id}")
        return admin_token
