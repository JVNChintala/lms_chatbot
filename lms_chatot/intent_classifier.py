import json
from typing import Dict, Any, List
from inference_systems.openai_inference import OpenAIInference


class IntentClassifier:
    """Deterministic intent classification for Canvas LMS operations"""

    INTENTS: List[str] = [
        "list_courses",
        "get_course_details",
        "create_course",
        "list_assignments",
        "get_assignment",
        "grade_assignment",
        "list_modules",
        "create_module",
        "enroll_user",
        "list_users",
        "general_question",
    ]

    INTENT_TOOL_MAP: Dict[str, List[str]] = {
        "list_courses": ["list_user_courses"],
        "get_course_details": ["get_course"],
        "create_course": ["create_course"],
        "list_assignments": ["list_assignments"],
        "get_assignment": ["get_assignment"],
        "grade_assignment": ["grade_assignment"],
        "list_modules": ["list_modules"],
        "create_module": ["create_module"],
        "enroll_user": ["enroll_user"],
        "list_users": ["list_users"],
        "general_question": [],
    }

    def __init__(self, confidence_threshold: float = 0.75):
        self.inference = OpenAIInference()
        self.confidence_threshold = confidence_threshold

    def classify_intent(self, user_message: str) -> Dict[str, Any]:
        """Classify user intent with confidence score"""

        system_prompt = (
            "You are an intent classifier for Canvas LMS operations.\n\n"
            f"Available intents: {', '.join(self.INTENTS)}\n\n"
            "Return ONLY valid JSON:\n"
            "{\n"
            '  "intent": "<intent>",\n'
            '  "confidence": 0.0-1.0,\n'
            '  "needs_tool": true|false\n'
            "}\n\n"
            "Rules:\n"
            "- Choose exactly one intent\n"
            '- Use "general_question" for non-Canvas queries\n'
            "- No explanations"
        )

        try:
            result = self.inference.call_with_tools(
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                tools=[]
            )

            content = result.get("content", "{}")
            intent_data = json.loads(content)

            if intent_data.get("intent") not in self.INTENTS:
                return self._fallback()

            return {
                "intent": intent_data["intent"],
                "confidence": float(intent_data.get("confidence", 0.0)),
                "needs_tool": bool(intent_data.get("needs_tool", False)),
            }

        except Exception as exc:
            print(f"[INTENT_CLASSIFIER] Error: {exc}")
            return self._fallback()

    def should_use_tool(self, intent_data: Dict[str, Any]) -> bool:
        """Decide whether tool execution is allowed"""

        return (
            intent_data.get("confidence", 0.0) >= self.confidence_threshold
            and intent_data.get("needs_tool", False)
            and intent_data.get("intent") in self.INTENT_TOOL_MAP
            and intent_data.get("intent") != "general_question"
        )

    def get_tools_for_intent(self, intent: str, user_role: str) -> List[Dict[str, Any]]:
        """Resolve tool definitions for an intent"""

        if intent not in self.INTENT_TOOL_MAP:
            return []

        tool_names = set(self.INTENT_TOOL_MAP[intent])
        if not tool_names:
            return []

        from canvas_tools import CanvasTools

        return [
            tool for tool in CanvasTools.get_tool_definitions(user_role)
            if tool["function"]["name"] in tool_names
        ]

    @staticmethod
    def _fallback() -> Dict[str, Any]:
        return {
            "intent": "general_question",
            "confidence": 0.5,
            "needs_tool": False,
        }
