"""Debug OpenAI Responses API tool calling"""
import sys
import os
import logging
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lms_chatot'))

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from dotenv import load_dotenv
from inference_systems.openai_inference import OpenAIInference

load_dotenv()

# Simple tool schema
tool = {
    "type": "function",
    "function": {
        "name": "list_user_courses",
        "description": "List courses for a user",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "User ID"}
            },
            "required": ["user_id"]
        }
    }
}

inference = OpenAIInference()
print(f"OpenAI available: {inference.is_available()}")

result = inference.call_with_tools(
    system_prompt="You must call the list_user_courses function. Do not respond with text.",
    messages=[{"role": "user", "content": "List my courses"}],
    tools=[tool],
    force_tool="list_user_courses"
)

print(f"\nResult:")
print(f"  needs_tool: {result.get('needs_tool')}")
print(f"  tool_name: {result.get('tool_name')}")
print(f"  tool_args: {result.get('tool_args')}")
print(f"  content: {result.get('content')}")
