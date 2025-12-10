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
        """Call Gemini API with function calling"""
        # Convert tools to Gemini format
        gemini_tools = []
        for tool in tools:
            gemini_tool = {
                "function_declarations": [{
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["input_schema"]
                }]
            }
            gemini_tools.append(gemini_tool)
        
        # Prepare prompt
        user_message = messages[-1]["content"] if messages else ""
        full_prompt = f"{system_prompt}\n\nUser: {user_message}"
        
        try:
            # Call Gemini with tools
            model_with_tools = genai.GenerativeModel('gemini-pro', tools=gemini_tools)
            response = model_with_tools.generate_content(full_prompt)
            
            # Check for function calls
            if response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'function_call'):
                        function_call = part.function_call
                        return {
                            "needs_tool": True,
                            "tool_name": function_call.name,
                            "tool_args": dict(function_call.args),
                            "function_call": function_call
                        }
            
            # No tool use
            return {
                "needs_tool": False,
                "content": response.text
            }
            
        except Exception as e:
            return {
                "needs_tool": False,
                "content": f"Gemini error: {str(e)}"
            }
    
    def get_final_response(self, messages: list, tool_result: dict, function_call) -> str:
        """Get final response after tool execution"""
        try:
            # Create function response
            function_response = genai.protos.Part(
                function_response=genai.protos.FunctionResponse(
                    name=function_call.name,
                    response={"result": json.dumps(tool_result)}
                )
            )
            
            # Get final response
            response = self.model.generate_content([
                genai.protos.Content(parts=[
                    genai.protos.Part(function_call=function_call),
                    function_response
                ])
            ])
            
            return response.text
            
        except Exception as e:
            return f"Tool executed successfully: {tool_result}"