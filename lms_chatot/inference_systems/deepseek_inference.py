# DeepSeek Inference (OpenAI-compatible)
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple

from openai import OpenAI
from dotenv import load_dotenv
from .base_inference import BaseInference

load_dotenv()
logger = logging.getLogger(__name__)


class DeepSeekInference(BaseInference):
    """
    DeepSeek Agent-capable Inference Wrapper
    - OpenAI-compatible API
    - Tool calling
    - Resume-safe friendly
    """

    DEFAULT_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    MAX_TOKENS = 4096
    MAX_STEPS = 20
    IDLE_LIMIT = 3

    def __init__(self):
        self.name = self.__class__.__name__

        api_key = os.getenv("DEEPSEEK_API_KEY")
        base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

        if not api_key:
            self.client = None
            logger.error("DEEPSEEK_API_KEY not set")
            return

        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url,
        )

        self._final_usage: Optional[Dict[str, int]] = None

        # Execution state is external & explicit (important)
        self.execution_state: Dict[str, Any] = {
            "course_id": None,
            "modules": {},
            "pages": {},
            "assignments": {},
            "quizzes": {},
            "completed_steps": set(),
        }

    # --------------------------------------------------
    # Availability
    # --------------------------------------------------

    def is_available(self) -> bool:
        return self.client is not None

    # --------------------------------------------------
    # SINGLE STEP (Backward compatibility)
    # --------------------------------------------------

    def call_with_tools(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        force_tool: Optional[str] = None,
    ) -> Dict[str, Any]:

        if not self.client:
            return {"content": "DeepSeek not configured.", "needs_tool": False}

        normalized_tools = self._normalize_tools(tools)

        payload = {
            "model": self.DEFAULT_MODEL,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "max_tokens": self.MAX_TOKENS,
        }

        if normalized_tools:
            payload["tools"] = normalized_tools
            payload["tool_choice"] = force_tool or "auto"

        try:
            response = self.client.chat.completions.create(**payload)
        except Exception as e:
            logger.error(f"DeepSeek call failed: {e}")
            return {"content": "Error contacting DeepSeek.", "needs_tool": False}

        choice = response.choices[0]
        msg = choice.message

        # Tool call?
        if getattr(msg, "tool_calls", None):
            tool_call = msg.tool_calls[0]
            args = json.loads(tool_call.function.arguments or "{}")

            return {
                "needs_tool": True,
                "tool_name": tool_call.function.name,
                "tool_args": args,
                "usage": self._usage_to_dict(response),
            }

        return {
            "needs_tool": False,
            "content": msg.content or "",
            "usage": self._usage_to_dict(response),
        }

    # --------------------------------------------------
    # AGENT LOOP (SAFE, NO FSM ASSUMPTIONS)
    # --------------------------------------------------

    def run_agent(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        tool_executor,
    ) -> Dict[str, Any]:

        if not self.client:
            return {"content": "DeepSeek not configured."}

        normalized_tools = self._normalize_tools(tools)

        conversation = [{"role": "system", "content": system_prompt}] + messages
        idle_steps = 0

        for step in range(self.MAX_STEPS):
            payload = {
                "model": self.DEFAULT_MODEL,
                "messages": conversation,
                "max_tokens": self.MAX_TOKENS,
            }

            if normalized_tools:
                payload["tools"] = normalized_tools
                payload["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**payload)
            self._final_usage = self._usage_to_dict(response)

            msg = response.choices[0].message

            # ---------------- TOOL CALL ----------------
            if getattr(msg, "tool_calls", None):
                idle_steps = 0
                tc = msg.tool_calls[0]
                tool_name = tc.function.name
                tool_args = json.loads(tc.function.arguments or "{}")

                tool_result = tool_executor(
                    tool_name=tool_name,
                    tool_args=tool_args,
                    state=self.execution_state,
                )

                self._update_execution_state(tool_name, tool_result)

                conversation.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(tool_result),
                })
                continue

            # ---------------- FINAL ----------------
            if msg.content:
                return {
                    "content": msg.content,
                    "usage": self._final_usage,
                    "state": self.execution_state,
                    "status": "completed",
                }

            idle_steps += 1
            if idle_steps >= self.IDLE_LIMIT:
                break

        return {
            "content": "Partial progress made. Would you like to continue?",
            "usage": self._final_usage,
            "state": self.execution_state,
            "status": "paused",
        }

    # --------------------------------------------------
    # TOOL NORMALIZATION (CRITICAL)
    # --------------------------------------------------

    def _normalize_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []

        for tool in tools:
            if tool.get("type") == "function":
                normalized.append(tool)
                continue

            if "function" in tool:
                fn = tool["function"]
                normalized.append({
                    "type": "function",
                    "function": {
                        "name": fn["name"],
                        "description": fn.get("description", ""),
                        "parameters": fn.get("parameters", {"type": "object"}),
                    },
                })
                continue

            normalized.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("input_schema", {"type": "object"}),
                },
            })

        return normalized

    # --------------------------------------------------
    # STATE UPDATE
    # --------------------------------------------------

    def _update_execution_state(self, tool_name: str, result: Dict[str, Any]):
        if not isinstance(result, dict):
            return

        if "course_id" in result:
            self.execution_state["course_id"] = result["course_id"]

        if "module_id" in result:
            self.execution_state["modules"][result.get("name")] = result["module_id"]

        if "page_id" in result:
            self.execution_state["pages"][result.get("title")] = result["page_id"]

        if "assignment_id" in result:
            self.execution_state["assignments"][result.get("name")] = result["assignment_id"]

        if "quiz_id" in result:
            self.execution_state["quizzes"][result.get("title")] = result["quiz_id"]

    # --------------------------------------------------
    # USAGE NORMALIZATION
    # --------------------------------------------------

    @staticmethod
    def _usage_to_dict(resp) -> Dict[str, int]:
        u = resp.usage or {}
        return {
            "model": resp.model,
            "input_tokens": u.prompt_tokens or 0,
            "output_tokens": u.completion_tokens or 0,
            "total_tokens": u.total_tokens or 0,
        }
