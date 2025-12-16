import os
import json
from openai import OpenAI
from .base_inference import BaseInference
from model_config import ModelConfig
from dotenv import load_dotenv
load_dotenv()

class OpenAIInference(BaseInference):
    """Legacy OpenAI inference - use MultiModelInference instead"""
    
    def __init__(self):
        super().__init__()
        self.client = None
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI()
    
    def is_available(self) -> bool:
        return bool(os.getenv('OPENAI_API_KEY')) and self.client is not None
    
    def call_with_tools(self, system_prompt: str, messages: list, tools: list) -> dict:
        """Basic single-model inference - use MultiModelInference for optimization"""
        if not self.client:
            return {"needs_tool": False, "content": "OpenAI client not available"}
        
        openai_tools = [{"type": "function", "function": {
            "name": tool["name"], "description": tool["description"], "parameters": tool["input_schema"]
        }} for tool in tools]
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system_prompt}] + messages,
                tools=openai_tools, tool_choice="auto", max_tokens=200, temperature=0.1
            )
            
            message = response.choices[0].message
            if message.tool_calls:
                return {
                    "needs_tool": True,
                    "tool_name": message.tool_calls[0].function.name,
                    "tool_args": json.loads(message.tool_calls[0].function.arguments),
                    "tool_call_id": message.tool_calls[0].id,
                    "usage": {"model": "gpt-4o-mini"}
                }
            return {"needs_tool": False, "content": message.content, "usage": {"model": "gpt-4o-mini"}}
            
        except Exception as e:
            return {"needs_tool": False, "content": f"Error: {str(e)}"}
    
    def get_final_response(self, messages: list, tool_result: dict, tool_call_id: str) -> str:
        """Basic response formatting"""
        if "courses" in str(tool_result):
            return f"Found {len(tool_result.get('courses', []))} courses"
        return "Operation completed"