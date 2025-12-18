import os
import json
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv
from .base_inference import BaseInference

load_dotenv()
logger = logging.getLogger(__name__)


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
        try:
            self.client: Optional[OpenAI] = OpenAI(api_key=api_key) if api_key else None
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.client = None
        self._final_usage: Optional[Dict[str, int]] = None

    # ---------------------------
    # Availability
    # ---------------------------
    def is_available(self) -> bool:
        if not self.client:
            logger.warning("OpenAI client not configured")
            return False
        return True

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
            logger.error("OpenAI client not configured")
            return {"needs_tool": False, "content": "OpenAI not configured."}

        try:
            return self._execute_tool_call(
                system_prompt=system_prompt,
                messages=messages,
                tools=tools,
                model=self.DEFAULT_MODEL,
                force_tool=force_tool,
            )
        except Exception as e:
            logger.error(f"Tool call failed: {e}")
            return {"needs_tool": False, "content": "I encountered an error processing your request."}

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

        try:
            response = self.client.chat.completions.create(**kwargs)
            if not response or not response.choices:
                logger.error("Invalid API response structure")
                return {"needs_tool": False, "content": "API response error"}
            
            usage = self._extract_usage(response, model)
            message = response.choices[0].message
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return {"needs_tool": False, "content": "Service temporarily unavailable"}

        if message.tool_calls:
            tool_call = message.tool_calls[0]
            print(f"[OPENAI_INFERENCE] Tool call detected: {tool_call.function.name}")
            try:
                tool_args = json.loads(tool_call.function.arguments or "{}")
                print(f"[OPENAI_INFERENCE] Parsed tool args: {tool_args}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in tool arguments: {e}")
                return {"needs_tool": False, "content": "Tool argument parsing error"}

            # Always prompt user to confirm arguments
            required_fields = self._get_required_fields(openai_tools, tool_call.function.name)
            print(f"[OPENAI_INFERENCE] Required fields for {tool_call.function.name}: {required_fields}")
            
            if required_fields:
                prompt_parts = []
                if tool_args:
                    prompt_parts.append("Please confirm:")
                    for field, value in tool_args.items():
                        if field in required_fields:
                            prompt_parts.append(f"{field}: {value}")
                
                missing_fields = [f for f in required_fields if f not in tool_args]
                print(f"[OPENAI_INFERENCE] Missing fields: {missing_fields}")
                if missing_fields:
                    prompt_parts.append(f"Please provide: {', '.join(missing_fields)}")
                
                confirmation_prompt = " ".join(prompt_parts)
                print(f"[OPENAI_INFERENCE] Prompting user for confirmation: {confirmation_prompt}")
                
                return {
                    "needs_tool": True,
                    "tool_name": tool_call.function.name,
                    "tool_args": tool_args,
                    "missing_args": missing_fields,
                    "prompt_user": confirmation_prompt,
                    "usage": usage,
                }

            # No required fields, proceed directly
            print(f"[OPENAI_INFERENCE] No required fields, proceeding with tool {tool_call.function.name}")
            return {
                "needs_tool": True,
                "tool_name": tool_call.function.name,
                "tool_args": tool_args,
                "tool_call_id": tool_call.id,
                "usage": usage,
            }

        print(f"[OPENAI_INFERENCE] No tool calls detected, returning conversational response")
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

        try:
            # Limit result size to prevent excessive token usage
            result_str = json.dumps(tool_result)
            if len(result_str) > 2000:
                result_str = result_str[:2000] + "..."
            
            # Sanitized system prompt without exposing internal details
            system_prompt = (
                "Convert this result into a friendly summary. Do not show technical details.\n\n"
                f"Result:\n{result_str}"
            )

            response = self.client.chat.completions.create(
                model=self.DEFAULT_MODEL,
                messages=[{"role": "system", "content": system_prompt}],
                max_tokens=self.MAX_TOKENS_FINAL,
                timeout=30
            )

            if not response or not response.choices:
                return "Operation completed successfully."
                
            self._final_usage = self._extract_usage(response, self.DEFAULT_MODEL)
            return response.choices[0].message.content or "Operation completed successfully."
        except Exception as e:
            logger.error(f"Final response generation failed: {e}")
            return "Operation completed successfully."

    def get_final_usage(self) -> Optional[Dict[str, int]]:
        return self._final_usage

    # ---------------------------
    # Helpers
    # ---------------------------
    def _normalize_tools(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for tool in tools:
            try:
                if "function" in tool:
                    normalized.append(tool)
                else:
                    input_schema = tool.get("input_schema", {})
                    normalized.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool.get("name", "unknown"),
                                "description": tool.get("description", ""),
                                "parameters": {
                                    "type": "object",
                                    "properties": input_schema.get("properties", {}),
                                    "required": input_schema.get("required", []),
                                    "additionalProperties": False,
                                },
                            },
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to normalize tool: {e}")
                continue
        return normalized

    @staticmethod
    def _extract_usage(response, model: str) -> Dict[str, int]:
        if not response or not hasattr(response, 'usage'):
            return {"model": model, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        
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
            try:
                func = t.get("function", {})
                if func.get("name") == tool_name:
                    return func.get("parameters", {}).get("required", [])
            except (KeyError, TypeError):
                continue
        return []
