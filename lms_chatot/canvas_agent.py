from canvas_integration import CanvasLMS
from inference_systems.inference_manager import InferenceManager
from analytics_cache import analytics_cache
from canvas_tools import CanvasTools
from usage_tracker import usage_tracker

class CanvasAgent:
    def __init__(self, canvas_url: str, admin_canvas_token: str, user_id: int = None):
        self.admin_canvas = CanvasLMS(canvas_url, admin_canvas_token)
        self.canvas = CanvasLMS(canvas_url, admin_canvas_token, as_user_id=user_id)
        
        print(f"[CANVAS_AGENT] Using admin token with as_user_id={user_id}")
        
        self.user_role = None
        self.user_info = None
        
        # Use OpenAI inference system
        from inference_systems.openai_inference import OpenAIInference
        self.inference_system = OpenAIInference()
        
    def process_message(self, user_message: str, conversation_history: list, user_role: str = None, user_info: dict = None) -> dict:
        if user_role:
            self.user_role = user_role
        if user_info:
            self.user_info = user_info
            
        # Get Canvas tools (universal for all inference systems)
        tools = CanvasTools.get_tool_definitions(self.user_role)
        
        # Initialize Canvas tools handler
        canvas_tools = CanvasTools(self.canvas, self.admin_canvas, self.user_role, self.user_info)
            
        system_prompt = f"""Canvas LMS assistant for {self.user_role or 'user'}.

Rules:
- Use tools for Canvas operations
- Maintain conversation context
- Be precise and helpful
- Infer intent from context"""
        
        # Build context-aware messages including recent conversation
        context_messages = []
        if conversation_history:
            # Include last few messages for context
            for msg in conversation_history[-4:]:
                context_messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        
        context_messages.append({"role": "user", "content": user_message})
        messages = context_messages
        
        try:
            # Use multi-model system
            result = self.inference_system.call_with_tools(system_prompt, messages, tools)
            
            # Handle tool execution
            if result.get("needs_tool"):
                tool_result = canvas_tools.execute_tool(result["tool_name"], result["tool_args"])
                
                # Get conversational final response from OpenAI
                if hasattr(self.inference_system, 'get_final_response'):
                    try:
                        final_content = self.inference_system.get_final_response(
                            messages, tool_result, result.get("tool_call_id")
                        )
                    except Exception as e:
                        print(f"[CANVAS_AGENT] Final response error: {e}")
                        # Fallback to basic response
                        final_content = "Canvas operation completed"
                else:
                    final_content = self._format_tool_result(result["tool_name"], tool_result)
                
                # Track usage with tool execution
                self._track_usage(result, True, result["tool_name"])
                
                # Generate dynamic analytics for chat
                chat_analytics = self._generate_chat_analytics()
                
                return {
                    "content": final_content,
                    "tool_used": True,
                    "tool_results": [{"function_name": result["tool_name"], "result": tool_result}],
                    "inference_system": result.get("inference_system"),
                    "analytics": chat_analytics
                }
            
            # Track usage without tool execution
            self._track_usage(result, False)
            
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
    
    def _track_usage(self, result: dict, tool_used: bool, tool_name: str = None):
        """Track AI model usage and tokens"""
        try:
            usage_data = result.get("usage", {})
            canvas_user_id = self.user_info.get('canvas_user_id') if self.user_info else 0
            
            usage_tracker.log_usage(
                user_id=canvas_user_id,
                user_role=self.user_role or "unknown",
                inference_system=result.get("inference_system", "unknown"),
                model_name=usage_data.get("model", "unknown"),
                input_tokens=usage_data.get("input_tokens", 0),
                output_tokens=usage_data.get("output_tokens", 0),
                tool_used=tool_used,
                tool_name=tool_name
            )
        except Exception as e:
            print(f"[USAGE] Failed to track usage: {e}")
    

    
    def get_inference_status(self):
        """Get status of inference systems"""
        return {"active_system": "OpenAI", "status": "available"}