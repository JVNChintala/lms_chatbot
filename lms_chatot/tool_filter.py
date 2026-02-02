"""
Intent-based tool filtering to reduce LLM confusion
Uses GPT-4o-mini for fast intent classification
"""
import os
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize OpenAI client for intent classification
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
INTENT_MODEL = "gpt-4o-mini"  # Fast model for intent classification

def classify_intent_with_llm(user_message: str, context: dict) -> dict:
    """Use GPT-4o-mini to classify user intent and resource type"""
    try:
        context_str = f"course_id={context.get('course_id')}, quiz_id={context.get('quiz_id')}, assignment_id={context.get('assignment_id')}, current_page={context.get('current_page', '')}"
        
        prompt = f"""Analyze this user message and extract:
1. Primary intent: view, create, update, delete, grade, enroll, or general
2. Resource type: course, assignment, quiz, page, module, discussion, or none

User message: \"{user_message}\"
Context: {context_str}

Respond ONLY with valid JSON:
{{"intent": "<intent>", "resource": "<resource>"}}"""

        response = client.chat.completions.create(
            model=INTENT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=50,
            response_format={"type": "json_object"}
        )

        import json
        content = response.choices[0].message.content
        if content is None or not content.strip():
            logger.warning("LLM returned empty content for intent classification.")
            return None
        content = content.strip()
        result = json.loads(content)
        
        # Validate response structure
        if "intent" not in result or "resource" not in result:
            logger.warning(f"LLM returned incomplete response: {result}")
            return None
            
        return result
    except Exception as e:
        logger.warning(f"LLM intent classification failed: {e}, falling back to keyword matching")
        return None

def classify_intent_and_filter_tools(user_message: str, user_role: str, context: dict, all_tools: list) -> list:
    """
    Pre-filter tools based on intent and context to reduce LLM confusion
    Uses GPT-4o-mini for intent classification
    Returns only relevant tools for the specific request
    """
    message_lower = user_message.lower()
    
    # Try LLM-based intent classification first
    llm_intent = classify_intent_with_llm(user_message, context)
    
    if llm_intent:
        detected_intent = llm_intent.get("intent")
        resource_type = llm_intent.get("resource")
        print(f"[LLM INTENT] Intent: {detected_intent}, Resource: {resource_type}")
    else:
        # Fallback to keyword-based detection
        detected_intent, resource_type = _keyword_based_classification(message_lower, context)
        print(f"[KEYWORD INTENT] Intent: {detected_intent}, Resource: {resource_type}")
    
    # For students, always include core navigation tools
    if user_role == "student":
        core_student_tools = [
            "list_user_courses", "get_course", 
            "list_assignments", "get_assignment",
            "list_modules", "get_module",
            "get_upcoming_assignments", "get_course_progress",
            "get_page_content", "get_rubric"
        ]
        filtered = [t for t in all_tools if t["function"]["name"] in core_student_tools]
        
        # Add discussion tools if mentioned
        if resource_type == "discussion":
            discussion_tools = ["list_discussions", "post_discussion_reply"]
            filtered.extend([t for t in all_tools if t["function"]["name"] in discussion_tools])
        
        return filtered
    
    # Filter tools based on intent + resource
    filtered = []
    for tool in all_tools:
        tool_name = tool["function"]["name"]
        
        # Always include basic tools
        if tool_name in ["list_user_courses", "get_course"]:
            filtered.append(tool)
            continue
        
        # Intent-based filtering
        if detected_intent == "view":
            if tool_name.startswith("list_") or tool_name.startswith("get_"):
                filtered.append(tool)
        elif detected_intent == "create":
            if tool_name.startswith("create_"):
                filtered.append(tool)
        elif detected_intent == "update":
            if tool_name.startswith("update_"):
                filtered.append(tool)
        elif detected_intent == "delete":
            if tool_name.startswith("delete_"):
                filtered.append(tool)
        elif detected_intent == "grade":
            if "grade" in tool_name or "submission" in tool_name:
                filtered.append(tool)
        elif detected_intent == "enroll":
            if "enroll" in tool_name or "user" in tool_name:
                filtered.append(tool)
        
        # Resource-based filtering
        if resource_type and resource_type != "none" and resource_type in tool_name:
            if tool not in filtered:
                filtered.append(tool)
        
        # Always include Commons search when creating courses
        if detected_intent == "create" and resource_type == "course":
            if "search_commons" in tool_name or "import_from_commons" in tool_name:
                if tool not in filtered:
                    filtered.append(tool)
    
    # If no filtering worked, return limited core tools
    if not filtered:
        core_tools = ["list_user_courses", "get_course", "list_assignments", "get_assignment"]
        filtered = [t for t in all_tools if t["function"]["name"] in core_tools]
    
    return filtered[:15]  # Max 15 tools to prevent overload

def _keyword_based_classification(message_lower: str, context: dict) -> tuple:
    """Fallback keyword-based intent classification"""
    
    # Detect primary intent
    intents = {
        "view": ["show", "list", "view", "see", "get", "what", "display"],
        "create": ["create", "add", "new", "make", "generate"],
        "update": ["update", "edit", "change", "modify", "fix"],
        "delete": ["delete", "remove"],
        "grade": ["grade", "score", "mark"],
        "enroll": ["enroll", "add student", "add user"],
    }
    
    detected_intent = "general"
    for intent, keywords in intents.items():
        if any(kw in message_lower for kw in keywords):
            detected_intent = intent
            break
    
    # Detect resource type from context or message
    resource_type = "none"
    if context.get("quiz_id") or "quiz" in message_lower:
        resource_type = "quiz"
    elif "/pages/" in context.get("current_page", "") or "page" in message_lower:
        resource_type = "page"
    elif context.get("assignment_id") or "assignment" in message_lower:
        resource_type = "assignment"
    elif context.get("module_id") or "module" in message_lower:
        resource_type = "module"
    elif "course" in message_lower:
        resource_type = "course"
    elif "discussion" in message_lower:
        resource_type = "discussion"
    
    return detected_intent, resource_type
