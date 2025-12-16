import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from .base_inference import BaseInference
from model_config import ModelConfig

load_dotenv()

class GeminiInference(BaseInference):
    """Google Gemini inference system"""
    
    def __init__(self):
        super().__init__()
        self.client = None
        if self.is_available():
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.model = genai.GenerativeModel(ModelConfig.GEMINI_MODEL)
    
    def is_available(self) -> bool:
        return bool(os.getenv('GEMINI_API_KEY'))
    
    def call_with_tools(self, system_prompt: str, messages: list, tools: list) -> dict:
        """Call Gemini API with enhanced tool detection"""
        user_message = messages[-1]["content"] if messages else ""
        
        # Enhanced tool detection prompt
        tool_names = [t['name'] for t in tools]
        tool_prompt = f"""{system_prompt}

Available Canvas tools: {tool_names}

User: {user_message}

Analyze the user request. If you need to use a Canvas tool:
1. Respond with: TOOL: tool_name
2. Extract any required parameters from the user message
3. For list_courses, create_course, etc. - determine the appropriate tool

Otherwise, respond normally to help the user."""
        
        try:
            response = self.model.generate_content(tool_prompt)
            response_text = response.text.strip()
            
            # Enhanced tool detection
            if "TOOL:" in response_text:
                lines = response_text.split('\n')
                for line in lines:
                    if line.strip().startswith('TOOL:'):
                        tool_name = line.split(':', 1)[1].strip()
                        
                        # Extract arguments based on user message
                        tool_args = self._extract_arguments(user_message, tool_name, tools)
                        
                        return {
                            "needs_tool": True,
                            "tool_name": tool_name,
                            "tool_args": tool_args,
                            "response_text": response_text
                        }
            
            return {
                "needs_tool": False,
                "content": response_text
            }
            
        except Exception as e:
            return {
                "needs_tool": False,
                "content": f"Gemini error: {str(e)}"
            }
    
    def _extract_arguments(self, user_message: str, tool_name: str, tools: list) -> dict:
        """Extract arguments from user message for tool calling"""
        import re
        
        # Find tool schema
        tool_schema = None
        for tool in tools:
            if tool["name"] == tool_name:
                tool_schema = tool["input_schema"]
                break
        
        if not tool_schema or "properties" not in tool_schema:
            return {}
        
        args = {}
        user_lower = user_message.lower()
        
        # Extract common parameters
        if "course_id" in tool_schema["properties"]:
            course_match = re.search(r'course\s+(\d+)', user_message, re.IGNORECASE)
            if course_match:
                args["course_id"] = int(course_match.group(1))
        
        if "name" in tool_schema["properties"]:
            # Extract course/assignment name
            name_patterns = [
                r'(?:course|assignment|named?)\s+["\']([^"\'\.\n]+)["\']',
                r'(?:course|assignment)\s+([A-Za-z0-9\s]+?)(?:\s|$)',
                r'create\s+([A-Za-z0-9\s]+?)(?:\s|$)'
            ]
            for pattern in name_patterns:
                match = re.search(pattern, user_message, re.IGNORECASE)
                if match:
                    args["name"] = match.group(1).strip()
                    break
        
        if "course_code" in tool_schema["properties"] and "name" in args:
            # Generate course code from name
            args["course_code"] = args["name"].replace(' ', '').upper()[:10]
        
        if "points" in tool_schema["properties"]:
            points_match = re.search(r'(\d+)\s+points?', user_message, re.IGNORECASE)
            if points_match:
                args["points"] = int(points_match.group(1))
        
        return args
    
    def get_final_response(self, messages: list, tool_result: dict, response_text: str) -> str:
        """Get final response after tool execution"""
        try:
            # Create contextual prompt based on tool result
            if "courses" in tool_result:
                courses = tool_result["courses"]
                if courses:
                    course_list = "\n".join([f"- {c['name']} ({c['course_code']})" for c in courses[:5]])
                    final_prompt = f"Here are the Canvas courses:\n{course_list}\n\nProvide a helpful summary and ask if the user needs help with any specific course."
                else:
                    final_prompt = "No courses found. Suggest creating a new course or checking permissions."
            elif "error" in tool_result:
                final_prompt = f"There was an issue: {tool_result['error']}. Provide helpful troubleshooting suggestions."
            else:
                final_prompt = f"Canvas operation completed successfully: {json.dumps(tool_result)}\n\nProvide a helpful response about what was accomplished."
            
            response = self.model.generate_content(final_prompt)
            return response.text
        except Exception as e:
            return f"Canvas operation completed: {tool_result}"