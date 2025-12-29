"""Test OpenAI Responses API with real Canvas LMS tool calls"""
import os
from dotenv import load_dotenv
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lms_chatot'))
from canvas_agent import CanvasAgent

load_dotenv()

def test_list_courses():
    """Test: List my courses"""
    agent = CanvasAgent(
        canvas_url=os.getenv("CANVAS_URL"),
        admin_canvas_token=os.getenv("CANVAS_TOKEN")
    )
    
    response = agent.process_message(
        "List my courses",
        conversation_history=[],
        user_role="student",
        user_info={"canvas_user_id": "self"}
    )
    print("\n=== TEST 1: List Courses ===")
    print(f"Response: {response['content'][:200]}...")
    print(f"Tool Used: {response.get('tool_used')}")
    print(f"Success: {response.get('tool_used') == True}")

def test_get_course_modules():
    """Test: Show modules in a course"""
    agent = CanvasAgent(
        canvas_url=os.getenv("CANVAS_URL"),
        admin_canvas_token=os.getenv("CANVAS_TOKEN")
    )
    
    response = agent.process_message(
        "Show me modules in course 1",
        conversation_history=[],
        user_role="student",
        user_info={"canvas_user_id": "self"}
    )
    print("\n=== TEST 2: Get Course Modules ===")
    print(f"Response: {response['content'][:200]}...")
    print(f"Tool Used: {response.get('tool_used')}")
    print(f"Success: {response.get('tool_used') == True}")

def test_create_course():
    """Test: Create a new course"""
    agent = CanvasAgent(
        canvas_url=os.getenv("CANVAS_URL"),
        admin_canvas_token=os.getenv("CANVAS_TOKEN")
    )
    
    response = agent.process_message(
        "Create a course named 'OpenAI Test Course' with code 'OPENAI-TEST'",
        conversation_history=[],
        user_role="admin",
        user_info={"canvas_user_id": 1765}
    )
    print("\n=== TEST 4: Create Course ===")
    print(f"Response: {response['content'][:300]}...")
    print(f"Tool Used: {response.get('tool_used')}")
    print(f"Success: {response.get('tool_used') == True}")
    return response

def test_create_course_no_args():
    """Test: Create course without arguments"""
    agent = CanvasAgent(
        canvas_url=os.getenv("CANVAS_URL"),
        admin_canvas_token=os.getenv("CANVAS_TOKEN")
    )
    
    response = agent.process_message(
        "Create a course",
        conversation_history=[],
        user_role="admin",
        user_info={"canvas_user_id": 1765}
    )
    print("\n=== TEST 6: Create Course (No Args) ===")
    print(f"Response: {response['content'][:400]}")
    print(f"Tool Used: {response.get('tool_used')}")
    print(f"Missing Args: {response.get('tool_results', [{}])[0].get('result', {}).get('missing_args')}")

def test_create_module_no_args():
    """Test: Create module without arguments"""
    agent = CanvasAgent(
        canvas_url=os.getenv("CANVAS_URL"),
        admin_canvas_token=os.getenv("CANVAS_TOKEN")
    )
    
    response = agent.process_message(
        "Create a module",
        conversation_history=[],
        user_role="teacher",
        user_info={"canvas_user_id": 1765}
    )
    print("\n=== TEST 7: Create Module (No Args) ===")
    print(f"Response: {response['content'][:400]}")
    print(f"Tool Used: {response.get('tool_used')}")
    print(f"Missing Args: {response.get('tool_results', [{}])[0].get('result', {}).get('missing_args')}")

if __name__ == "__main__":
    print("Testing OpenAI Responses API with Canvas LMS Integration\n")
    
    try:
        test_create_course()
        print("\n" + "="*50)
        test_create_course_no_args()
        test_create_module_no_args()
        print("\n[OK] All tests completed")
    except Exception as e:
        print("\nX Test failed: {}".format(e))
        import traceback
        traceback.print_exc()
