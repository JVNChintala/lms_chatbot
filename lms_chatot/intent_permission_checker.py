import logging
from typing import Dict, Any, Optional, Set

logger = logging.getLogger(__name__)

class IntentPermissionChecker:
    """Check if user intent requires tools they don't have access to"""
    
    # Keywords that map to specific tools
    INTENT_TOOL_MAP = {
        "create_course": ["create", "new", "make", "add", "course"],
        "update_course": ["update", "modify", "change", "edit", "course"],
        "delete_course": ["delete", "remove", "course"],
        "publish_course": ["publish", "course"],
        "unpublish_course": ["unpublish", "course"],
        "create_module": ["create", "new", "make", "add", "module"],
        "update_module": ["update", "modify", "change", "edit", "module"],
        "delete_module": ["delete", "remove", "module"],
        "create_assignment": ["create", "new", "make", "add", "assignment"],
        "update_assignment": ["update", "modify", "change", "edit", "assignment"],
        "delete_assignment": ["delete", "remove", "assignment"],
        "grade_assignment": ["grade", "score", "mark", "assignment"],
        "create_quiz": ["create", "new", "make", "add", "quiz"],
        "create_page": ["create", "new", "make", "add", "page"],
        "create_discussion": ["create", "new", "make", "add", "discussion"],
        "create_announcement": ["create", "new", "make", "add", "announcement", "post"],
        "enroll_user": ["enroll", "add", "user", "student"],
        "create_user": ["create", "new", "user"],
    }
    
    def __init__(self):
        pass
    
    def check_permission(
        self,
        user_message: str,
        available_tools: Set[str],
        user_role: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if user intent requires unavailable tools
        
        Returns:
            {"allowed": True} if permitted
            {"allowed": False, "message": "..."} if denied
        """
        message_lower = user_message.lower()
        
        for tool_name, keywords in self.INTENT_TOOL_MAP.items():
            # Check if all keywords for this tool are in the message
            if all(kw in message_lower for kw in keywords):
                if tool_name not in available_tools:
                    return {
                        "allowed": False,
                        "message": self._get_permission_message(tool_name, user_role),
                        "required_tool": tool_name
                    }
        
        return {"allowed": True}
    
    def _get_permission_message(self, tool_name: str, user_role: Optional[str]) -> str:
        """Generate user-friendly permission error message"""
        role_display = user_role or "your role"
        
        action_map = {
            "create_course": "create courses",
            "update_course": "update courses",
            "delete_course": "delete courses",
            "publish_course": "publish courses",
            "unpublish_course": "unpublish courses",
            "create_module": "create modules",
            "update_module": "update modules",
            "delete_module": "delete modules",
            "create_assignment": "create assignments",
            "update_assignment": "update assignments",
            "delete_assignment": "delete assignments",
            "grade_assignment": "grade assignments",
            "create_quiz": "create quizzes",
            "create_page": "create pages",
            "create_discussion": "create discussions",
            "create_announcement": "create announcements",
            "enroll_user": "enroll users",
            "create_user": "create users",
        }
        
        action = action_map.get(tool_name, "perform this action")
        
        return (
            f"I don't have permission to {action} with {role_display} access. "
            f"This action requires teacher or admin privileges."
        )
