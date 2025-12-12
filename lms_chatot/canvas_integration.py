import requests
from typing import List, Dict, Optional
from canvas_api_validator import CanvasAPIValidator

class CanvasLMS:
    def __init__(self, base_url: str, access_token: str, as_user_id: int = None):
        self.base_url = base_url.rstrip('/').replace('/api/v1', '')
        self.headers = {"Authorization": f"Bearer {access_token}"}
        self.as_user_id = as_user_id
        print(f"[CanvasLMS] Initialized with as_user_id={as_user_id}")
    
    def list_courses(self, account_id: Optional[int] = None) -> List[Dict]:
        """List all courses with pagination and error handling"""
        params = {"per_page": 100}
        
        if account_id:
            url = f"{self.base_url}/api/v1/accounts/{account_id}/courses"
            if self.as_user_id:
                params["as_user_id"] = self.as_user_id
        else:
            if self.as_user_id:
                url = f"{self.base_url}/api/v1/users/{self.as_user_id}/courses"
                params["include"] = ["total_scores", "current_grading_period_scores", "term"]
            else:
                url = f"{self.base_url}/api/v1/courses"
        
        courses = []
        
        try:
            while url:
                response = requests.get(url, headers=self.headers, params=params)
                result = CanvasAPIValidator.validate_response(response, "list_courses")
                
                if not result["success"]:
                    print(f"[CANVAS] Error: {result['error']}")
                    return []
                
                batch = result["data"]
                courses.extend(batch)
                
                url = response.links.get('next', {}).get('url')
                params = None
            
            return courses
            
        except Exception as e:
            print(f"[CANVAS] Exception in list_courses: {str(e)}")
            return []
    
    def get_course(self, course_id: int) -> Dict:
        """Get a specific course by ID"""
        url = f"{self.base_url}/api/v1/courses/{course_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def create_course(self, account_id: int, name: str, course_code: str, **kwargs) -> Dict:
        """Create a new course with error handling"""
        url = f"{self.base_url}/api/v1/accounts/{account_id}/courses"
        data = {
            "course[name]": name,
            "course[course_code]": course_code,
        }
        for key, value in kwargs.items():
            data[f"course[{key}]"] = value
            
        try:
            response = requests.post(url, headers=self.headers, data=data)
            result = CanvasAPIValidator.validate_response(response, "create_course")
            return CanvasAPIValidator.format_tool_response(result, "create_course")
        except Exception as e:
            return {"error": f"Failed to create course: {str(e)}"}
    
    def list_modules(self, course_id: int) -> List[Dict]:
        """List all modules in a course with error handling"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/modules"
        
        try:
            response = requests.get(url, headers=self.headers)
            result = CanvasAPIValidator.validate_response(response, "list_modules")
            
            if result["success"]:
                return result["data"]
            else:
                return [{"error": result["error"]}]
        except Exception as e:
            return [{"error": f"Failed to list modules: {str(e)}"}]
    
    def create_module(self, course_id: int, name: str, **kwargs) -> Dict:
        """Create a new module in a course"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/modules"
        data = {"module[name]": name}
        for key, value in kwargs.items():
            data[f"module[{key}]"] = value
        response = requests.post(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def upload_file(self, course_id: int, file_name: str) -> Dict:
        """Upload a file to a course"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/files"
        data = {"name": file_name}
        response = requests.post(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def list_account_courses(self, account_id: int = 1) -> List[Dict]:
        """List all courses in an account (admin access)"""
        url = f"{self.base_url}/api/v1/accounts/{account_id}/courses"
        courses = []
        params = {"per_page": 100}
        
        while url:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            courses.extend(response.json())
            url = response.links.get('next', {}).get('url')
            params = None
        
        return courses
    
    def create_user(self, account_id: int, name: str, email: str, login_id: str) -> Dict:
        """Create a new user (admin only)"""
        url = f"{self.base_url}/api/v1/accounts/{account_id}/users"
        data = {
            "user[name]": name,
            "pseudonym[unique_id]": login_id,
            "pseudonym[password]": "Welcome123!",
            "pseudonym[send_confirmation]": False,
            "communication_channel[type]": "email",
            "communication_channel[address]": email,
            "communication_channel[skip_confirmation]": True
        }
        try:
            response = requests.post(url, headers=self.headers, data=data)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            # If user already exists, search and return existing user
            if e.response.status_code == 400:
                users = self.list_users(account_id)
                for user in users:
                    if user.get('login_id') == login_id or user.get('email') == email:
                        return {**user, "already_exists": True}
            raise
    
    def enroll_user(self, course_id: int, user_id: int, role: str = "StudentEnrollment") -> Dict:
        """Enroll a user in a course"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/enrollments"
        data = {
            "enrollment[user_id]": user_id,
            "enrollment[type]": role,
            "enrollment[enrollment_state]": "active"
        }
        response = requests.post(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def list_users(self, account_id: int = 1) -> List[Dict]:
        """List all users in an account (admin only)"""
        url = f"{self.base_url}/api/v1/accounts/{account_id}/users"
        response = requests.get(url, headers=self.headers, params={"per_page": 100})
        response.raise_for_status()
        return response.json()
    
    def create_assignment(self, course_id: int, name: str, points: int = 100, description: str = None, **kwargs) -> Dict:
        """Create an assignment in a course"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/assignments"
        data = {
            "assignment[name]": name,
            "assignment[points_possible]": points,
            "assignment[published]": True
        }
        if description:
            data["assignment[description]"] = description
        for key, value in kwargs.items():
            data[f"assignment[{key}]"] = value
        response = requests.post(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def create_page(self, course_id: int, title: str, body: str) -> Dict:
        """Create a page in a course"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/pages"
        data = {
            "wiki_page[title]": title,
            "wiki_page[body]": body,
            "wiki_page[published]": True
        }
        response = requests.post(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def publish_course(self, course_id: int) -> Dict:
        """Publish a course"""
        url = f"{self.base_url}/api/v1/courses/{course_id}"
        data = {"course[event]": "offer"}
        response = requests.put(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def add_module_item(self, course_id: int, module_id: int, item_type: str, content_id: int, title: str) -> Dict:
        """Add an item to a module"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/modules/{module_id}/items"
        data = {
            "module_item[type]": item_type,
            "module_item[content_id]": content_id,
            "module_item[title]": title
        }
        response = requests.post(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def create_discussion(self, course_id: int, title: str, message: str) -> Dict:
        """Create a discussion topic"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/discussion_topics"
        data = {
            "title": title,
            "message": message,
            "discussion_type": "threaded",
            "published": True
        }
        response = requests.post(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def create_announcement(self, course_id: int, title: str, message: str) -> Dict:
        """Create an announcement"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/discussion_topics"
        data = {
            "title": title,
            "message": message,
            "is_announcement": True,
            "published": True
        }
        response = requests.post(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def update_course_settings(self, course_id: int, **settings) -> Dict:
        """Update course settings (syllabus, grading scheme, etc.)"""
        url = f"{self.base_url}/api/v1/courses/{course_id}"
        data = {}
        for key, value in settings.items():
            data[f"course[{key}]"] = value
        response = requests.put(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def publish_module(self, course_id: int, module_id: int) -> Dict:
        """Publish a module"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/modules/{module_id}"
        data = {"module[published]": True}
        response = requests.put(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def search_users(self, account_id: int, search_term: str) -> List[Dict]:
        """Search for users by name or email"""
        url = f"{self.base_url}/api/v1/accounts/{account_id}/users"
        response = requests.get(url, headers=self.headers, params={"search_term": search_term})
        response.raise_for_status()
        return response.json()
