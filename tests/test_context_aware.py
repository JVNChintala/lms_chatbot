"""Test context-aware parameter extraction"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lms_chatot'))

from dotenv import load_dotenv
from canvas_agent import CanvasAgent

load_dotenv()

agent = CanvasAgent(
    canvas_url=os.getenv("CANVAS_URL"),
    admin_canvas_token=os.getenv("CANVAS_TOKEN")
)

# Step 1: List courses
print("=== STEP 1: List Courses ===")
response1 = agent.process_message(
    "list all courses",
    conversation_history=[],
    user_role="teacher",
    user_info={"canvas_user_id": 1765}
)
print(f"Response: {response1['content'][:200]}...")

# Step 2: Create module without course_id
print("\n=== STEP 2: Create Module (No course_id) ===")
response2 = agent.process_message(
    "create a module",
    conversation_history=[
        {"role": "user", "content": "list all courses"},
        {"role": "assistant", "content": response1['content'], "raw_tool_data": response1.get('raw_tool_data')}
    ],
    user_role="teacher",
    user_info={"canvas_user_id": 1765}
)
print(f"Response: {response2['content'][:200]}...")
print(f"Clarification Needed: {response2.get('clarification_needed')}")

# Step 3: Provide course name (should extract ID from history)
print("\n=== STEP 3: Provide Course Name ===")
response3 = agent.process_message(
    "create a module named 'Week 1' in Training Test",
    conversation_history=[
        {"role": "user", "content": "list all courses"},
        {"role": "assistant", "content": response1['content'], "raw_tool_data": response1.get('raw_tool_data')},
        {"role": "user", "content": "create a module"},
        {"role": "assistant", "content": response2['content']}
    ],
    user_role="teacher",
    user_info={"canvas_user_id": 1765},
    pending_tool=response2.get('pending_tool'),
    pending_tool_def=response2.get('pending_tool_def')
)
print(f"Response: {response3['content'][:200]}...")
print(f"Tool Used: {response3.get('tool_used')}")
print(f"Success: {response3.get('tool_used') == True}")
