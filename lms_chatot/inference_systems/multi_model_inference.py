import os
import json
from openai import OpenAI
from .base_inference import BaseInference
from dotenv import load_dotenv
load_dotenv()

class MultiModelInference(BaseInference):
    """Multi-model inference system using different GPT models for different tasks"""
    
    def __init__(self):
        super().__init__()
        self.client = None
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI()
    
    def is_available(self) -> bool:
        return bool(os.getenv('OPENAI_API_KEY')) and self.client is not None
    
    def call_with_tools(self, system_prompt: str, messages: list, tools: list) -> dict:
        """Multi-stage inference with different models"""
        if not self.client:
            return {"needs_tool": False, "content": "OpenAI client not available"}
        
        # Stage 1: Intent detection with gpt-5-nano (cheapest)
        intent_prompt = "Tool needed? Reply TOOL or CHAT."
        intent_messages = [{"role": "system", "content": intent_prompt}] + messages[-1:]
        
        try:
            intent_response = self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=intent_messages,
                max_completion_tokens=5,
            )
            
            needs_tool = "TOOL" in intent_response.choices[0].message.content.upper()
            
            if not needs_tool:
                # Stage 2: Direct response with gpt-4.1-nano
                chat_response = self.client.chat.completions.create(
                    model="gpt-4.1-nano",
                    messages=[{"role": "system", "content": "Be concise"}] + messages,
                    max_tokens=100,
                    temperature=0.2
                )
                return {
                    "needs_tool": False,
                    "content": chat_response.choices[0].message.content,
                    "usage": {"model": "gpt-4.1-nano"}
                }
            
            # Stage 3: Tool calling with gpt-4.1-mini (cost-effective for tools)
            openai_tools = [{"type": "function", "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }} for tool in tools]
            
            tool_response = self.client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "system", "content": system_prompt}] + messages,
                tools=openai_tools,
                tool_choice="auto",
                max_tokens=150,
                temperature=0
            )
            
            message = tool_response.choices[0].message
            
            if message.tool_calls:
                return {
                    "needs_tool": True,
                    "tool_name": message.tool_calls[0].function.name,
                    "tool_args": json.loads(message.tool_calls[0].function.arguments),
                    "tool_call_id": message.tool_calls[0].id,
                    "usage": {"model": "gpt-4.1-mini"}
                }
            
            return {
                "needs_tool": False,
                "content": message.content,
                "usage": {"model": "gpt-4.1-mini"}
            }
            
        except Exception as e:
            return {"needs_tool": False, "content": f"Error: {str(e)}"}
    
    def get_final_response(self, messages: list, tool_result: dict, tool_call_id: str) -> str:
        """Generate final response with gpt-4o-mini for efficiency"""
        if not self.client:
            return "Operation completed"
        
        try:
            # Stage 4: Output formatting with gpt-5-nano (cheapest)
            format_prompt = f"Format concisely: {json.dumps(tool_result)}"
            
            final_response = self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[{"role": "system", "content": format_prompt}],
                max_completion_tokens=50,                
            )
            
            return final_response.choices[0].message.content
            
        except Exception as e:
            # Ultra-minimal fallback
            if "courses" in str(tool_result):
                return f"{len(tool_result.get('courses', []))} courses found"
            return "Done"