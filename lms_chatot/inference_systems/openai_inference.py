import os
import json
from openai import OpenAI
from .base_inference import BaseInference
from model_config import ModelConfig

class OpenAIInference(BaseInference):
    """OpenAI GPT-4 inference system"""
    
    def __init__(self):
        super().__init__()
        self.client = None
        if self.is_available():
            self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def is_available(self) -> bool:
        return bool(os.getenv('OPENAI_API_KEY'))
    
    def call_with_tools(self, system_prompt: str, messages: list, tools: list) -> dict:
        """Call OpenAI API with function calling"""
        # Convert tools to OpenAI format
        openai_tools = [{
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }
        } for tool in tools]
        
        # Add system message
        openai_messages = [{"role": "system", "content": system_prompt}] + messages
        
        response = self.client.chat.completions.create(
            model=ModelConfig.OPENAI_MODEL,
            messages=openai_messages,
            tools=openai_tools,
            tool_choice="auto",
            max_tokens=ModelConfig.MAX_TOKENS
        )
        
        message = response.choices[0].message
        
        # Handle tool calls
        if message.tool_calls:
            return {
                "needs_tool": True,
                "tool_name": message.tool_calls[0].function.name,
                "tool_args": json.loads(message.tool_calls[0].function.arguments),
                "tool_call_id": message.tool_calls[0].id,
                "assistant_message": message
            }
        
        # No tool use
        return {
            "needs_tool": False,
            "content": message.content
        }
    
    def get_final_response(self, messages: list, tool_result: dict, tool_call_id: str) -> str:
        """Get final response after tool execution"""
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": json.dumps(tool_result)
        })
        
        final_response = self.client.chat.completions.create(
            model=ModelConfig.OPENAI_MODEL,
            messages=messages,
            max_tokens=ModelConfig.MAX_TOKENS
        )
        
        return final_response.choices[0].message.content