import json
import re
from typing import Dict, Any, List
from inference_systems.openai_inference import OpenAIInference


class IntentClassifier:
    """
    Deterministic intent classification for Canvas LMS operations.

    IMPORTANT:
    - This class NEVER triggers tools
    - It ONLY consumes plain text responses
    - It is hardened against tool-shaped responses
    """

    INTENTS: List[str] = [
        # Course operations
        "list_courses",
        "get_course_details",
        "create_course",
        "update_course",
        "publish_course",
        "unpublish_course",
        
        # Assignment operations
        "list_assignments",
        "get_assignment",
        "create_assignment",
        "update_assignment",
        "delete_assignment",
        "grade_assignment",
        "submit_assignment",
        
        # Module operations
        "list_modules",
        "get_module",
        "create_module",
        "update_module",
        "delete_module",
        
        # User operations
        "list_users",
        "get_user",
        "create_user",
        "enroll_user",
        "unenroll_user",
        "list_enrollments",
        
        # Announcement operations
        "list_announcements",
        "create_announcement",
        
        # Discussion operations
        "list_discussions",
        "create_discussion",
        
        # Quiz operations
        "list_quizzes",
        "create_quiz",
        
        # Page operations
        "list_pages",
        "create_page",
        
        # File operations
        "list_files",
        "upload_file",
        
        # Grade operations
        "get_grades",
        "view_gradebook",
        
        # Synthetic intents (Canvas data + LLM reasoning)
        "generate_study_plan",
        "suggest_learning_path",
        "analyze_progress",
        "recommend_resources",
        "explain_concept",
        "create_lesson_plan",
        "generate_quiz_questions",
        "provide_feedback",
        "summarize_course",
        
        # Meta intents (clarification needed)
        "create_content",
        "help_with_course",
        
        "general_question",
    ]

    INTENT_TOOL_MAP: Dict[str, List[str]] = {
        # Course operations
        "list_courses": ["list_user_courses"],
        "get_course_details": ["get_course"],
        "create_course": ["create_course"],
        "update_course": ["update_course"],
        "publish_course": ["publish_course"],
        "unpublish_course": ["unpublish_course"],
        
        # Assignment operations
        "list_assignments": ["list_assignments"],
        "get_assignment": ["get_assignment"],
        "create_assignment": ["create_assignment"],
        "update_assignment": ["update_assignment"],
        "delete_assignment": ["delete_assignment"],
        "grade_assignment": ["grade_assignment"],
        "submit_assignment": ["submit_assignment"],
        
        # Module operations
        "list_modules": ["list_modules"],
        "get_module": ["get_module"],
        "create_module": ["create_module"],
        "update_module": ["update_module"],
        "delete_module": ["delete_module"],
        
        # User operations
        "list_users": ["list_users"],
        "get_user": ["get_user_profile"],
        "create_user": ["create_user"],
        "enroll_user": ["enroll_user"],
        "unenroll_user": ["unenroll_user"],
        "list_enrollments": ["list_enrollments"],
        
        # Announcement operations
        "list_announcements": ["list_announcements"],
        "create_announcement": ["create_announcement"],
        
        # Discussion operations
        "list_discussions": ["list_discussions"],
        "create_discussion": ["create_discussion"],
        
        # Quiz operations
        "list_quizzes": ["list_quizzes"],
        "create_quiz": ["create_quiz"],
        
        # Page operations
        "list_pages": ["list_pages"],
        "create_page": ["create_page"],
        
        # File operations
        "list_files": ["list_files"],
        "upload_file": ["upload_file"],
        
        # Grade operations
        "get_grades": ["get_grades"],
        "view_gradebook": ["view_gradebook"],
        
        # Synthetic intents (fetch Canvas data, LLM reasons over it)
        "generate_study_plan": ["list_user_courses", "list_assignments"],
        "suggest_learning_path": ["list_user_courses", "list_modules"],
        "analyze_progress": ["get_grades", "list_assignments"],
        "recommend_resources": ["list_user_courses"],
        "explain_concept": [],  # Pure LLM reasoning
        "create_lesson_plan": ["list_modules"],
        "generate_quiz_questions": [],  # Pure LLM generation
        "provide_feedback": ["get_assignment"],
        "summarize_course": ["get_course", "list_modules"],
        
        # Meta intents (guide user to specific action)
        "create_content": [],
        "help_with_course": [],
        
        "general_question": [],
    }

    def __init__(self, confidence_threshold: float = 0.75):
        self.inference = OpenAIInference()
        self.confidence_threshold = confidence_threshold

    # ------------------------------------------------------------------
    # Intent classification
    # ------------------------------------------------------------------

    def classify_intent(self, user_message: str) -> Dict[str, Any]:
        """
        Classify user intent with confidence score.

        HARD RULE:
        - We ONLY accept valid JSON text output
        - Any tool-like response is ignored
        """

        system_prompt = (
            "You are an intent classifier for Canvas LMS.\n\n"
            f"Available intents:\n{', '.join(self.INTENTS)}\n\n"
            "Return ONLY valid JSON in this exact format:\n"
            "{\n"
            '  "intent": "<intent>",\n'
            '  "confidence": 0.0,\n'
            '  "needs_tool": true\n'
            "}\n\n"
            "Rules:\n"
            "- Choose exactly ONE intent\n"
            "- Use 'general_question' for greetings or unclear queries\n"
            "- Do NOT explain\n"
            "- Do NOT call tools\n"
        )

        try:
            result = self.inference.call_with_tools(
                system_prompt=system_prompt,
                messages=[{"role": "user", "content": user_message}],
                tools=[],              # no tools
                force_tool=None,        # never force tools
            )

            # Ignore tool-shaped responses completely
            if result.get("needs_tool"):
                return self._fallback()

            raw_content = (result.get("content") or "").strip()
            if not raw_content:
                return self._fallback()

            intent_data = self._safe_json_parse(raw_content)
            if not intent_data:
                return self._fallback()

            intent = intent_data.get("intent")
            confidence = float(intent_data.get("confidence", 0.0))
            needs_tool = bool(intent_data.get("needs_tool", False))

            if intent not in self.INTENTS:
                return self._fallback()

            return {
                "intent": intent,
                "confidence": confidence,
                "needs_tool": needs_tool,
            }

        except Exception as exc:
            print(f"[INTENT_CLASSIFIER] Error: {exc}")
            return self._fallback()

    # ------------------------------------------------------------------
    # Tool gating
    # ------------------------------------------------------------------

    def should_use_tool(self, intent_data: Dict[str, Any]) -> bool:
        """
        Decide whether tool execution is allowed.
        """

        return (
            intent_data.get("confidence", 0.0) >= self.confidence_threshold
            and intent_data.get("needs_tool", False)
            and intent_data.get("intent") in self.INTENT_TOOL_MAP
            and intent_data.get("intent") != "general_question"
        )

    def get_tools_for_intent(self, intent: str, user_role: str) -> List[Dict[str, Any]]:
        """
        Resolve tool definitions for an intent.
        """

        if intent not in self.INTENT_TOOL_MAP:
            return []

        tool_names = set(self.INTENT_TOOL_MAP[intent])
        if not tool_names:
            return []

        from canvas_tools import CanvasTools

        return [
            tool
            for tool in CanvasTools.get_tool_definitions(user_role)
            if tool["function"]["name"] in tool_names
        ]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_json_parse(text: str) -> Dict[str, Any]:
        """
        Extract and parse JSON even if the model adds noise.
        """
        try:
            # Direct parse
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Fallback: extract JSON block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return {}

        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _fallback() -> Dict[str, Any]:
        return {
            "intent": "general_question",
            "confidence": 0.5,
            "needs_tool": False,
        }
