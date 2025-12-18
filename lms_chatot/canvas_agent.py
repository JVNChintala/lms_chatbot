import json
import logging
from typing import Dict, Any, List, Optional

from canvas_integration import CanvasLMS
from canvas_tools import CanvasTools
from analytics_cache import analytics_cache
from usage_tracker import usage_tracker
from intent_classifier import IntentClassifier
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
        self.intent_classifier = IntentClassifier()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_message(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
        user_role: Optional[str] = None,
        user_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        self._set_user_context(user_role, user_info)

        try:
            intent_data = self.intent_classifier.classify_intent(user_message)
            print(f"[CANVAS_AGENT] Intent classified: {intent_data}")

            if not self.intent_classifier.should_use_tool(intent_data):
                print(f"[CANVAS_AGENT] No tool needed, handling as general question")
                return self._handle_general_question(user_message, conversation_history)

            intent = intent_data.get("intent")
            tools = self.intent_classifier.get_tools_for_intent(intent, self.user_role)
            print(f"[CANVAS_AGENT] Tools for intent '{intent}' and role '{self.user_role}': {len(tools) if tools else 0} tools")

            if not tools:
                print(f"[CANVAS_AGENT] No tools available for intent, handling as general question")
                return self._handle_general_question(user_message, conversation_history)

            tool_def = tools[0]
            tool_name = tool_def["function"]["name"]
            print(f"[CANVAS_AGENT] Selected tool: {tool_name}")

            canvas_tools = CanvasTools(
                self.canvas,
                self.admin_canvas,
                self.user_role,
                self.user_info,
            )

            tool_result = self._execute_tool(user_message, tool_name, tool_def, canvas_tools)
            print(f"[CANVAS_AGENT] Tool execution result: {type(tool_result).__name__} with keys: {list(tool_result.keys()) if isinstance(tool_result, dict) else 'N/A'}")
            final_response = self._format_tool_response(user_message, tool_result, tool_name)

            return {
                "content": final_response,
                "tool_used": True,
                "tool_results": [{"function_name": tool_name, "result": tool_result}],
                "inference_system": "OpenAI",
                "analytics": self._generate_chat_analytics(),
                "intent": intent_data,
            }

        except Exception as exc:
            logger.error(f"Canvas agent error: {exc}", exc_info=True)
            return {
                "content": "I encountered an error while processing your request. Please try again.",
                "tool_used": False,
            }

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
    # Conversational Path
    # ------------------------------------------------------------------

    def _handle_general_question(
        self,
        user_message: str,
        conversation_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        system_prompt = (
            f"You are a helpful Canvas LMS assistant for {self.user_role or 'user'}. "
            "Answer questions clearly and concisely."
        )

        messages = [
            {"role": m.get("role", "user"), "content": m.get("content", "")}
            for m in (conversation_history or [])[-3:]
        ]
        messages.append({"role": "user", "content": user_message})

        try:
            result = self.inference.call_with_tools(system_prompt, messages, [])
            self._track_usage(result, tool_used=False)
            
            analytics = {"quick_actions": []}
            try:
                analytics = self._generate_chat_analytics()
            except Exception as e:
                logger.warning(f"Analytics generation failed: {e}")

            return {
                "content": result.get("content", "I'm here to help with Canvas LMS."),
                "tool_used": False,
                "inference_system": "OpenAI",
                "analytics": analytics,
            }
        except Exception as e:
            logger.error(f"General question handling failed: {e}")
            return {
                "content": "I'm here to help with Canvas LMS.",
                "tool_used": False,
                "inference_system": "OpenAI",
                "analytics": {"quick_actions": []},
            }

    # ------------------------------------------------------------------
    # Tool Execution
    # ------------------------------------------------------------------

    def _execute_tool(
        self,
        user_message: str,
        tool_name: str,
        tool_def: Dict[str, Any],
        canvas_tools: CanvasTools,
    ) -> Dict[str, Any]:

        system_prompt = (
            f"You must call the {tool_name} function with correct arguments.\n"
            "Do not respond with text."
        )

        try:
            result = self.inference.call_with_tools(
                system_prompt,
                [{"role": "user", "content": user_message}],
                [tool_def],
                force_tool=tool_name,
            )
            print(f"[CANVAS_AGENT] Inference result for tool {tool_name}: needs_tool={result.get('needs_tool')}, has_args={bool(result.get('tool_args'))}")

            if result.get("needs_tool"):
                tool_args = result.get("tool_args", {})
                print(f"[CANVAS_AGENT] Executing tool {tool_name} with args: {tool_args}")
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
