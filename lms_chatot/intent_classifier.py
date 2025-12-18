import json
from typing import Dict, Any
from inference_systems.openai_inference import OpenAIInference

class IntentClassifier:
    """Deterministic intent classification for Canvas LMS operations"""
    
    INTENTS = [
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
        "general_question"
    ]
    
    INTENT_TOOL_MAP = {
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
        "general_question": []
    }
    
    def __init__(self):
        self.inference = OpenAIInference()
        self.confidence_threshold = 0.75
    
    def classify_intent(self, user_message: str) -> Dict[str, Any]:
        """Classify user intent with confidence score"""
        
        system_prompt = f"""You are an intent classifier for Canvas LMS operations. 
        
Available intents: {', '.join(self.INTENTS)}

Analyze the user message and return ONLY valid JSON with:
- intent: exactly one from the list above
- confidence: float between 0.0 and 1.0
- needs_tool: true if intent requires Canvas API call, false otherwise

Rules:
- Return JSON only, no explanations
- Choose exactly one intent
- Use "general_question" for non-Canvas queries
- Be precise with confidence scores"""

        messages = [{"role": "user", "content": user_message}]
        
        try:
            result = self.inference.call_with_tools(system_prompt, messages, [])
            content = result.get("content", "{}")
            
            # Parse JSON response
            intent_data = json.loads(content)
            
            # Validate intent
            if intent_data.get("intent") not in self.INTENTS:
                return self._fallback_classification()
                
            return intent_data
            
        except Exception as e:
            print(f"[INTENT] Classification error: {e}")
            return self._fallback_classification()
    
    def get_tools_for_intent(self, intent: str, user_role: str) -> list:
        """Get Canvas tools for specific intent and user role"""
        from canvas_tools import CanvasTools
        
        if intent not in self.INTENT_TOOL_MAP:
            return []
            
        tool_names = self.INTENT_TOOL_MAP[intent]
        if not tool_names:
            return []
        
        # Get all available tools for role
        all_tools = CanvasTools.get_tool_definitions(user_role)
        
        # Filter to only tools needed for this intent
        filtered_tools = []
        for tool in all_tools:
            if tool.get("function", {}).get("name") in tool_names:
                filtered_tools.append(tool)
        
        return filtered_tools
    
    def should_use_tool(self, intent_data: Dict[str, Any]) -> bool:
        """Determine if tool should be executed based on intent and confidence"""
        confidence = intent_data.get("confidence", 0.0)
        needs_tool = intent_data.get("needs_tool", False)
        intent = intent_data.get("intent", "general_question")
        
        return (
            confidence >= self.confidence_threshold and
            needs_tool and
            intent != "general_question" and
            intent in self.INTENT_TOOL_MAP
        )
    
    def _fallback_classification(self) -> Dict[str, Any]:
        """Fallback when classification fails"""
        return {
            "intent": "general_question",
            "confidence": 0.5,
            "needs_tool": False
        }