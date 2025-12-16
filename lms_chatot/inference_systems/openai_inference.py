import os
import json
from openai import OpenAI
from .base_inference import BaseInference
from model_config import ModelConfig
from dotenv import load_dotenv
load_dotenv()


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
        
        # Create contextual system prompt
        contextual_system = f"{system_prompt}\n\nBe helpful and contextually aware. When users refer to 'recent course' or similar, use context from the conversation. Ask for clarification when needed."
        
        # Add system message with full conversation history
        openai_messages = [{"role": "system", "content": contextual_system}] + messages
        
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
            content = message.content or "Canvas LMS assistant ready. How can I help?"
            return {
                "needs_tool": False,
                "content": content,
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
        """Get conversational final response after tool execution"""
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call_id,
            "content": json.dumps(tool_result)
        })
        
        if not self.client:
            return f"Perfect! I've completed that for you. 😊 Here's what I found: {tool_result}"
        
        try:
            # Add instruction for contextual response from tool results
            messages.append({
                "role": "system",
                "content": f"Based on the tool results and conversation context, provide a helpful response. If a course was just created, mention its details. If user asks about 'recent course', refer to the most recently created one. Be informative and contextually aware. Tool results: {json.dumps(tool_result)}"
            })
            
            final_response = self.client.chat.completions.create(
                model=ModelConfig.OPENAI_MODEL,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
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
            # Provide contextual response based on tool result
            if "courses" in str(tool_result):
                courses = tool_result.get("courses", [])
                if courses:
                    course_list = "\n".join([f"- {c.get('name', 'Unknown')} (ID: {c.get('id', 'N/A')})" for c in courses])
                    return f"Found {len(courses)} courses:\n{course_list}"
                else:
                    return "No courses found."
            elif "id" in str(tool_result) and "name" in str(tool_result):
                course_name = tool_result.get('name', 'Unknown')
                course_id = tool_result.get('id', 'N/A')
                return f"Course '{course_name}' created successfully with ID {course_id}. The course is ready for content."
            elif "error" in str(tool_result):
                return f"Error: {tool_result.get('error', 'Unknown error')}"
            else:
                return f"Operation completed successfully."
    
    def get_additional_usage(self):
        """Get additional usage from final response"""
        return getattr(self, '_additional_usage', None)