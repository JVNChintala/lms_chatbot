# OpenAI Inference (Stable Production Agent)
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
    Production-safe Agent-capable OpenAI Responses API wrapper
    - GPT-4 & GPT-5 compatible
    - Tool-first
    - Loop-safe
    - Human-recoverable
    """

    DEFAULT_MODEL = "gpt-4o-mini"  # For intent classification and output generation
    TOOL_SELECTION_MODEL = "gpt-5o-mini"  # For tool selection
    MAX_TOKENS = 5000
    MAX_STEPS = 20
    IDLE_LIMIT = 3
    TOOL_REPEAT_LIMIT = 10

    def __init__(self):
        self.name = self.__class__.__name__
        api_key = os.getenv("OPENAI_API_KEY")

        try:
            self.client = OpenAI(api_key=api_key) if api_key else None
        except Exception as e:
            logger.error(f"OpenAI init failed: {e}")
            self.client = None

        self._final_usage: Optional[Dict[str, int]] = None

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
    # AGENT LOOP (PRODUCTION SAFE)
    # ------------------------------------------------------------------
    
    def call_with_tools(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Single-step tool detection (backward compatibility)"""
        if not self.client:
            return {"content": "OpenAI not configured.", "needs_tool": False}

        if not tools:
            try:
                response = self.client.responses.create(
                    model=self.DEFAULT_MODEL,
                    input=[{"role": "system", "content": system_prompt}] + messages,
                    max_output_tokens=self.MAX_TOKENS,
                )
                return {
                    "content": response.output_text or "I'm here to help.",
                    "needs_tool": False,
                    "usage": self._to_dict(response.usage, response.model),
                }
            except Exception as e:
                logger.error(f"Conversation call failed: {e}")
                return {"content": "Error processing request.", "needs_tool": False}

        # Single-step tool detection
        normalized_tools = self._normalize_tools(tools)
        conversation = [{"role": "system", "content": system_prompt}] + messages
        
        try:
            response = self._call_llm(conversation, normalized_tools)
            tool_call = self._extract_tool_call(response)
            
            if tool_call:
                tool_name, tool_args = tool_call
                return {
                    "needs_tool": True,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "usage": self._to_dict(response.usage, response.model),
                }
            
            final_text = self._extract_final_text(response)
            return {
                "needs_tool": False,
                "content": final_text or "I'm here to help.",
                "usage": self._to_dict(response.usage, response.model),
            }
        except Exception as e:
            logger.error(f"call_with_tools failed: {e}")
            return {"content": "Error processing request.", "needs_tool": False}

    def run_agent(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        tool_executor,
    ) -> Dict[str, Any]:

        if not self.client:
            return {"content": "OpenAI not configured."}

        # 🔐 Ensure resume tracking exists
        self.execution_state.setdefault("completed_steps", [])

        normalized_tools = self._normalize_tools(tools)

        # 🟢 RESUME-SAFE SYSTEM PROMPT
        conversation = [
            self._build_resume_guard(system_prompt, tools)
        ] + messages

        idle_steps = 0
        tool_history = []
        stop_reason = None

        for step in range(self.MAX_STEPS):
            # Use GPT-4o for tool selection, GPT-4o-mini for final output
            use_tool_model = len(normalized_tools) > 0
            response = self._call_llm(conversation, normalized_tools, use_tool_selection_model=use_tool_model)
            self._final_usage = self._to_dict(response.usage, response.model)

            tool_call = self._extract_tool_call(response)

            # ---------------- TOOL EXECUTION ----------------
            if tool_call:
                idle_steps = 0
                tool_name, tool_args = tool_call
                tool_history.append(tool_name)

                # 🔁 Tool loop protection
                if len(tool_history) >= 3 and len(set(tool_history[-3:])) == 1:
                    stop_reason = f"Repeated invocation of tool '{tool_name}'"
                    break

                tool_result = tool_executor(
                    tool_name=tool_name,
                    tool_args=tool_args,
                    state=self.execution_state,
                )

                # 🔐 UPDATE EXECUTION STATE
                self._update_execution_state(tool_name, tool_result)

                # 🧠 LOGICAL COMPLETION MARKERS (CRITICAL)
                if tool_name == "create_course" and self.execution_state.get("course_id"):
                    if "course_created" not in self.execution_state["completed_steps"]:
                        self.execution_state["completed_steps"].append("course_created")

                if tool_name == "create_module" and "name" in tool_result:
                    marker = f"module:{tool_result['name']}"
                    if marker not in self.execution_state["completed_steps"]:
                        self.execution_state["completed_steps"].append(marker)

                if tool_name == "add_page_to_module":
                    marker = f"module:{tool_result.get('module_name')}:items"
                    if marker not in self.execution_state["completed_steps"]:
                        self.execution_state["completed_steps"].append(marker)

                if tool_name == "create_assignment":
                    marker = f"assignment:{tool_result.get('name')}"
                    if marker not in self.execution_state["completed_steps"]:
                        self.execution_state["completed_steps"].append(marker)

                if tool_name == "create_quiz":
                    if "final_quiz_created" not in self.execution_state["completed_steps"]:
                        self.execution_state["completed_steps"].append("final_quiz_created")

                # Inject state context with IDs for chaining
                state_context = self._build_state_context()
                conversation.append({
                    "role": "system",
                    "content": f"Tool '{tool_name}' executed. Result: {json.dumps(tool_result)}\n\n{state_context}",
                })
                continue

            # ---------------- FINAL RESPONSE ----------------
            final_text = self._extract_final_text(response)
            if final_text:
                return {
                    "content": final_text,
                    "usage": self._final_usage,
                    "state": self.execution_state,
                    "status": "completed",
                }

            # ---------------- IDLE STATE ----------------
            idle_steps += 1
            if idle_steps >= 3:
                stop_reason = "Model produced no tool calls or final output"
                break

        if not stop_reason:
            stop_reason = "Maximum steps reached"

        return self._graceful_pause(
            conversation=conversation,
            reason=stop_reason,
            step=step,
        )

    # ------------------------------------------------------------------
    # LLM CALL
    # ------------------------------------------------------------------

    def _call_llm(
        self,
        conversation: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        use_tool_selection_model: bool = False,
    ):
        model = self.TOOL_SELECTION_MODEL if use_tool_selection_model and tools else self.DEFAULT_MODEL
        return self.client.responses.create(
            model=model,
            input=conversation,
            tools=tools,
            max_output_tokens=self.MAX_TOKENS,
        )

    # ------------------------------------------------------------------
    # GPT-4 / GPT-5 SAFE PARSING
    # ------------------------------------------------------------------

    def _extract_tool_call(self, response) -> Optional[Tuple[str, Dict[str, Any]]]:
        for item in getattr(response, "output", []) or []:
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
        if getattr(response, "output_text", None):
            return response.output_text.strip() or None

        texts = [
            getattr(item, "text", None)
            for item in getattr(response, "output", []) or []
            if getattr(item, "type", None) == "output_text"
        ]

        combined = "\n".join(t for t in texts if t)
        return combined.strip() or None

    # ------------------------------------------------------------------
    # GRACEFUL PAUSE (LLM-GENERATED)
    # ------------------------------------------------------------------

    def _graceful_pause(self, conversation, reason: str, step: int):
        pause_prompt = {
            "role": "system",
            "content": (
                "You are running a multi-step automation.\n\n"
                f"The automation paused at step {step + 1}.\n"
                f"Reason: {reason}\n\n"
                "Please:\n"
                "1. Summarize what has been completed so far.\n"
                "2. Explain why the automation paused.\n"
                "3. Ask the user if they want to continue as a new request "
                "or provide clarification.\n\n"
                "Be concise and user-friendly."
            )
        }

        response = self._call_llm(conversation + [pause_prompt], tools=[])
        text = self._extract_final_text(response)

        return {
            "content": text or "Partial progress made. Would you like me to continue?",
            "usage": self._final_usage,
            "state": self.execution_state,
            "status": "paused",
            "reason": reason,
        }

    def _build_resume_guard(self, base_prompt: str, tools: List[Dict[str, Any]]) -> Dict[str, str]:
        """
        Injects authoritative resume constraints for the LLM.
        """
        completed = sorted(self.execution_state.get("completed_steps", []))

        state_ids = []
        if self.execution_state.get("course_id"):
            state_ids.append(f"course_id={self.execution_state['course_id']}")
        if self.execution_state.get("modules"):
            for name, mid in self.execution_state["modules"].items():
                state_ids.append(f"module '{name}' id={mid}")

        state_context = "\n".join(state_ids) if state_ids else "No IDs available yet."

        if not completed:
            return {
                "role": "system",
                "content": (
                    f"{base_prompt}\n\n"
                    "CRITICAL: When creating resources, use IDs from tool results for subsequent operations.\n"
                    f"Current state:\n{state_context}"
                )
            }

        completed_text = "\n".join(f"- {c}" for c in completed)

        return {
            "role": "system",
            "content": (
                f"{base_prompt}\n\n"
                "IMPORTANT RESUME INSTRUCTIONS:\n"
                "The following steps are ALREADY COMPLETED in Canvas and MUST NOT be repeated:\n"
                f"{completed_text}\n\n"
                "Rules:\n"
                "- Do NOT recreate existing courses, modules, pages, assignments, or quizzes.\n"
                "- Continue ONLY with steps that are not completed yet.\n"
                "- Assume completed items exist and are published.\n"
                "- If unsure, prefer ADDING missing items over recreating parents.\n\n"
                "CRITICAL: Use these IDs for subsequent operations:\n"
                f"{state_context}"
            )
        }

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

    def _build_state_context(self) -> str:
        """Build context string with current IDs for tool chaining"""
        parts = []
        if self.execution_state.get("course_id"):
            parts.append(f"Current course_id: {self.execution_state['course_id']}")
        if self.execution_state.get("modules"):
            parts.append(f"Available modules: {json.dumps(self.execution_state['modules'])}")
        if self.execution_state.get("assignments"):
            parts.append(f"Created assignments: {json.dumps(self.execution_state['assignments'])}")
        return "\n".join(parts) if parts else ""

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