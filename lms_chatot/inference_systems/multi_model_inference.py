import os
import json
from openai import OpenAI
from .base_inference import BaseInference
from dotenv import load_dotenv
load_dotenv()

class MultiModelInference(BaseInference):
    """Unified OpenAI inference with multi-model optimization for Canvas LMS"""
    
    def __init__(self, use_multi_model=True):
        super().__init__()
        self.client = None
        self.use_multi_model = use_multi_model
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI()
    
    def _get_canvas_system_prompt(self, base_prompt: str) -> str:
        """Add Canvas LMS context to system prompt"""
        canvas_context = "You are a Canvas LMS AI Assistant helping teachers, students, and admins manage Canvas operations effectively."
        return f"{canvas_context} {base_prompt}"
    
    def is_available(self) -> bool:
        return bool(os.getenv('OPENAI_API_KEY')) and self.client is not None
    
    def call_with_tools(self, system_prompt: str, messages: list, tools: list) -> dict:
        """Unified inference with optional multi-model optimization"""
        if not self.client:
            return {"needs_tool": False, "content": "OpenAI client not available"}
        
        enhanced_prompt = self._get_canvas_system_prompt(system_prompt)
        
        if self.use_multi_model:
            return self._multi_model_inference(enhanced_prompt, messages, tools)
        else:
            return self._single_model_inference(enhanced_prompt, messages, tools)
    
    def _multi_model_inference(self, system_prompt: str, messages: list, tools: list) -> dict:
        """Multi-stage inference with cost optimization"""
        try:
            # Stage 1: Intent detection
            intent_response = self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[{"role": "system", "content": "Canvas LMS Assistant: Tool needed? Reply TOOL or CHAT."}] + messages[-1:],
                max_completion_tokens=5,
            )
            
            if "TOOL" not in intent_response.choices[0].message.content.upper():
                # Direct chat response
                chat_response = self.client.chat.completions.create(
                    model="gpt-4.1-nano",
                    messages=[{"role": "system", "content": system_prompt}] + messages,
                    max_tokens=100, temperature=0.2
                )
                return {"needs_tool": False, "content": chat_response.choices[0].message.content, "usage": {"model": "gpt-4.1-nano"}}
            
            # Tool calling
            return self._execute_tool_call(system_prompt, messages, tools, "gpt-4.1-mini")
            
        except Exception as e:
            return {"needs_tool": False, "content": f"Error: {str(e)}"}
    
    def _single_model_inference(self, system_prompt: str, messages: list, tools: list) -> dict:
        """Single model inference (fallback)"""
        return self._execute_tool_call(system_prompt, messages, tools, "gpt-4o-mini")
    
    def _execute_tool_call(self, system_prompt: str, messages: list, tools: list, model: str) -> dict:
        """Execute tool calling with specified model"""
        openai_tools = [{"type": "function", "function": {
            "name": tool["name"], "description": tool["description"], "parameters": tool["input_schema"]
        }} for tool in tools]
        
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            tools=openai_tools, tool_choice="auto", max_tokens=150, temperature=0
        )
        
        message = response.choices[0].message
        if message.tool_calls:
            return {
                "needs_tool": True,
                "tool_name": message.tool_calls[0].function.name,
                "tool_args": json.loads(message.tool_calls[0].function.arguments),
                "tool_call_id": message.tool_calls[0].id,
                "usage": {"model": model}
            }
        return {"needs_tool": False, "content": message.content, "usage": {"model": model}}
    
    def get_final_response(self, messages: list, tool_result: dict, tool_call_id: str) -> str:
        """Generate Canvas LMS contextual final response"""
        if not self.client:
            return "Canvas operation completed"
        
        try:
            model = "gpt-5-nano" if self.use_multi_model else "gpt-4o-mini"
            canvas_format_prompt = self._get_canvas_system_prompt(f"Format Canvas operation result concisely: {json.dumps(tool_result)}")
            
            final_response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": canvas_format_prompt}],
                max_tokens=50, temperature=0
            )
            
            return final_response.choices[0].message.content
            
        except Exception as e:
            if "courses" in str(tool_result):
                return f"Found {len(tool_result.get('courses', []))} Canvas courses"
            return "Canvas operation completed"