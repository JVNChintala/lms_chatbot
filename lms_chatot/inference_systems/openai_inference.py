import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from .base_inference import BaseInference

load_dotenv()


class OpenAIInference(BaseInference):
    """
    Cost-optimized OpenAI inference for Canvas LMS.
    - Uses gpt-4o-mini for intent classification, tool argument generation, and response formatting.
    - Handles missing tool arguments interactively.
    - Provides user-friendly, conversational responses.
    """

    DEFAULT_MODEL = "gpt-4o-mini"
    MAX_TOKENS_TOOL = 200
    MAX_TOKENS_FINAL = 150

    def __init__(self):
        super().__init__()
        api_key = os.getenv("OPENAI_API_KEY")
        self.client: Optional[OpenAI] = OpenAI() if api_key else None
        self._final_usage: Optional[Dict[str, int]] = None

    # ---------------------------
    # Availability
    # ---------------------------
    def is_available(self) -> bool:
        return self.client is not None

    # ---------------------------
    # Public API
    # ---------------------------
    def call_with_tools(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        force_tool: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.client:
            return {"needs_tool": False, "content": "OpenAI not configured."}

        return self._execute_tool_call(
            system_prompt=system_prompt,
            messages=messages,
            tools=tools,
            model=self.DEFAULT_MODEL,
            force_tool=force_tool,
        )

    # ---------------------------
    # Tool Execution with interactive argument filling
    # ---------------------------
    def _execute_tool_call(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        model: str,
        force_tool: Optional[str],
    ) -> Dict[str, Any]:
        """
        Executes OpenAI tool calling using a cost-effective model.
        Prompts user for missing required arguments if any.
        """
        openai_tools = self._normalize_tools(tools)

        kwargs = {
            "model": model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "max_tokens": self.MAX_TOKENS_TOOL,
        }

        if openai_tools:
            kwargs["tools"] = openai_tools
            if force_tool:
                kwargs["tool_choice"] = {"type": "function", "function": {"name": force_tool}}
            else:
                kwargs["tool_choice"] = "auto"

        response = self.client.chat.completions.create(**kwargs)
        usage = self._extract_usage(response, model)
        message = response.choices[0].message

        if message.tool_calls:
            tool_call = message.tool_calls[0]
            tool_args = json.loads(tool_call.function.arguments or "{}")

            # Interactive argument filling
            required_fields = self._get_required_fields(openai_tools, tool_call.function.name)
            missing_fields = [f for f in required_fields if f not in tool_args]

            if missing_fields:
                # Build a prompt to ask user for missing info
                missing_prompt = (
                    f"To complete the requested action '{tool_call.function.name}', I need the following information: "
                    + ", ".join(missing_fields)
                )
                return {
                    "needs_tool": True,
                    "tool_name": tool_call.function.name,
                    "tool_args": tool_args,
                    "missing_args": missing_fields,
                    "prompt_user": missing_prompt,
                    "usage": usage,
                }

            return {
                "needs_tool": True,
                "tool_name": tool_call.function.name,
                "tool_args": tool_args,
                "tool_call_id": tool_call.id,
                "usage": usage,
            }

        return {
            "needs_tool": False,
            "content": message.content or "I am here to help with Canvas LMS.",
            "usage": usage,
        }

    # ---------------------------
    # Final response formatting (friendly)
    # ---------------------------
    def get_final_response(self, tool_result: Dict[str, Any]) -> str:
        """
        Convert raw Canvas API result into a user-friendly, conversational response.
        """
        if not self.client:
            return "Operation completed successfully."

        # Generate a plain-English description
        system_prompt = (
            "You are a Canvas LMS assistant. Convert the following API result into a friendly, "
            "conversational summary for a teacher, student, or admin. Do NOT show raw JSON.\n\n"
            f"Result:\n{json.dumps(tool_result)}"
        )

        response = self.client.chat.completions.create(
            model=self.DEFAULT_MODEL,
            messages=[{"role": "system", "content": system_prompt}],
            max_tokens=self.MAX_TOKENS_FINAL,
        )

        self._final_usage = self._extract_usage(response, self.DEFAULT_MODEL)
        return response.choices[0].message.content or "Operation completed successfully."

    def get_final_usage(self) -> Optional[Dict[str, int]]:
        return self._final_usage

    # ---------------------------
    # Helpers
    # ---------------------------
    def _normalize_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for tool in tools:
            if "function" in tool:
                normalized.append(tool)
            else:
                normalized.append(
                    {
                        "type": "function",
                        "function": {
                            "name": tool["name"],
                            "description": tool.get("description", ""),
                            "parameters": {
                                "type": "object",
                                "properties": tool.get("input_schema", {}).get("properties", {}),
                                "required": tool.get("input_schema", {}).get("required", []),
                                "additionalProperties": False,
                            },
                        },
                    }
                )
        return normalized

    @staticmethod
    def _extract_usage(response, model: str) -> Dict[str, int]:
        usage = response.usage
        return {
            "model": model,
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
            "total_tokens": usage.total_tokens if usage else 0,
        }

    @staticmethod
    def _get_required_fields(tools: List[Dict[str, Any]], tool_name: str) -> List[str]:
        """
        Retrieve required fields for a tool from the normalized tools.
        """
        for t in tools:
            if t["function"]["name"] == tool_name:
                return t["function"]["parameters"].get("required", [])
        return []
