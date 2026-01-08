import json
import logging
import re
from typing import Dict, Any, List, Optional

from canvas_integration import CanvasLMS
from canvas_tools import CanvasTools
from usage_tracker import usage_tracker
from inference_systems.openai_inference import OpenAIInference
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
        
        system_prompt = (
            f"You are a Canvas LMS assistant for {self.user_role or 'user'}.\n"
            "Execute Canvas operations step-by-step using available tools.\n"
            "For complex requests (e.g., 'create course with modules'), call tools sequentially.\n"
            "Use conversation history to reference created entities by their IDs.\n"
            "Only respond with text when all operations are complete."
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
