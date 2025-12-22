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
    """OpenAI Responses API with dict-compatible wrapper"""

    DEFAULT_MODEL = "gpt-4o-mini"
    MAX_TOKENS = 300
    MAX_FINAL_TOKENS = 150

    def __init__(self):
        self.name = self.__class__.__name__
        api_key = os.getenv("OPENAI_API_KEY")
        try:
            self.client = OpenAI(api_key=api_key) if api_key else None
        except Exception as e:
            logger.error(f"OpenAI init failed: {e}")
            self.client = None
        self._final_usage: Optional[Dict[str, int]] = None

    def is_available(self) -> bool:
        return self.client is not None

    def call_with_tools(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        force_tool: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not self.client:
            return {"needs_tool": False, "content": "OpenAI not configured."}
        return self._execute_response_call(system_prompt, messages, tools, force_tool)

    def _execute_response_call(
        self,
        system_prompt: str,
        messages: List[Dict[str, str]],
        tools: List[Dict[str, Any]],
        force_tool: Optional[str],
    ) -> Dict[str, Any]:
        normalized_tools = self._normalize_tools(tools)
        input_messages = [{"role": "system", "content": system_prompt}] + messages

        request = {
            "model": self.DEFAULT_MODEL,
            "input": input_messages,
            "max_output_tokens": self.MAX_TOKENS,
        }

        if normalized_tools:
            request["tools"] = normalized_tools
            if force_tool:
                request["tool_choice"] = "required"

        try:
            response = self.client.responses.create(**request)
            logger.info(f"OpenAI Response: output_text={response.output_text[:100] if response.output_text else 'None'}, output_items={len(response.output)}")
            for idx, item in enumerate(response.output):
                item_type = getattr(item, "type", None)
                logger.info(f"  Item {idx}: type={item_type}, name={getattr(item, 'name', 'N/A')}")
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            return {"needs_tool": False, "content": "Service temporarily unavailable."}

        self._final_usage = self._to_dict(response.usage, response.model)

        for item in response.output:
            item_type = getattr(item, "type", None)
            if item_type in ("tool_call", "function_call"):
                tool_name = getattr(item, "name", "")
                tool_args_raw = getattr(item, "arguments", {}) or {}
                
                # Parse JSON string if needed
                if isinstance(tool_args_raw, str):
                    try:
                        tool_args = json.loads(tool_args_raw)
                    except:
                        tool_args = {}
                else:
                    tool_args = tool_args_raw

                required_fields = self._get_required_fields(normalized_tools, tool_name)
                missing = [f for f in required_fields if not tool_args.get(f)]

                if missing:
                    # Use OpenAI to generate conversational clarification
                    clarification = self._generate_clarification(tool_name, missing, messages)
                    return {
                        "needs_tool": False,
                        "content": clarification,
                        "missing_args": missing,
                        "usage": self._final_usage,
                    }

                return {
                    "needs_tool": True,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "usage": self._final_usage,
                }

        return {
            "needs_tool": False,
            "content": response.output_text or "I'm here to help with Canvas LMS.",
            "usage": self._final_usage,
        }

    def get_final_response(self, tool_result: Dict[str, Any]) -> str:
        if not self.client:
            return "Operation completed successfully."

        result_str = json.dumps(tool_result)
        if len(result_str) > 2000:
            result_str = result_str[:2000] + "..."

        prompt = f"Convert the following Canvas result into a friendly, non-technical summary for the user.\n\n{result_str}"

        try:
            response = self.client.responses.create(
                model=self.DEFAULT_MODEL,
                input=prompt,
                max_output_tokens=self.MAX_FINAL_TOKENS,
            )
            self._final_usage = self._to_dict(response.usage, response.model)
            return response.output_text or "Operation completed successfully."
        except Exception as e:
            logger.error(f"Final response failed: {e}")
            return "Operation completed successfully."

    def get_final_usage(self) -> Optional[Dict[str, int]]:
        return self._final_usage

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
                continue
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

    def _generate_clarification(self, tool_name: str, missing: List[str], conversation: List[Dict[str, str]]) -> str:
        """Use OpenAI to generate natural clarification request with context"""
        if not self.client:
            return f"I need more information: {', '.join(missing)}"
        
        # Build context-aware prompt
        context = "\n".join([f"{m['role']}: {m['content']}" for m in conversation[-3:]])
        prompt = (
            f"The user wants to {tool_name.replace('_', ' ')} but didn't provide: {', '.join(missing)}.\n"
            f"Recent conversation:\n{context}\n\n"
            "Ask the user conversationally for the missing information. Be friendly and helpful."
        )
        
        try:
            response = self.client.responses.create(
                model=self.DEFAULT_MODEL,
                input=prompt,
                max_output_tokens=100,
            )
            return response.output_text or f"Could you provide the {', '.join(missing)}?"
        except:
            return f"Could you provide the {', '.join(missing)}?"

    @staticmethod
    def _get_required_fields(tools: List[Dict[str, Any]], tool_name: str) -> List[str]:
        for t in tools:
            if t.get("name") == tool_name:
                return t.get("parameters", {}).get("required", [])
        return []

    @staticmethod
    def _to_dict(usage_obj, model: str) -> Dict[str, int]:
        """Convert typed usage object to dict for backward compatibility"""
        if not usage_obj:
            return {"model": model, "input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
        return {
            "model": model,
            "input_tokens": getattr(usage_obj, "input_tokens", 0),
            "output_tokens": getattr(usage_obj, "output_tokens", 0),
            "total_tokens": getattr(usage_obj, "total_tokens", 0),
        }
