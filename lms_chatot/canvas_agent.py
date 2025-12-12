from canvas_integration import CanvasLMS
from inference_systems.inference_manager import InferenceManager
from analytics_cache import analytics_cache
from canvas_tools import CanvasTools

class CanvasAgent:
    def __init__(self, canvas_url: str, canvas_token: str, user_id: int = None):
        self.canvas = CanvasLMS(canvas_url, canvas_token, as_user_id=user_id)
        self.admin_canvas = CanvasLMS(canvas_url, canvas_token)
        self.user_role = None
        self.user_info = None
        
        # Initialize plug-and-play inference manager
        self.inference_manager = InferenceManager()
        
    def process_message(self, user_message: str, conversation_history: list, user_role: str = None, user_info: dict = None) -> dict:
        if user_role:
            self.user_role = user_role
        if user_info:
            self.user_info = user_info
            
        # Get Canvas tools (universal for all inference systems)
        tools = CanvasTools.get_tool_definitions(self.user_role)
        
        # Initialize Canvas tools handler
        canvas_tools = CanvasTools(self.canvas, self.admin_canvas, self.user_role, self.user_info)
            
        system_prompt = f"""You are a Canvas LMS assistant. User role: {self.user_role or 'unknown'}.

Rules:
1. Always use tools to get real Canvas data
2. Never make up course IDs or data
3. Be helpful and conversational
4. If user asks about courses, call list_courses first

For students, you have access to enhanced features:
- Learning Plan Generator
- Progress Tracker
- Study Recommendations
- Assignment Prioritizer
- Learning Analytics
- Study Buddy Suggestions"""
        
        messages = [{"role": "user", "content": user_message}]
        
        try:
            # Call inference manager (automatically selects best available system)
            result = self.inference_manager.call_with_tools(system_prompt, messages, tools)
            
            # Handle tool execution
            if result.get("needs_tool"):
                tool_result = canvas_tools.execute_tool(result["tool_name"], result["tool_args"])
                
                # Get final response from inference system
                if hasattr(self.inference_manager.active_system, 'get_final_response'):
                    final_content = self.inference_manager.get_final_response(
                        messages, tool_result, result.get("tool_call_id") or result.get("tool_use_id") or result.get("response_text")
                    )
                else:
                    final_content = f"Executed {result['tool_name']}: {tool_result}"
                
                # Generate dynamic analytics for chat
                chat_analytics = self._generate_chat_analytics()
                
                return {
                    "content": final_content,
                    "tool_used": True,
                    "tool_results": [{"function_name": result["tool_name"], "result": tool_result}],
                    "inference_system": result.get("inference_system"),
                    "analytics": chat_analytics
                }
            
            # Generate dynamic analytics for chat
            chat_analytics = self._generate_chat_analytics()
            
            return {
                "content": result["content"],
                "tool_used": False,
                "inference_system": result.get("inference_system"),
                "analytics": chat_analytics
            }
            
        except Exception as e:
            return {"content": f"Error: {str(e)}", "tool_used": False}
    

    
    def _generate_chat_analytics(self):
        """Generate lightweight analytics for chat interface"""
        try:
            # Check cache first
            cached = analytics_cache.get_cached_analytics(self.user_role, self.user_info.get('canvas_user_id') if self.user_info else None)
            if cached:
                return cached
            
            # Generate fresh analytics with student features
            canvas_client = self.canvas if self.user_role != "admin" else self.admin_canvas
            analytics = analytics_cache.get_quick_analytics(canvas_client, self.user_role)
            
            # Add student-specific quick actions
            if self.user_role == "student":
                analytics["quick_actions"].extend([
                    {"action": "learning_plan", "label": "📋 Learning Plan", "prompt": "Generate my learning plan"},
                    {"action": "progress_tracker", "label": "📊 Progress Tracker", "prompt": "Show my progress"},
                    {"action": "study_recommendations", "label": "💡 Study Tips", "prompt": "Get study recommendations"},
                    {"action": "assignment_prioritizer", "label": "⏰ Prioritize Tasks", "prompt": "Help me prioritize assignments"}
                ])
            
            # Cache the result
            analytics_cache.cache_analytics(self.user_role, analytics, self.user_info.get('canvas_user_id') if self.user_info else None)
            
            return analytics
        except Exception as e:
            return {"error": str(e), "quick_actions": []}
    
    def get_inference_status(self):
        """Get status of inference systems"""
        return self.inference_manager.get_status()