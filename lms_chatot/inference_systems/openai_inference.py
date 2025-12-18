import os
import json
from openai import OpenAI
from .base_inference import BaseInference
from model_config import ModelConfig
from dotenv import load_dotenv
load_dotenv()

class OpenAIInference(BaseInference):
    """Unified OpenAI inference with multi-model optimization for Canvas LMS"""
    
    def __init__(self):
        super().__init__()
        self.client = None
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.client = OpenAI()
    
    def _get_canvas_system_prompt(self, base_prompt: str) -> str:
        """Add Canvas LMS context to system prompt"""
        canvas_context = "You are a Canvas LMS AI Assistant helping teachers, students, and admins manage Canvas operations effectively."
        return f"{canvas_context} {base_prompt}"
    
    def is_available(self) -> bool:
        return bool(os.getenv('OPENAI_API_KEY')) and self.client is not None
    
    def call_with_tools(self, system_prompt: str, messages: list, tools: list, force_tool: str = None) -> dict:
        """Canvas LMS inference with tool calling"""
        if not self.client:
            return {"needs_tool": False, "content": "OpenAI client not available"}
        
        enhanced_prompt = self._get_canvas_system_prompt(system_prompt)
        return self._execute_tool_call(enhanced_prompt, messages, tools, "gpt-4o-mini", force_tool)

    def _execute_tool_call(self, system_prompt: str, messages: list, tools: list, model: str, force_tool: str = None) -> dict:
        """Execute tool calling with specified model"""
        openai_tools = []
        for tool in tools:
            # Handle both old and new tool formats
            if "function" in tool:
                # New format from intent classifier
                openai_tools.append(tool)
            else:
                # Old format - convert
                openai_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool["description"],
                        "parameters": {
                            "type": "object",
                            "properties": tool["input_schema"].get("properties", {}),
                            "required": tool["input_schema"].get("required", []),
                            "additionalProperties": False
                        }
                    }
                })
        
        # Determine tool choice
        tool_choice = "auto"
        if force_tool and openai_tools:
            tool_choice = {
                "type": "function",
                "function": {"name": force_tool}
            }
        
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "system", "content": system_prompt}] + messages,
            tools=openai_tools, 
            tool_choice=tool_choice, 
            max_tokens=200
        )
        
        # Extract usage data
        usage_data = {
            "model": model,
            "input_tokens": response.usage.prompt_tokens if response.usage else 0,
            "output_tokens": response.usage.completion_tokens if response.usage else 0,
            "total_tokens": response.usage.total_tokens if response.usage else 0
        }
        
        message = response.choices[0].message
        if message.tool_calls:
            tool_name = message.tool_calls[0].function.name
            tool_args = json.loads(message.tool_calls[0].function.arguments)
            print(f"[DEBUG] OpenAI wants to call tool: {tool_name} with args: {tool_args}")
            return {
                "needs_tool": True,
                "tool_name": tool_name,
                "tool_args": tool_args,
                "tool_call_id": message.tool_calls[0].id,
                "usage": usage_data
            }
        print(f"[DEBUG] OpenAI direct response: {message.content}")
        return {"needs_tool": False, "content": message.content, "usage": usage_data}
    
    def get_final_response(self, messages: list, tool_result: dict, tool_call_id: str) -> str:
        """Generate Canvas LMS contextual final response"""
        if not self.client:
            return "Canvas operation completed"
        
        try:
            canvas_format_prompt = f"Based on this Canvas operation result, provide a natural, helpful response. Don't show raw JSON. Be conversational. Result: {json.dumps(tool_result)}"
            
            final_response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": canvas_format_prompt}],
                max_tokens=100
            )

            # Store usage for final response
            self._final_usage = {
                "model": "gpt-4o-mini",
                "input_tokens": final_response.usage.prompt_tokens if final_response.usage else 0,
                "output_tokens": final_response.usage.completion_tokens if final_response.usage else 0,
                "total_tokens": final_response.usage.total_tokens if final_response.usage else 0
            }

            return final_response.choices[0].message.content or "Operation completed successfully"
            
        except Exception as e:
            print(f"[DEBUG] Final response failed, using fallback. Error: {e}")
            if "courses" in str(tool_result):
                courses = tool_result.get("courses", [])
                if courses:
                    course_list = "\n".join([f"- {c.get('name', 'Unknown')} (ID: {c.get('id', 'N/A')})" for c in courses])
                    return f"Here are your {len(courses)} courses:\n{course_list}\n\nWhat would you like to do with any of these courses?"
                return "No courses found. Would you like me to help you create a new course?"
            elif "name" in str(tool_result) and "id" in str(tool_result):
                if "module" in str(tool_result).lower() or "items_url" in str(tool_result):
                    return f"Successfully created module '{tool_result.get('name')}' with ID {tool_result.get('id')}. The module is ready for content."
                else:
                    return f"Successfully created '{tool_result.get('name')}' with ID {tool_result.get('id')}."
            return "Operation completed successfully. How else can I help you?"
    
    def get_final_usage(self):
        """Get usage from final response call"""
        return getattr(self, '_final_usage', None)