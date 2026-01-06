import requests
import os
from typing import Dict
from dotenv import load_dotenv

load_dotenv()

class CanvasCourseDelete:
    def __init__(self, base_url: str = None, access_token: str = None):
        self.base_url = (base_url or os.getenv("CANVAS_URL")).rstrip('/').replace('/api/v1', '')
        self.headers = {"Authorization": f"Bearer {access_token or os.getenv('CANVAS_TOKEN')}"}
    
    def delete_course(self, course_id: int) -> Dict:
        """Delete a course (admin only)"""
        url = f"{self.base_url}/api/v1/courses/{course_id}"
        data = {"event": "delete"}
        response = requests.delete(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()

for i in [873, 900, 896, 860, 894, 885, 888, 889, 887, 874, 893, 880, 877, 833, 882, 884, 898, 899, 849]:
    CanvasCourseDelete().delete_course(course_id=i)