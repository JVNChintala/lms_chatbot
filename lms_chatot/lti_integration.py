from fastapi import Request, HTTPException
from typing import Optional, Dict
import jwt
import requests

class CanvasLTI:
    """Handle Canvas LTI integration for embedded chatbot"""
    
    def __init__(self, canvas_url: str):
        self.canvas_url = canvas_url.rstrip('/').replace('/api/v1', '')
    
    def verify_lti_launch(self, request: Request) -> Dict:
        """Verify LTI launch request from Canvas"""
        # Canvas sends LTI parameters in POST request
        form_data = request.form
        
        user_id = form_data.get('custom_canvas_user_id')
        user_login = form_data.get('custom_canvas_user_login_id')
        roles = form_data.get('roles', '').lower()
        
        # Determine role from LTI roles
        role = 'student'
        if 'instructor' in roles or 'teacher' in roles:
            role = 'teacher'
        elif 'administrator' in roles:
            role = 'admin'
        
        return {
            'user_id': user_id,
            'user_login': user_login,
            'role': role
        }
    
    def get_user_from_session(self, canvas_session: str) -> Optional[Dict]:
        """Get user info from Canvas session cookie"""
        try:
            headers = {'Cookie': f'canvas_session={canvas_session}'}
            response = requests.get(f"{self.canvas_url}/api/v1/users/self", headers=headers)
            response.raise_for_status()
            return response.json()
        except:
            return None

def extract_user_from_canvas_context(request: Request) -> Optional[Dict]:
    """Extract user info from Canvas iframe/embed context"""
    # Canvas passes user info via query params or headers when embedding
    user_id = request.query_params.get('user_id')
    access_token = request.headers.get('X-Canvas-User-Token')
    
    if user_id and access_token:
        return {
            'canvas_user_id': int(user_id),
            'access_token': access_token
        }
    
    return None
