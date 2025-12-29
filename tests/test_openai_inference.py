"""Test OpenAI Inference System"""
import os
import sys
from dotenv import load_dotenv

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'lms_chatot'))
from inference_systems.openai_inference import OpenAIInference

load_dotenv()

def test_basic_conversation():
    """Test basic conversation without tools"""
    print("\n=== TEST 1: Basic Conversation ===")
    inference = OpenAIInference()
    
    if not inference.is_available():
        print("❌ OpenAI not available - check API key")
        return False
    
    result = inference.call_with_tools(
        system_prompt="You are a helpful assistant.",
        messages=[{"role": "user", "content": "Hello, how are you?"}],
        tools=[]
    )
    
    print(f"Response: {result.get('content')}")
    print(f"Needs tool: {result.get('needs_tool')}")
    print(f"Usage: {result.get('usage')}")
    return True

def test_tool_selection():
    """Test tool selection with simple tools"""
    print("\n=== TEST 2: Tool Selection ===")
    inference = OpenAIInference()
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Get weather for a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {"type": "string", "description": "City name"}
                    },
                    "required": ["location"]
                }
            }
        }
    ]
    
    result = inference.call_with_tools(
        system_prompt="You are a helpful assistant with access to weather data.",
        messages=[{"role": "user", "content": "What's the weather in Paris?"}],
        tools=tools
    )
    
    print(f"Needs tool: {result.get('needs_tool')}")
    print(f"Tool name: {result.get('tool_name')}")
    print(f"Tool args: {result.get('tool_args')}")
    print(f"Usage: {result.get('usage')}")
    return result.get('needs_tool') == True

def test_missing_args():
    """Test missing argument detection"""
    print("\n=== TEST 3: Missing Arguments ===")
    inference = OpenAIInference()
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "create_course",
                "description": "Create a new course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "code": {"type": "string"}
                    },
                    "required": ["name", "code"]
                }
            }
        }
    ]
    
    result = inference.call_with_tools(
        system_prompt="You are a Canvas LMS assistant.",
        messages=[{"role": "user", "content": "Create a course"}],
        tools=tools
    )
    
    print(f"Needs tool: {result.get('needs_tool')}")
    print(f"Missing args: {result.get('missing_args')}")
    print(f"Clarification: {result.get('content')}")
    return result.get('missing_args') is not None

def test_canvas_tools():
    """Test with actual Canvas tool schemas"""
    print("\n=== TEST 4: Canvas Tools ===")
    inference = OpenAIInference()
    
    tools = [
        {
            "type": "function",
            "function": {
                "name": "list_user_courses",
                "description": "List all courses for the current user",
                "parameters": {"type": "object", "properties": {}}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "create_module",
                "description": "Create a new module in a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                        "name": {"type": "string"}
                    },
                    "required": ["course_id", "name"]
                }
            }
        }
    ]
    
    result = inference.call_with_tools(
        system_prompt="You are a Canvas LMS assistant.",
        messages=[{"role": "user", "content": "Show me my courses"}],
        tools=tools
    )
    
    print(f"Needs tool: {result.get('needs_tool')}")
    print(f"Tool name: {result.get('tool_name')}")
    print(f"Tool args: {result.get('tool_args')}")
    return result.get('tool_name') == 'list_user_courses'

def main():
    print("🧪 Testing OpenAI Inference System\n")
    print("="*60)
    
    tests = [
        ("Basic Conversation", test_basic_conversation),
        ("Tool Selection", test_tool_selection),
        ("Missing Arguments", test_missing_args),
        ("Canvas Tools", test_canvas_tools)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
            print(f"✅ {name}: {'PASS' if success else 'FAIL'}")
        except Exception as e:
            results.append((name, False))
            print(f"❌ {name}: ERROR - {e}")
            import traceback
            traceback.print_exc()
        print("-"*60)
    
    print("\n" + "="*60)
    print("📊 Test Summary:")
    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")

if __name__ == "__main__":
    main()
