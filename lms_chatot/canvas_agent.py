import json
import logging
import re
from typing import Dict, Any, List, Optional

from canvas_integration import CanvasLMS
from canvas_tools import CanvasTools
from usage_tracker import usage_tracker
from inference_systems.openai_inference import OpenAIInference
from intent_permission_checker import IntentPermissionChecker
# from inference_systems.deepseek_inference import DeepSeekInference


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
        self.permission_checker = IntentPermissionChecker()
        # self.inference = DeepSeekInference()

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
            
            # 1. Handle Pending Clarifications
            if pending_tool and pending_tool_def:
                return self._handle_pending_tool(
                    user_message, 
                    pending_tool, 
                    pending_tool_def, 
                    canvas_tools, 
                    conversation_history
                )
            
            # 2. Handle New Request
            return self._handle_new_request(
                user_message,
                conversation_history,
                available_tools,
                canvas_tools
            )

        except Exception as exc:
            logger.error(f"Canvas agent error: {exc}", exc_info=True)
            return {
                "content": "I encountered an error while processing your request. Please try again.",
                "tool_used": False,
            }

    # ------------------------------------------------------------------
    # Handlers
    # ------------------------------------------------------------------

    def _handle_pending_tool(
        self,
        user_message: str,
        pending_tool: str,
        pending_tool_def: Dict[str, Any],
        canvas_tools: CanvasTools,
        conversation_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Resume a pending tool execution with new user input"""
        tool_result = self._execute_tool(
            user_message, 
            pending_tool, 
            pending_tool_def, 
            canvas_tools, 
            conversation_history
        )
        
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

    def _handle_new_request(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        available_tools: List[Dict[str, Any]],
        canvas_tools: CanvasTools
    ) -> Dict[str, Any]:
        """Process a fresh user message using run_agent for multi-step workflows"""
        
        # Check permissions before calling LLM
        available_tool_names = {t["function"]["name"] for t in available_tools}
        permission_check = self.permission_checker.check_permission(
            user_message,
            available_tool_names,
            self.user_role
        )
        
        if not permission_check["allowed"]:
            return {
                "content": permission_check["message"],
                "tool_used": False,
                "permission_denied": True,
            }
        
        # Build context-aware system prompt
        context_info = self._build_context_prompt()
        
        system_prompt = (
            f"You are a Canvas LMS assistant for a {self.user_role or 'user'}.\n"
            f"{context_info}"
            "You have access to Canvas API tools. ALWAYS use tools to perform Canvas operations.\n\n"
            "CRITICAL CHAINING RULES:\n"
            "1. After creating a resource (course, module, etc.), use the returned ID for subsequent operations\n"
            "2. Example: create_course returns course_id → use that course_id to create_module\n"
            "3. Example: create_module returns module_id → use that module_id to add_page_to_module\n"
            "4. NEVER call list/search tools to find IDs you just created - use the IDs from tool results\n\n"
            f"ROLE-BASED RESTRICTIONS:\n"
            f"- You are assisting a {self.user_role}. Only suggest actions they can perform.\n"
            f"- Students CANNOT create courses, add users, or perform administrative tasks.\n"
            f"- Only suggest operations available in your tool list.\n\n"
            f"STUDENT ASSISTANCE (if role=student):\n"
            f"- Help explain course content, assignments, and learning materials in simple terms\n"
            f"- Use get_assignment + get_rubric to provide detailed assignment help with grading criteria\n"
            f"- Use get_course_progress + get_student_analytics for personalized learning insights\n"
            f"- Use get_page_content to understand current page context and provide relevant help\n"
            f"- Use post_discussion_reply to help draft thoughtful discussion posts\n"
            f"- Use get_upcoming_assignments to create study plans and deadline reminders\n"
            f"- Provide step-by-step guidance, study tips, and learning strategies\n\n"
            "When user requests creating a course but does not provide a course_code, generate one by uppercasing the name, removing non-alphanumeric characters, and truncating to 10 characters.\n"
            "For complex requests, call tools sequentially using IDs from previous results."
        )
        
        messages = [
            {"role": "system" if m.get("role") == "tool" else m.get("role", "user"), "content": m.get("content", "")}
            for m in (conversation_history or [])[-5:]
        ]
        messages.append({"role": "user", "content": user_message})
        
        # Use run_agent for full agentic workflow
        def tool_executor(tool_name, tool_args, state):
            result = canvas_tools.execute_tool(tool_name, tool_args)
            return result
        
        result = self.inference.run_agent(
            system_prompt,
            messages,
            available_tools,
            tool_executor
        )
        
        self._track_usage(result, tool_used=True)
        return {
            "content": result.get("content", "Operation completed."),
            "tool_used": True,
            "inference_system": "OpenAI",
            "state": result.get("state", {}),
            "usage": result.get("usage", {}),
        }



    def _set_user_context(self, role: Optional[str], info: Optional[Dict[str, Any]]):
        if role:
            self.user_role = role
        if info:
            self.user_info = info

    def _build_context_prompt(self) -> str:
        """Build context-aware prompt based on current page"""
        context_parts = []
        
        # Course context
        if self.user_info.get("course_id"):
            course_name = self.user_info.get("course_name", "this course")
            context_parts.append(f"User is currently viewing course '{course_name}' (ID: {self.user_info['course_id']}).")
            context_parts.append("When user says 'this course' or uses relative terms, use this course_id.")
        
        # Assignment context
        if self.user_info.get("assignment_id"):
            context_parts.append(f"User is viewing assignment ID {self.user_info['assignment_id']}.")
            context_parts.append("When user refers to 'this assignment', use this assignment_id.")
        
        # Quiz context
        if self.user_info.get("quiz_id"):
            context_parts.append(f"User is viewing quiz ID {self.user_info['quiz_id']}.")
            context_parts.append("When user refers to 'this quiz', use this quiz_id.")
        
        # Module context
        if self.user_info.get("module_id"):
            context_parts.append(f"User is viewing module ID {self.user_info['module_id']}.")
            context_parts.append("When user refers to 'this module', use this module_id.")
        
        # Discussion context
        if self.user_info.get("discussion_id"):
            context_parts.append(f"User is viewing discussion ID {self.user_info['discussion_id']}.")
            context_parts.append("When user refers to 'this discussion', use this discussion_id.")
        
        # Page context - detect if user is on a specific page
        current_page = self.user_info.get("current_page", "")
        if "/pages/" in current_page:
            page_url = current_page.split("/pages/")[-1].split("?")[0]
            context_parts.append(f"User is viewing a content page with URL slug: '{page_url}'.")
            context_parts.append("CRITICAL: When user says 'update this page', 'update current page', or 'update the page', they mean THIS specific page.")
            context_parts.append(f"To update this page, use update_page tool with course_id={self.user_info.get('course_id')} and page_url='{page_url}'.")
            context_parts.append("DO NOT use update_course when user wants to update a page.")
            context_parts.append("DO NOT create a new page when user wants to update the current page.")
            context_parts.append("ALWAYS ask what content they want to add/change before calling update_page.")
        
        if context_parts:
            return "CURRENT CONTEXT:\n" + "\n".join(context_parts) + "\n\n"
        return ""

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
                if m.get("raw_tool_data"):
                    tool_data_str = json.dumps(m['raw_tool_data'])
                    messages.append({"role": "system", "content": f"Tool data: {tool_data_str}"})
            
            messages.append({"role": "user", "content": user_message})
            
            result = self.inference.call_with_tools(
                system_prompt,
                messages,
                [tool_def],
            )

            if result.get("missing_args"):
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
                
                tool_result = canvas_tools.execute_tool(
                    result.get("tool_name", tool_name),
                    tool_args,
                )
                self._track_usage(result, tool_used=True, tool_name=tool_name)
                return tool_result

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
            "Convert this result into a helpful, user-friendly response. Be conversational and summarize clearly."
            "While summarizing do mention the 'id' in an understanding way."
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
