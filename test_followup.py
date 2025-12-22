"""Test clarification follow-up flow"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lms_chatot'))

from dotenv import load_dotenv
from canvas_agent import CanvasAgent

load_dotenv()

def test_clarification_flow():
    """Test: Create course with follow-up clarification"""
    agent = CanvasAgent(
        canvas_url=os.getenv("CANVAS_URL"),
        admin_canvas_token=os.getenv("CANVAS_TOKEN")
    )
    
    # Step 1: Ask without args
    response1 = agent.process_message(
        "Create a course",
        conversation_history=[],
        user_role="admin",
        user_info={"canvas_user_id": 1765}
    )
    
    print("=== STEP 1: Initial Request ===")
    print(f"Response: {response1['content']}")
    print(f"Clarification Needed: {response1.get('clarification_needed')}")
    print(f"Pending Tool: {response1.get('pending_tool')}")
    
    if not response1.get('clarification_needed'):
        print("FAIL: Should ask for clarification")
        return
    
    # Step 2: Provide missing info
    response2 = agent.process_message(
        "Name it 'Follow-up Test Course' with code 'FOLLOWUP-01'",
        conversation_history=[
            {"role": "user", "content": "Create a course"},
            {"role": "assistant", "content": response1['content']}
        ],
        user_role="admin",
        user_info={"canvas_user_id": 1765},
        pending_tool=response1.get('pending_tool'),
        pending_tool_def=response1.get('pending_tool_def')
    )
    
    print("\n=== STEP 2: Follow-up with Info ===")
    print(f"Response: {response2['content'][:200]}...")
    print(f"Tool Used: {response2.get('tool_used')}")
    print(f"Success: {response2.get('tool_used') == True}")

if __name__ == "__main__":
    test_clarification_flow()
