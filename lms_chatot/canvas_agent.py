import json
import logging
from typing import Dict, Any, List, Optional

from canvas_integration import CanvasLMS
from canvas_tools import CanvasTools
from analytics_cache import analytics_cache
from usage_tracker import usage_tracker
from inference_systems.openai_inference import OpenAIInference

logger = logging.getLogger(__name__)


class CanvasAgent:
    """
    CanvasAgent orchestrates:
    - intent classification
    - tool gating & execution
    - conversational fallback
    - analytics + usage tracking
    """

    def __init__(self, canvas_url: str, admin_canvas_token: str, as_user_id: Optional[int] = None):
        self.admin_canvas = CanvasLMS(canvas_url, admin_canvas_token)
        self.canvas = CanvasLMS(canvas_url, admin_canvas_token, as_user_id=as_user_id)

        logger.info(f"Canvas agent initialized (as_user_id={as_user_id})")

        self.user_role: Optional[str] = None
        self.user_info: Dict[str, Any] = {}

        self.inference = OpenAIInference()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_message(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        user_role: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None,
        pending_tool: Optional[str] = None,
        pending_tool_def: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        self._set_user_context(user_role, user_info)

        try:
            # Get role-based tools
            canvas_tools = CanvasTools(
                self.canvas,
                self.admin_canvas,
                self.user_role,
                self.user_info,
            )
            available_tools = CanvasTools.get_tool_definitions(self.user_role)
            print(f"[CANVAS_AGENT] Available tools for {self.user_role}: {len(available_tools)}")
            
            # If there's a pending tool from clarification, resume it
            if pending_tool and pending_tool_def:
                print(f"[CANVAS_AGENT] Resuming pending tool: {pending_tool}")
                tool_result = self._execute_tool(user_message, pending_tool, pending_tool_def, canvas_tools, conversation_history)
                
                if tool_result.get("clarification_needed"):
                    return {
                        "content": tool_result.get("content"),
                        "tool_used": False,
                        "clarification_needed": True,
                        "pending_tool": pending_tool,
                        "pending_tool_def": pending_tool_def,
                    }
                
                final_response = self._format_tool_response(user_message, tool_result, pending_tool)
                return {
                    "content": final_response,
                    "tool_used": True,
                    "tool_results": [{"function_name": pending_tool, "result": tool_result}],
                    "inference_system": "OpenAI",
                }
            
            # Multi-step workflow: Detect and execute prerequisite tools
            required_tools = self._detect_required_tools(user_message, conversation_history)
            if required_tools:
                print(f"[CANVAS_AGENT] Multi-step workflow: Required tools: {required_tools}")
                self._execute_prerequisite_tools(required_tools, canvas_tools, conversation_history)
            
            # Let OpenAI decide: use tool or conversation
            system_prompt = (
                f"You are a Canvas LMS assistant for {self.user_role or 'user'}.\n"
                "You have access to Canvas tools to fetch/modify data.\n"
                "When user mentions entities by NAME (course, module, etc), extract the ID from conversation history.\n"
                "Use tools for Canvas operations, conversation for questions/guidance.\n"
                "If ambiguous, ask clarifying questions."
            )
            
            messages = [
                {"role": m.get("role", "user"), "content": m.get("content", "")}
                for m in (conversation_history or [])[-5:]
            ]
            messages.append({"role": "user", "content": user_message})
            
            result = self.inference.call_with_tools(
                system_prompt,
                messages,
                available_tools,
            )
            
            # Tool was called
            if result.get("needs_tool"):
                tool_name = result.get("tool_name")
                tool_args = result.get("tool_args", {})
                print(f"[CANVAS_AGENT] OpenAI selected tool: {tool_name} with args: {tool_args}")
                
                # Check for missing args
                if result.get("missing_args"):
                    print(f"[CANVAS_AGENT] Missing args: {result.get('missing_args')}")
                    return {
                        "content": result.get("content"),
                        "tool_used": False,
                        "clarification_needed": True,
                        "pending_tool": tool_name,
                        "pending_tool_def": next((t for t in available_tools if t["function"]["name"] == tool_name), None),
                    }
                
                # Execute tool
                tool_result = canvas_tools.execute_tool(tool_name, tool_args)
                self._track_usage(result, tool_used=True, tool_name=tool_name)
                
                # Check if this was a prerequisite tool (list operation)
                is_prerequisite = tool_name in ["list_user_courses", "list_modules", "list_assignments", "list_users"]
                
                if is_prerequisite:
                    # Add result to history and retry with original intent
                    import json
                    conversation_history.append({
                        "role": "system",
                        "content": f"Canvas data fetched: {json.dumps(tool_result)}",
                        "raw_tool_data": tool_result
                    })
                    
                    print(f"[CANVAS_AGENT] Prerequisite tool executed, retrying with context")
                    
                    # Build enhanced prompt for second call
                    enhanced_prompt = (
                        f"You are a Canvas LMS assistant for {self.user_role or 'user'}.\n"
                        "You just fetched Canvas data. Now use it to complete the user's original request.\n"
                        "Extract IDs from the fetched data and call the appropriate tool.\n"
                        "Example: If user wants 'create module in Biology' and you have course list, find Biology's ID and call create_module."
                    )
                    
                    # Retry with updated context
                    messages = [
                        {"role": "system", "content": f"Available data: {json.dumps(tool_result)}"},
                        {"role": "user", "content": user_message}
                    ]
                    
                    result2 = self.inference.call_with_tools(enhanced_prompt, messages, available_tools)
                    
                    if result2.get("needs_tool"):
                        tool_name2 = result2.get("tool_name")
                        tool_args2 = result2.get("tool_args", {})
                        print(f"[CANVAS_AGENT] Second tool: {tool_name2} with args: {tool_args2}")
                        
                        tool_result2 = canvas_tools.execute_tool(tool_name2, tool_args2)
                        self._track_usage(result2, tool_used=True, tool_name=tool_name2)
                        
                        final_response = self._format_tool_response(user_message, tool_result2, tool_name2)
                        return {
                            "content": final_response,
                            "tool_used": True,
                            "tool_results": [
                                {"function_name": tool_name, "result": tool_result},
                                {"function_name": tool_name2, "result": tool_result2}
                            ],
                            "inference_system": "OpenAI",
                            "raw_tool_data": tool_result2,
                        }
                
                # Single tool execution
                final_response = self._format_tool_response(user_message, tool_result, tool_name)
                return {
                    "content": final_response,
                    "tool_used": True,
                    "tool_results": [{"function_name": tool_name, "result": tool_result}],
                    "inference_system": "OpenAI",
                    "raw_tool_data": tool_result,
                }
            
            # Pure conversation
            self._track_usage(result, tool_used=False)
            return {
                "content": result.get("content", "I'm here to help with Canvas LMS."),
                "tool_used": False,
                "inference_system": "OpenAI",
            }

        except Exception as exc:
            logger.error(f"Canvas agent error: {exc}", exc_info=True)
            return {
                "content": "I encountered an error while processing your request. Please try again.",
                "tool_used": False,
            }

    # ------------------------------------------------------------------
    # Multi-Step Workflow System
    # ------------------------------------------------------------------

    def _detect_required_tools(self, user_message: str, conversation_history: List[Dict[str, Any]]) -> List[str]:
        """Detect which tools need to be called as prerequisites"""
        
        required_tools = []
        
        # Check what data is already in conversation history
        has_course_list = any(msg.get("raw_tool_data", {}).get("courses") for msg in conversation_history[-5:])
        has_module_list = any(msg.get("raw_tool_data", {}).get("modules") for msg in conversation_history[-5:])
        has_assignment_list = any(msg.get("raw_tool_data", {}).get("assignments") for msg in conversation_history[-5:])
        
        message_lower = user_message.lower()
        
        # Detect if user references entities by name (not ID)
        import re
        
        # Course name reference without course list
        if not has_course_list:
            course_patterns = [r'in course \w+', r'course named', r'course called', r'in the \w+ course']
            if any(re.search(pattern, message_lower) for pattern in course_patterns):
                if not re.search(r'course\s+\d+', message_lower):  # Not using course ID
                    required_tools.append("list_user_courses")
        
        # Module name reference without module list
        if not has_module_list and has_course_list:
            module_patterns = [r'in module', r'module named', r'module called']
            if any(re.search(pattern, message_lower) for pattern in module_patterns):
                if not re.search(r'module\s+\d+', message_lower):
                    required_tools.append("list_modules")
        
        # Assignment name reference without assignment list
        if not has_assignment_list and has_course_list:
            assignment_patterns = [r'assignment named', r'assignment called', r'grade.*assignment']
            if any(re.search(pattern, message_lower) for pattern in assignment_patterns):
                if not re.search(r'assignment\s+\d+', message_lower):
                    required_tools.append("list_assignments")
        
        return required_tools

    def _execute_prerequisite_tools(self, required_tools: List[str], canvas_tools: CanvasTools, conversation_history: List[Dict[str, Any]]) -> None:
        """Execute prerequisite tools and add results to conversation history"""
        
        import json
        
        for tool_name in required_tools:
            print(f"[CANVAS_AGENT] Multi-step: Executing prerequisite tool: {tool_name}")
            
            try:
                # Determine arguments based on tool
                args = {}
                if tool_name in ["list_modules", "list_assignments"]:
                    # Need course_id from previous course list
                    for msg in reversed(conversation_history):
                        courses = msg.get("raw_tool_data", {}).get("courses", [])
                        if courses:
                            args["course_id"] = courses[0]["id"]  # Use first course
                            break
                
                result = canvas_tools.execute_tool(tool_name, args)
                
                # Add to conversation history
                conversation_history.append({
                    "role": "system",
                    "content": f"Fetched data: {json.dumps(result)[:500]}",
                    "raw_tool_data": result
                })
                
            except Exception as e:
                print(f"[CANVAS_AGENT] Prerequisite tool {tool_name} failed: {e}")

    # ------------------------------------------------------------------
    # Context & Analytics
    # ------------------------------------------------------------------

    def _set_user_context(self, role: Optional[str], info: Optional[Dict[str, Any]]):
        if role:
            self.user_role = role
        if info:
            self.user_info = info

    def _generate_chat_analytics(self) -> Dict[str, Any]:
        try:
            canvas_user_id = self.user_info.get("canvas_user_id")
            cached = analytics_cache.get_cached_analytics(self.user_role, canvas_user_id)
            if cached:
                return cached

            canvas_client = self.admin_canvas if self.user_role == "admin" else self.canvas
            analytics = analytics_cache.get_quick_analytics(canvas_client, self.user_role)

            if self.user_role == "student":
                analytics.setdefault("quick_actions", []).extend([
                    {"action": "learning_plan", "label": "📋 Learning Plan", "prompt": "Generate my learning plan"},
                    {"action": "progress_tracker", "label": "📊 Progress Tracker", "prompt": "Show my progress"},
                    {"action": "study_recommendations", "label": "💡 Study Tips", "prompt": "Get study recommendations"},
                    {"action": "assignment_prioritizer", "label": "⏰ Prioritize Tasks", "prompt": "Help me prioritize assignments"},
                ])

            analytics_cache.cache_analytics(self.user_role, analytics, canvas_user_id)
            return analytics

        except Exception as exc:
            logger.warning(f"Analytics generation failed: {exc}")
            return {"quick_actions": []}

# ------------------------------------------------------------------
    # Tool Execution
    # ------------------------------------------------------------------

    def _execute_tool(
        self,
        user_message: str,
        tool_name: str,
        tool_def: Dict[str, Any],
        canvas_tools: CanvasTools,
        conversation_history: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        system_prompt = (
            f"Extract parameters from the user's message for {tool_name}.\n"
            "Extract only parameters explicitly mentioned by the user.\n"
            "If a required parameter is not mentioned, leave it empty or null.\n"
            "If this is a follow-up message providing missing information, extract those values.\n"
            "CRITICAL: If user mentions a course by name, find its exact 'id' from the Tool data in conversation history.\n"
            "Example: 'Test Python One' -> look for course with name='Test Python One' in Tool data -> use its 'id' field."
        )

        try:
            # Include conversation history with tool data for context-aware extraction
            messages = []
            for m in (conversation_history or [])[-5:]:
                messages.append({"role": m.get("role", "user"), "content": m.get("content", "")})
                # Include raw tool data if available
                if m.get("raw_tool_data"):
                    import json
                    tool_data_str = json.dumps(m['raw_tool_data'])
                    print(f"[CANVAS_AGENT] Including tool data in context: {tool_data_str[:200]}...")
                    messages.append({"role": "system", "content": f"Tool data: {tool_data_str}"})
            
            messages.append({"role": "user", "content": user_message})
            print(f"[CANVAS_AGENT] Total messages for tool extraction: {len(messages)}")
            
            result = self.inference.call_with_tools(
                system_prompt,
                messages,
                [tool_def],
                force_tool=tool_name,
            )
            print(f"[CANVAS_AGENT] Inference result for tool {tool_name}: needs_tool={result.get('needs_tool')}, has_args={bool(result.get('tool_args'))}")

            # Check if clarification is needed - use general conversation instead
            if result.get("missing_args"):
                print(f"[CANVAS_AGENT] Missing required args: {result.get('missing_args')} - using conversational mode")
                # Use general conversation with context about the tool intent
                context_prompt = (
                    f"User wants to {tool_name.replace('_', ' ')} but needs to provide: {', '.join(result.get('missing_args', []))}.\n"
                    "Ask them conversationally for this information."
                )
                conv_result = self.inference.call_with_tools(
                    context_prompt,
                    [{"role": "user", "content": user_message}],
                    [],
                )
                return {
                    "clarification_needed": True,
                    "content": conv_result.get("content"),
                    "pending_tool": tool_name,
                    "pending_tool_def": tool_def,
                }

            if result.get("needs_tool"):
                tool_args = result.get("tool_args", {})
                print(f"[CANVAS_AGENT] Executing tool {tool_name} with args: {tool_args}")
                
                # Check for missing required args
                if result.get("missing_args"):
                    print(f"[CANVAS_AGENT] Missing required args: {result.get('missing_args')}")
                    return {
                        "content": result.get("prompt_user", "Please provide more information."),
                        "tool_used": False,
                        "missing_args": result.get("missing_args"),
                    }
                
                tool_result = canvas_tools.execute_tool(
                    result.get("tool_name", tool_name),
                    tool_args,
                )
                print(f"[CANVAS_AGENT] Tool call result: {tool_result}")
                self._track_usage(result, tool_used=True, tool_name=tool_name)
                return tool_result

            print(f"[CANVAS_AGENT] Tool {tool_name} execution failed - needs_tool=False")
            return {"error": "Tool execution failed"}
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return {"error": "Tool execution failed"}

    # ------------------------------------------------------------------
    # Tool Result Formatting
    # ------------------------------------------------------------------

    def _format_tool_response(
        self,
        user_message: str,
        tool_result: Dict[str, Any],
        tool_name: str,
    ) -> str:

        # Sanitized system prompt without exposing internal details
        system_prompt = (
            "Convert this result into a helpful, user-friendly response. "
            "Be conversational and summarize clearly."
        )

        try:
            result = self.inference.call_with_tools(
                system_prompt,
                [{"role": "user", "content": json.dumps(tool_result)}],
                [],
            )
            return result.get("content", "Operation completed successfully.")
        except Exception as e:
            logger.error(f"Tool response formatting failed: {e}")
            return "Operation completed successfully."

    # ------------------------------------------------------------------
    # Usage Tracking
    # ------------------------------------------------------------------

    def _track_usage(self, result: Dict[str, Any], tool_used: bool, tool_name: Optional[str] = None):
        try:
            usage = result.get("usage", {})
            usage_tracker.log_usage(
                user_id=self.user_info.get("canvas_user_id", 0),
                user_role=self.user_role or "unknown",
                inference_system=result.get("inference_system", "OpenAI"),
                model_name=usage.get("model", "unknown"),
                input_tokens=usage.get("input_tokens", 0),
                output_tokens=usage.get("output_tokens", 0),
                tool_used=tool_used,
                tool_name=tool_name,
            )
        except Exception as exc:
            logger.warning(f"Usage tracking failed: {exc}")

    # ------------------------------------------------------------------

    def get_inference_status(self) -> Dict[str, str]:
        return {"active_system": "OpenAI", "status": "available"}
