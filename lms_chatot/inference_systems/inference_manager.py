from typing import List, Dict, Any, Optional
from .openai_inference import OpenAIInference
from .bedrock_inference import BedrockInference
from .gemini_inference import GeminiInference

class InferenceManager:
    """Manages multiple inference systems with automatic fallback"""
    
    def __init__(self):
        self.systems = [
            OpenAIInference(),
            BedrockInference(),
            GeminiInference()
        ]
        self.active_system = self._get_active_system()
    
    def _get_active_system(self):
        """Get the first available inference system"""
        for system in self.systems:
            if system.is_available():
                return system
        return None
    
    def is_available(self) -> bool:
        """Check if any inference system is available"""
        return self.active_system is not None
    
    def call_with_tools(self, system_prompt: str, messages: List[Dict], tools: List[Dict]) -> Dict[str, Any]:
        """Call the active inference system with tools"""
        if not self.active_system:
            return {"content": "No AI inference system configured. Please set OPENAI_API_KEY or AWS credentials.", "tool_used": False}
        
        try:
            result = self.active_system.call_with_tools(system_prompt, messages, tools)
            result["inference_system"] = self.active_system.name
            return result
        except Exception as e:
            return {"content": f"Inference error: {str(e)}", "tool_used": False}
    
    def get_final_response(self, messages: List[Dict], tool_result: Dict, tool_id: str) -> str:
        """Get final response after tool execution"""
        if hasattr(self.active_system, 'get_final_response'):
            return self.active_system.get_final_response(messages, tool_result, tool_id)
        return "Tool executed successfully."
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all inference systems"""
        return {
            "available_systems": [sys.get_status() for sys in self.systems],
            "active_system": self.active_system.name if self.active_system else None
        }