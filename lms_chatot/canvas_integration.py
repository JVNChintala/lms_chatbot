import requests
from typing import List, Dict, Optional

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
                response.raise_for_status()
                courses.extend(response.json())
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
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": f"Failed to create course: {str(e)}"}
    
    def list_modules(self, course_id: int) -> List[Dict]:
        """List all modules in a course with error handling"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/modules"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
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
    
    def create_assignment(self, course_id: int, assignment_data: Dict) -> Dict:
        """Create an assignment in a course"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/assignments"
        data = {}
        for key, value in assignment_data.items():
            data[f"assignment[{key}]"] = value
        if "published" not in assignment_data:
            data["assignment[published]"] = True
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
    
    def list_quizzes(self, course_id: int) -> List[Dict]:
        """List all quizzes in a course"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/quizzes"
        response = requests.get(url, headers=self.headers, params={"per_page": 100})
        response.raise_for_status()
        return response.json()
    
    def list_module_items(self, course_id: int, module_id: int) -> List[Dict]:
        """List all items in a module"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/modules/{module_id}/items"
        response = requests.get(url, headers=self.headers, params={"per_page": 100})
        response.raise_for_status()
        return response.json()
    
    def list_pages(self, course_id: int) -> List[Dict]:
        """List all pages in a course"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/pages"
        response = requests.get(url, headers=self.headers, params={"per_page": 100})
        response.raise_for_status()
        return response.json()
    
    def create_quiz(self, course_id: int, title: str, description: str = "", quiz_type: str = "assignment") -> Dict:
        """Create a quiz in a course"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/quizzes"
        data = {
            "quiz[title]": title,
            "quiz[description]": description,
            "quiz[quiz_type]": quiz_type,
            "quiz[published]": True
        }
        response = requests.post(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def create_quiz_question(self, course_id: int, quiz_id: int, question_name: str, question_text: str, question_type: str = "multiple_choice_question", points_possible: int = 1, answers: List[Dict] = None) -> Dict:
        """Create a question in a quiz"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/quizzes/{quiz_id}/questions"
        data = {
            "question[question_name]": question_name,
            "question[question_text]": question_text,
            "question[question_type]": question_type,
            "question[points_possible]": points_possible
        }
        if answers:
            for i, answer in enumerate(answers):
                data[f"question[answers][{i}][answer_text]"] = answer.get("text", "")
                data[f"question[answers][{i}][answer_weight]"] = answer.get("weight", 0)
        response = requests.post(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def update_course(self, course_id: int, updates: Dict) -> Dict:
        """Update course details"""
        url = f"{self.base_url}/api/v1/courses/{course_id}"
        data = {f"course[{k}]": v for k, v in updates.items()}
        response = requests.put(url, headers=self.headers, data=data)
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
    
    def list_assignments(self, course_id: int) -> List[Dict]:
        """List all assignments in a course"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/assignments"
        response = requests.get(url, headers=self.headers, params={"per_page": 100})
        response.raise_for_status()
        return response.json()
    
    def get_assignment(self, course_id: int, assignment_id: int) -> Dict:
        """Get a specific assignment"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def grade_assignment(self, course_id: int, assignment_id: int, user_id: int, grade: float, comment: str = None) -> Dict:
        """Grade a student's assignment submission"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}"
        data = {
            "submission[posted_grade]": grade
        }
        if comment:
            data["comment[text_comment]"] = comment
        response = requests.put(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def submit_assignment(self, course_id: int, assignment_id: int, submission_type: str, body: str = None, url: str = None) -> Dict:
        """Submit an assignment"""
        api_url = f"{self.base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions"
        data = {
            "submission[submission_type]": submission_type
        }
        if body:
            data["submission[body]"] = body
        if url:
            data["submission[url]"] = url
        response = requests.post(api_url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
    
    def list_enrollments(self, course_id: int) -> List[Dict]:
        """List all enrollments in a course"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/enrollments"
        response = requests.get(url, headers=self.headers, params={"per_page": 100})
        response.raise_for_status()
        return response.json()
    
    def list_course_users(self, course_id: int) -> List[Dict]:
        """List all users enrolled in a course"""
        url = f"{self.base_url}/api/v1/courses/{course_id}/users"
        response = requests.get(url, headers=self.headers, params={"per_page": 100})
        response.raise_for_status()
        return response.json()
    
    def get_user_profile(self, user_id: int) -> Dict:
        """Get user profile information"""
        url = f"{self.base_url}/api/v1/users/{user_id}/profile"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def update_course(self, course_id: int, updates: Dict) -> Dict:
        """Update course settings"""
        url = f"{self.base_url}/api/v1/courses/{course_id}"
        data = {}
        for key, value in updates.items():
            data[f"course[{key}]"] = value
        response = requests.put(url, headers=self.headers, data=data)
        response.raise_for_status()
        return response.json()
