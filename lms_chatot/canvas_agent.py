import json
from canvas_integration import CanvasLMS
from analytics_cache import analytics_cache
from canvas_tools import CanvasTools
from usage_tracker import usage_tracker
from intent_classifier import IntentClassifier
from inference_systems.openai_inference import OpenAIInference

class CanvasAgent:
    def __init__(self, canvas_url: str, admin_canvas_token: str, user_id: int = None):
        self.admin_canvas = CanvasLMS(canvas_url, admin_canvas_token)
        self.canvas = CanvasLMS(canvas_url, admin_canvas_token, as_user_id=user_id)
        
        print(f"[CANVAS_AGENT] Using admin token with as_user_id={user_id}")
        
        self.user_role = None
        self.user_info = None
        
        # Use OpenAI inference system and intent classifier
        self.inference_system = OpenAIInference()
        self.intent_classifier = IntentClassifier()
        
    def process_message(self, user_message: str, conversation_history: list, user_role: str = None, user_info: dict = None) -> dict:
        if user_role:
            self.user_role = user_role
        if user_info:
            self.user_info = user_info
            
        try:
            # Step 1: Intent Classification (NO TOOLS)
            intent_data = self.intent_classifier.classify_intent(user_message)
            print(f"[CANVAS_AGENT] Intent: {intent_data}")
            
            # Step 2: Tool Gating (CODE CONTROLLED)
            should_use_tool = self.intent_classifier.should_use_tool(intent_data)
            
            if not should_use_tool:
                # Fallback: Conversational response
                return self._handle_general_question(user_message, conversation_history)
            
            # Step 3: Get tools for specific intent
            intent = intent_data.get("intent")
            tools = self.intent_classifier.get_tools_for_intent(intent, self.user_role)
            
            if not tools:
                return self._handle_general_question(user_message, conversation_history)
            
            # Step 4: Tool Argument Generation (FORCED EXECUTION)
            canvas_tools = CanvasTools(self.canvas, self.admin_canvas, self.user_role, self.user_info)
            tool_name = tools[0]["function"]["name"]
            
            # Force tool execution with specific tool
            tool_result = self._execute_forced_tool(user_message, tool_name, tools[0], canvas_tools)
            
            # Step 5: Response Formatting
            final_response = self._format_tool_response(user_message, tool_result, tool_name)
            
            chat_analytics = self._generate_chat_analytics()
            
            return {
                "content": final_response,
                "tool_used": True,
                "tool_results": [{"function_name": tool_name, "result": tool_result}],
                "inference_system": "OpenAI",
                "analytics": chat_analytics,
                "intent": intent_data
            }
            
        except Exception as e:
            print(f"[CANVAS_AGENT] Error: {e}")
            return {"content": f"I encountered an error processing your request. Please try again.", "tool_used": False}
    

    
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
    

    
    def _handle_general_question(self, user_message: str, conversation_history: list) -> dict:
        """Handle non-Canvas questions conversationally"""
        system_prompt = f"You are a helpful Canvas LMS assistant for {self.user_role or 'user'}. Answer questions about Canvas LMS or provide general assistance."
        
        context_messages = []
        if conversation_history:
            for msg in conversation_history[-3:]:
                context_messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        
        context_messages.append({"role": "user", "content": user_message})
        
        result = self.inference_system.call_with_tools(system_prompt, context_messages, [])
        self._track_usage(result, False)
        
        return {
            "content": result.get("content", "I'm here to help with Canvas LMS."),
            "tool_used": False,
            "inference_system": "OpenAI",
            "analytics": self._generate_chat_analytics()
        }
    
    def _execute_forced_tool(self, user_message: str, tool_name: str, tool_def: dict, canvas_tools: CanvasTools) -> dict:
        """Execute tool with forced selection and argument generation"""
        system_prompt = f"""You must call the {tool_name} function with appropriate arguments based on the user request.
Do not provide text responses - only call the function with proper arguments."""
        
        messages = [{"role": "user", "content": user_message}]
        
        # Force specific tool execution
        result = self.inference_system.call_with_tools(
            system_prompt, 
            messages, 
            [tool_def],
            force_tool=tool_name
        )
        
        if result.get("needs_tool"):
            tool_result = canvas_tools.execute_tool(result["tool_name"], result["tool_args"])
            self._track_usage(result, True, tool_name)
            return tool_result
        
        # Fallback if forced execution fails
        return {"error": "Tool execution failed"}
    
    def _format_tool_response(self, user_message: str, tool_result: dict, tool_name: str) -> str:
        """Format tool result into human-friendly response"""
        system_prompt = f"""Convert this Canvas API result into a helpful, human-friendly response for the user.
Original request: {user_message}
Tool used: {tool_name}

Rules:
- Be conversational and helpful
- Don't expose raw JSON
- Summarize key information clearly
- Don't mention technical details"""
        
        messages = [{"role": "user", "content": f"Tool result: {json.dumps(tool_result, indent=2)}"}]
        
        result = self.inference_system.call_with_tools(system_prompt, messages, [])
        return result.get("content", "Operation completed successfully.")
    
    def get_inference_status(self):
        """Get status of inference systems"""
        return {"active_system": "OpenAI", "status": "available"}