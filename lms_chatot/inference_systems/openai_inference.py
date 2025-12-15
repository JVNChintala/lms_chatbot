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
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            try:
                # Set environment variable and use default initialization
                os.environ['OPENAI_API_KEY'] = api_key
                self.client = OpenAI()
                print(f"[OpenAI] Client initialized successfully")
            except Exception as e:
                print(f"[OpenAI] Failed to initialize client: {e}")
                self.client = None
    
    def is_available(self) -> bool:
        return bool(os.getenv('OPENAI_API_KEY')) and self.client is not None
    
    def call_with_tools(self, system_prompt: str, messages: list, tools: list) -> dict:
        """Call OpenAI API with function calling - Optimized for Canvas LMS"""
        # Convert tools to OpenAI format
        openai_tools = [{
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["input_schema"]
            }
        } for tool in tools]
        
        # Optimize system prompt for Canvas LMS
        optimized_system = f"{system_prompt}\n\nYou are an expert Canvas LMS assistant. Always use tools to get real data. Be concise and helpful."
        
        # Add system message
        openai_messages = [{"role": "system", "content": optimized_system}] + messages
        
        if not self.client:
            return {
                "needs_tool": False,
                "content": "OpenAI client not available. Please check your API key and try again."
            }
        
        try:
            response = self.client.chat.completions.create(
                model=ModelConfig.OPENAI_MODEL,
                messages=openai_messages,
                tools=openai_tools,
                tool_choice="auto",
                max_tokens=ModelConfig.MAX_TOKENS,
                temperature=ModelConfig.TEMPERATURE,
                stream=False,
                timeout=30
            )
            
            message = response.choices[0].message
            
            # Extract token usage
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            
            # Handle tool calls
            if message.tool_calls:
                return {
                    "needs_tool": True,
                    "tool_name": message.tool_calls[0].function.name,
                    "tool_args": json.loads(message.tool_calls[0].function.arguments),
                    "tool_call_id": message.tool_calls[0].id,
                    "assistant_message": message,
                    "usage": {
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                        "model": ModelConfig.OPENAI_MODEL
                    }
                }
            
            # No tool use
            return {
                "needs_tool": False,
                "content": message.content,
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": input_tokens + output_tokens,
                    "model": ModelConfig.OPENAI_MODEL
                }
            }
            
        except Exception as e:
            error_msg = str(e)
            if "rate_limit" in error_msg.lower():
                return {
                    "needs_tool": False,
                    "content": "OpenAI rate limit reached. Please try again in a moment."
                }
            elif "timeout" in error_msg.lower():
                return {
                    "needs_tool": False,
                    "content": "Request timed out. Please try again."
                }
            else:
                return {
                    "needs_tool": False,
                    "content": f"OpenAI API error: {error_msg}"
                }
    
    def get_final_response(self, messages: list, tool_result: dict, tool_call_id: str) -> str:
        """Get final response after tool execution"""
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": json.dumps(tool_result)
        })
        
        if not self.client:
            return f"Canvas operation completed successfully. Tool result: {tool_result}"
        
        try:
            final_response = self.client.chat.completions.create(
                model=ModelConfig.OPENAI_MODEL,
                messages=messages,
                max_tokens=ModelConfig.MAX_TOKENS,
                temperature=ModelConfig.TEMPERATURE,
                stream=False,
                timeout=30
            )
            
            # Store additional usage for final response
            if hasattr(final_response, 'usage') and final_response.usage:
                self._additional_usage = {
                    "input_tokens": final_response.usage.prompt_tokens,
                    "output_tokens": final_response.usage.completion_tokens,
                    "total_tokens": final_response.usage.total_tokens
                }
            
            return final_response.choices[0].message.content
            
        except Exception as e:
            return f"Canvas operation completed successfully. Tool result: {tool_result}"
    
    def get_additional_usage(self):
        """Get additional usage from final response"""
        return getattr(self, '_additional_usage', None)