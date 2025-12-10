"""
Qwen2.5 7B Optimization Configuration for Tool Calling
Optimized parameters for enhanced performance with Canvas LMS tools
"""

import os
from typing import Dict, Any

class QwenConfig:
    """Optimized configuration for Qwen2.5 7B model"""
    
    # Model-specific optimizations
    QWEN_OPTIMIZED_PARAMS = {
        # Core generation parameters
        "temperature": float(os.getenv("OLLAMA_TEMPERATURE", "0.1")),
        "top_p": float(os.getenv("OLLAMA_TOP_P", "0.9")),
        "top_k": int(os.getenv("OLLAMA_TOP_K", "40")),
        "repeat_penalty": float(os.getenv("OLLAMA_REPEAT_PENALTY", "1.05")),
        
        # Context and prediction limits
        "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "8192")),
        "num_predict": int(os.getenv("OLLAMA_NUM_PREDICT", "512")),
        
        # Performance optimizations
        "num_thread": -1,  # Use all available CPU threads
        "num_gpu": 1,      # Use GPU if available
        "low_vram": False, # Set to True if GPU memory is limited
        
        # Qwen2.5 specific optimizations
        "mirostat": 0,     # Disable mirostat for tool calling
        "mirostat_eta": 0.1,
        "mirostat_tau": 5.0,
        
        # Stop sequences for tool calling
        "stop": ["<|im_end|>", "<|endoftext|>", "\n\nUser:", "\n\nHuman:"]
    }
    
    # Tool detection specific parameters
    TOOL_DETECTION_PARAMS = {
        "temperature": float(os.getenv("TOOL_DETECTION_TEMPERATURE", "0.05")),
        "top_p": 0.8,
        "num_predict": 50,
        "repeat_penalty": 1.1,
        "stop": ["\n", "Examples:", "User:", "Human:"]
    }
    
    # Tool execution parameters
    TOOL_EXECUTION_PARAMS = {
        "temperature": float(os.getenv("TOOL_EXECUTION_TEMPERATURE", "0.2")),
        "top_p": 0.9,
        "num_predict": 300,
        "repeat_penalty": 1.05
    }
    
    # System prompts optimized for Qwen2.5
    QWEN_SYSTEM_PROMPT = """You are a Canvas LMS assistant powered by Qwen2.5. You excel at understanding user intent and using tools effectively.

TOOL CALLING RULES:
1. Always analyze user intent first
2. Use tools when specific Canvas operations are requested
3. Provide natural, conversational responses
4. Never invent or assume data - always use real API results

RESPONSE FORMAT:
- Be concise but helpful
- Use bullet points for lists
- Include relevant IDs and details from API responses
- Ask clarifying questions when needed"""

    TOOL_DETECTION_PROMPT = """Analyze this Canvas LMS user request and determine if a tool is needed.

Available tools:
- list_courses: Show courses (keywords: list, show, view, my courses)
- create_course: Make new course (keywords: create, new, add course)
- list_modules: Show modules (keywords: modules, list modules)
- create_module: Add module (keywords: create module, add module)
- create_assignment: Make assignment (keywords: create assignment)
- create_user: Add user (keywords: create user, add student)
- list_users: Show users (keywords: list users, show users)

User request: "{user_message}"

Respond with only:
TOOL:tool_name (if tool needed)
NO_TOOL (if no tool needed)"""

    @classmethod
    def get_optimized_params(cls, operation_type: str = "general") -> Dict[str, Any]:
        """Get optimized parameters for specific operation types"""
        if operation_type == "tool_detection":
            return {**cls.QWEN_OPTIMIZED_PARAMS, **cls.TOOL_DETECTION_PARAMS}
        elif operation_type == "tool_execution":
            return {**cls.QWEN_OPTIMIZED_PARAMS, **cls.TOOL_EXECUTION_PARAMS}
        else:
            return cls.QWEN_OPTIMIZED_PARAMS
    
    @classmethod
    def get_system_prompt(cls, user_role: str = None) -> str:
        """Get role-specific system prompt"""
        role_context = ""
        if user_role == "admin":
            role_context = "\nYou have ADMINISTRATOR privileges. You can create users, courses, and manage all Canvas operations."
        elif user_role == "teacher":
            role_context = "\nYou are assisting a TEACHER. They can create courses, modules, assignments, and manage their classes."
        elif user_role == "student":
            role_context = "\nYou are assisting a STUDENT. They can view courses and modules they're enrolled in."
        
        return cls.QWEN_SYSTEM_PROMPT + role_context
    
    @classmethod
    def get_tool_detection_prompt(cls, user_message: str) -> str:
        """Get formatted tool detection prompt"""
        return cls.TOOL_DETECTION_PROMPT.format(user_message=user_message)

# Performance monitoring
class QwenPerformanceMonitor:
    """Monitor and optimize Qwen2.5 performance"""
    
    def __init__(self):
        self.response_times = []
        self.tool_usage = {}
        self.error_count = 0
    
    def log_response_time(self, operation: str, time_ms: float):
        """Log response time for performance analysis"""
        self.response_times.append({
            "operation": operation,
            "time_ms": time_ms,
            "timestamp": __import__("time").time()
        })
    
    def log_tool_usage(self, tool_name: str, success: bool):
        """Log tool usage statistics"""
        if tool_name not in self.tool_usage:
            self.tool_usage[tool_name] = {"success": 0, "failure": 0}
        
        if success:
            self.tool_usage[tool_name]["success"] += 1
        else:
            self.tool_usage[tool_name]["failure"] += 1
            self.error_count += 1
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        if not self.response_times:
            return {"status": "No data available"}
        
        avg_response_time = sum(r["time_ms"] for r in self.response_times) / len(self.response_times)
        
        return {
            "average_response_time_ms": round(avg_response_time, 2),
            "total_requests": len(self.response_times),
            "error_rate": round(self.error_count / len(self.response_times) * 100, 2),
            "tool_usage": self.tool_usage,
            "recommendations": self._get_recommendations(avg_response_time)
        }
    
    def _get_recommendations(self, avg_time: float) -> list:
        """Get performance optimization recommendations"""
        recommendations = []
        
        if avg_time > 5000:  # 5 seconds
            recommendations.append("Consider reducing num_predict parameter")
            recommendations.append("Check if GPU acceleration is enabled")
        
        if self.error_count > len(self.response_times) * 0.1:  # 10% error rate
            recommendations.append("Review tool detection logic")
            recommendations.append("Check Canvas API connectivity")
        
        return recommendations

# Global performance monitor instance
performance_monitor = QwenPerformanceMonitor()