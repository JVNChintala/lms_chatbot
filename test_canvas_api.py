import requests
import os
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("CANVAS_URL", "").rstrip('/').replace('/api/v1', '')
TOKEN = os.getenv("CANVAS_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

def test_list_courses():
    url = f"{BASE_URL}/api/v1/courses"
    response = requests.get(url, headers=HEADERS, params={"per_page": 1000})
    print(f"List Courses: {response.status_code}")
    print(response.json())
    print('number of records:', len(response.json()))
    
def test_list_courses_with_account_id(account_id=1):
    url = f"{BASE_URL}/api/v1/accounts/{account_id}/courses"
    response = requests.get(url, headers=HEADERS, params={"per_page": 1000})
    print(f"List Courses: {response.status_code}")
    print(response.json())
    print('number of records:', len(response.json()))

def test_create_course(account_id=1):
    url = f"{BASE_URL}/api/v1/accounts/{account_id}/courses"
    data = {"course[name]": "Test Course", "course[course_code]": "TEST101"}
    response = requests.post(url, headers=HEADERS, data=data)
    print(f"Create Course: {response.status_code}")
    print(response.json())
    return response.json().get("id")

def test_get_course(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}"
    response = requests.get(url, headers=HEADERS)
    print(f"Get Course: {response.status_code}")
    print(response.json())

def test_update_course(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}"
    data = {"course[name]": "Updated Test Course"}
    response = requests.put(url, headers=HEADERS, data=data)
    print(f"Update Course: {response.status_code}")
    print(response.json())

def test_delete_course(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}"
    data = {"event": "delete"}
    response = requests.delete(url, headers=HEADERS, data=data)
    print(f"Delete Course: {response.status_code}")
    print(response.json())

def test_list_modules(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/modules"
    response = requests.get(url, headers=HEADERS)
    print(f"List Modules: {response.status_code}")
    print(response.json())

def test_create_module(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/modules"
    data = {"module[name]": "Test Module"}
    response = requests.post(url, headers=HEADERS, data=data)
    print(f"Create Module: {response.status_code}")
    print(response.json())
    return response.json().get("id")

def test_get_module(course_id, module_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/modules/{module_id}"
    response = requests.get(url, headers=HEADERS)
    print(f"Get Module: {response.status_code}")
    print(response.json())

def test_update_module(course_id, module_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/modules/{module_id}"
    data = {"module[name]": "Updated Module"}
    response = requests.put(url, headers=HEADERS, data=data)
    print(f"Update Module: {response.status_code}")
    print(response.json())

def test_delete_module(course_id, module_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/modules/{module_id}"
    response = requests.delete(url, headers=HEADERS)
    print(f"Delete Module: {response.status_code}")
    print(response.json())

def test_list_assignments(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/assignments"
    response = requests.get(url, headers=HEADERS)
    print(f"List Assignments: {response.status_code}")
    print(response.json())

def test_create_assignment(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/assignments"
    data = {"assignment[name]": "Test Assignment", "assignment[points_possible]": 100}
    response = requests.post(url, headers=HEADERS, data=data)
    print(f"Create Assignment: {response.status_code}")
    print(response.json())
    return response.json().get("id")

def test_list_users(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/users"
    response = requests.get(url, headers=HEADERS)
    print(f"List Users: {response.status_code}")
    print(response.json())

def test_enroll_user(course_id, user_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/enrollments"
    data = {"enrollment[user_id]": user_id, "enrollment[type]": "StudentEnrollment"}
    response = requests.post(url, headers=HEADERS, data=data)
    print(f"Enroll User: {response.status_code}")
    print(response.json())

def test_list_pages(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/pages"
    response = requests.get(url, headers=HEADERS)
    print(f"List Pages: {response.status_code}")
    print(response.json())

def test_create_page(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/pages"
    data = {"wiki_page[title]": "Test Page", "wiki_page[body]": "Test content"}
    response = requests.post(url, headers=HEADERS, data=data)
    print(f"Create Page: {response.status_code}")
    print(response.json())

def test_list_quizzes(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/quizzes"
    response = requests.get(url, headers=HEADERS)
    print(f"List Quizzes: {response.status_code}")
    print(response.json())

def test_create_quiz(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/quizzes"
    data = {"quiz[title]": "Test Quiz"}
    response = requests.post(url, headers=HEADERS, data=data)
    print(f"Create Quiz: {response.status_code}")
    print(response.json())

def test_list_announcements(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/discussion_topics"
    response = requests.get(url, headers=HEADERS, params={"only_announcements": True})
    print(f"List Announcements: {response.status_code}")
    print(response.json())

def test_create_announcement(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/discussion_topics"
    data = {"title": "Test Announcement", "message": "Test message", "is_announcement": True}
    response = requests.post(url, headers=HEADERS, data=data)
    print(f"Create Announcement: {response.status_code}")
    print(response.json())

def test_list_files(course_id):
    url = f"{BASE_URL}/api/v1/courses/{course_id}/files"
    response = requests.get(url, headers=HEADERS)
    print(f"List Files: {response.status_code}")
    print(response.json())

def test_list_accounts():
    url = f"{BASE_URL}/api/v1/accounts"
    response = requests.get(url, headers=HEADERS)
    print(f"List Accounts: {response.status_code}")
    print(response.json())

def test_authentication():
    """Test Canvas API authentication"""
    url = f"{BASE_URL}/api/v1/users/self"
    response = requests.get(url, headers=HEADERS)
    print(f"Authentication Test: {response.status_code}")
    if response.status_code == 200:
        user = response.json()
        print(f"Authenticated as: {user.get('name')} (ID: {user.get('id')})")
        print(f"Login ID: {user.get('login_id')}")
        print(f"Email: {user.get('email')}")
        return user
    else:
        print(f"Authentication failed: {response.text}")
        return None

def test_user_enrollments(user_id):
    """Test getting user enrollments to determine role"""
    url = f"{BASE_URL}/api/v1/users/{user_id}/enrollments"
    response = requests.get(url, headers=HEADERS)
    print(f"User Enrollments: {response.status_code}")
    if response.status_code == 200:
        enrollments = response.json()
        print(f"Total enrollments: {len(enrollments)}")
        for enrollment in enrollments[:3]:
            print(f"  - {enrollment.get('type')} in course {enrollment.get('course_id')}")
        return enrollments
    return []

if __name__ == "__main__":
    print("Testing Canvas LMS API\n")
    
    print("\n=== Authentication ===")
    user = test_authentication()
    
    if user:
        print("\n=== User Enrollments & Role ===")
        test_user_enrollments(user.get('id'))
    
    print("\n=== Courses ===")
    test_list_courses()
    
    print("\n=== Accounts ===")
    test_list_accounts()
