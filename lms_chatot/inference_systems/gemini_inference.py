import os
import json
import google.generativeai as genai
from .base_inference import BaseInference

class GeminiInference(BaseInference):
    """Google Gemini inference system"""
    
    def __init__(self):
        super().__init__()
        self.client = None
        if self.is_available():
            genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
            self.model = genai.GenerativeModel('gemini-pro')
    
    def is_available(self) -> bool:
        return bool(os.getenv('GEMINI_API_KEY'))
    
    def call_with_tools(self, system_prompt: str, messages: list, tools: list) -> dict:
        """Call Gemini API with simple text generation"""
        user_message = messages[-1]["content"] if messages else ""
        
        # Simple tool detection via prompt
        tool_prompt = f"{system_prompt}\n\nAvailable tools: {[t['name'] for t in tools]}\n\nUser: {user_message}\n\nIf you need to use a tool, respond with 'TOOL: tool_name' followed by parameters. Otherwise, respond normally."
        
        try:
            response = self.model.generate_content(tool_prompt)
            response_text = response.text.strip()
            
            # Check if tool is requested
            if response_text.startswith('TOOL:'):
                parts = response_text.split(':', 1)
                if len(parts) > 1:
                    tool_name = parts[1].strip().split()[0]
                    # Find matching tool
                    for tool in tools:
                        if tool["name"] == tool_name:
                            return {
                                "needs_tool": True,
                                "tool_name": tool_name,
                                "tool_args": {},  # Simple implementation
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
    
    def get_final_response(self, messages: list, tool_result: dict, response_text: str) -> str:
        """Get final response after tool execution"""
        try:
            final_prompt = f"Tool result: {json.dumps(tool_result)}\n\nProvide a helpful response based on this Canvas data:"
            response = self.model.generate_content(final_prompt)
            return response.text
        except Exception as e:
            return f"Tool executed successfully: {tool_result}"