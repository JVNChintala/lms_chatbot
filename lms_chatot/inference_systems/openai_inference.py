# OpenAI Inference (Stable GPT-5–safe Agent)
import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple

from openai import OpenAI
from dotenv import load_dotenv
from .base_inference import BaseInference

load_dotenv()
logger = logging.getLogger(__name__)


class OpenAIInference(BaseInference):
    """
    Agent-capable OpenAI Responses API wrapper
    - Stable across GPT-4o and GPT-5 models
    - Tool-first, stateful, loop-safe
    """

    DEFAULT_MODEL = "gpt-4o-mini"
    MAX_TOKENS = 5000
    MAX_STEPS = 20

    def __init__(self):
        self.name = self.__class__.__name__
        api_key = os.getenv("OPENAI_API_KEY")

        try:
            self.client = OpenAI(api_key=api_key) if api_key else None
        except Exception as e:
            logger.error(f"OpenAI init failed: {e}")
            print(f"OpenAI init failed: {e}")
            self.client = None

        self._final_usage: Optional[Dict[str, int]] = None

        # Persistent agent memory (Canvas orchestration)
        self.execution_state: Dict[str, Any] = {
            "course_id": None,
            "modules": {},
            "pages": {},
            "assignments": {},
            "quizzes": {},
        }

    def is_available(self) -> bool:
        return self.client is not None

    # ------------------------------------------------------------------
    # PUBLIC ENTRY POINT
    # ------------------------------------------------------------------

    def run_agent(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        tool_executor,
    ) -> Dict[str, Any]:
        """
        Fully stable agent loop:
        - Tool-first
        - No premature fallback
        - Terminates only on real completion
        """
        if not self.client:
            return {"content": "OpenAI not configured."}

        normalized_tools = self._normalize_tools(tools)
        conversation = [{"role": "system", "content": system_prompt}] + messages

        for step in range(self.MAX_STEPS):
            response = self._call_llm(conversation, normalized_tools)
            self._final_usage = self._to_dict(response.usage, response.model)

            tool_call = self._extract_tool_call(response)

            # 🟢 TOOL EXECUTION PATH
            if tool_call:
                tool_name, tool_args = tool_call

                tool_result = tool_executor(
                    tool_name=tool_name,
                    tool_args=tool_args,
                    state=self.execution_state,
                )

                self._update_execution_state(tool_name, tool_result)

                conversation.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": json.dumps(tool_result),
                })
                continue

            # 🟢 FINAL RESPONSE PATH
            final_text = self._extract_final_text(response)

            if final_text:
                return {
                    "content": final_text,
                    "usage": self._final_usage,
                    "state": self.execution_state,
                }

            # 🟡 GPT-5 WAIT STATE (no text, no tool)
            logger.debug(
                f"Waiting for model completion (step={step}, "
                f"output_items={len(response.output)})"
            )
            print(
                f"Waiting for model completion (step={step}, "
                f"output_items={len(response.output)})"
            )

        return {
            "content": "Automation stopped: model did not converge.",
            "usage": self._final_usage,
            "state": self.execution_state,
        }

    # ------------------------------------------------------------------
    # LLM CALL
    # ------------------------------------------------------------------

    def _call_llm(
        self,
        conversation: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
    ):
        return self.client.responses.create(
            model=self.DEFAULT_MODEL,
            input=conversation,
            tools=tools,
            max_output_tokens=self.MAX_TOKENS,
        )

    # ------------------------------------------------------------------
    # RESPONSE PARSING (GPT-5 SAFE)
    # ------------------------------------------------------------------

    def _extract_tool_call(self, response) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        GPT-5 emits tool calls without output_text — this is NORMAL
        """
        for item in response.output:
            if getattr(item, "type", None) in ("tool_call", "function_call"):
                name = getattr(item, "name", "")
                raw_args = getattr(item, "arguments", {})

                if isinstance(raw_args, str):
                    try:
                        args = json.loads(raw_args)
                    except Exception:
                        args = {}
                else:
                    args = raw_args or {}

                return name, args
        return None

    def _extract_final_text(self, response) -> Optional[str]:
        """
        Only finalize when the model explicitly emits text
        """
        if response.output_text:
            return response.output_text.strip() or None

        # Some GPT-5 variants emit text as output items
        texts = [
            getattr(item, "text", None)
            for item in response.output
            if getattr(item, "type", None) == "output_text"
        ]

        combined = "\n".join(t for t in texts if t)
        return combined.strip() or None

    # ------------------------------------------------------------------
    # STATE MANAGEMENT
    # ------------------------------------------------------------------

    def _update_execution_state(self, tool_name: str, result: Dict[str, Any]):
        if not isinstance(result, dict):
            return

        if "course_id" in result:
            self.execution_state["course_id"] = result["course_id"]

        if "module_id" in result:
            self.execution_state["modules"][result.get("name", "unnamed")] = result["module_id"]

        if "page_id" in result:
            self.execution_state["pages"][result.get("title", "untitled")] = result["page_id"]

        if "assignment_id" in result:
            self.execution_state["assignments"][result.get("name", "assignment")] = result["assignment_id"]

        if "quiz_id" in result:
            self.execution_state["quizzes"][result.get("title", "quiz")] = result["quiz_id"]

    # ------------------------------------------------------------------
    # TOOL NORMALIZATION
    # ------------------------------------------------------------------

    def _normalize_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for tool in tools:
            if "function" in tool:
                func = tool["function"]
                normalized.append({
                    "type": "function",
                    "name": func.get("name"),
                    "description": func.get("description", ""),
                    "parameters": func.get("parameters", {}),
                })
            else:
                schema = tool.get("input_schema", {})
                normalized.append({
                    "type": "function",
                    "name": tool.get("name"),
                    "description": tool.get("description", ""),
                    "parameters": {
                        "type": "object",
                        "properties": schema.get("properties", {}),
                        "required": schema.get("required", []),
                    },
                })
        return normalized

    # ------------------------------------------------------------------
    # USAGE NORMALIZATION
    # ------------------------------------------------------------------

    @staticmethod
    def _to_dict(usage_obj: Any, model: str) -> Dict[str, int]:
        if not usage_obj:
            return {"model": model, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

        if isinstance(usage_obj, dict):
            return {
                "model": model,
                "input_tokens": usage_obj.get("input_tokens", 0),
                "output_tokens": usage_obj.get("output_tokens", 0),
                "total_tokens": usage_obj.get("total_tokens", 0),
            }

        return {
            "model": model,
            "input_tokens": getattr(usage_obj, "input_tokens", 0),
            "output_tokens": getattr(usage_obj, "output_tokens", 0),
            "total_tokens": getattr(usage_obj, "total_tokens", 0),
        }
