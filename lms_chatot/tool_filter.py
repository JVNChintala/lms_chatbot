"""
Intent-based tool filtering to reduce LLM confusion
"""

def classify_intent_and_filter_tools(user_message: str, user_role: str, context: dict, all_tools: list) -> list:
    """
    Pre-filter tools based on intent and context to reduce LLM confusion
    Returns only relevant tools for the specific request
    """
    message_lower = user_message.lower()
    
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
        if "discussion" in message_lower or "post" in message_lower:
            discussion_tools = ["list_discussions", "post_discussion_reply"]
            filtered.extend([t for t in all_tools if t["function"]["name"] in discussion_tools])
        
        return filtered
    
    # Detect primary intent
    intents = {
        "view": ["show", "list", "view", "see", "get", "what", "display"],
        "create": ["create", "add", "new", "make", "generate"],
        "update": ["update", "edit", "change", "modify", "fix"],
        "delete": ["delete", "remove"],
        "grade": ["grade", "score", "mark"],
        "enroll": ["enroll", "add student", "add user"],
    }
    
    detected_intent = None
    for intent, keywords in intents.items():
        if any(kw in message_lower for kw in keywords):
            detected_intent = intent
            break
    
    # Detect resource type from context or message
    resource_type = None
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
        if resource_type and resource_type in tool_name:
            if tool not in filtered:
                filtered.append(tool)
    
    # If no filtering worked, return limited core tools
    if not filtered:
        core_tools = ["list_user_courses", "get_course", "list_assignments", "get_assignment"]
        filtered = [t for t in all_tools if t["function"]["name"] in core_tools]
    
    return filtered[:15]  # Max 15 tools to prevent overload
