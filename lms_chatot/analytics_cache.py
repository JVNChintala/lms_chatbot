import time
from typing import Dict, Any, Optional
from canvas_integration import CanvasLMS

class AnalyticsCache:
    """Lightweight analytics cache to reduce Canvas API calls"""
    
    def __init__(self, cache_duration: int = 300):  # 5 minutes
        self.cache = {}
        self.cache_duration = cache_duration
    
    def get_cached_analytics(self, user_role: str, canvas_user_id: int = None) -> Optional[Dict[str, Any]]:
        """Get cached analytics if available and not expired"""
        cache_key = f"{user_role}_{canvas_user_id}"
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_duration:
                return cached_data
        
        return None
    
    def cache_analytics(self, user_role: str, analytics: Dict[str, Any], canvas_user_id: int = None):
        """Cache analytics data"""
        cache_key = f"{user_role}_{canvas_user_id}"
        self.cache[cache_key] = (analytics, time.time())
    
    def get_quick_analytics(self, canvas: CanvasLMS, user_role: str) -> Dict[str, Any]:
        """Get lightweight analytics for chat integration"""
        try:
            if user_role == "admin":
                courses = canvas.list_account_courses()[:5]  # Limit for performance
                return {
                    "total_courses": len(courses),
                    "recent_courses": [{"id": c.get("id"), "name": c.get("name")} for c in courses[:3]],
                    "quick_actions": [
                        {"action": "create_course", "label": "📚 Create Course", "prompt": "Create a new course"},
                        {"action": "list_users", "label": "👥 View Users", "prompt": "Show me all users"},
                        {"action": "create_user", "label": "➕ Add User", "prompt": "Create a new user"}
                    ]
                }
            elif user_role in ["teacher", "faculty", "instructor"]:
                courses = canvas.list_courses()[:3]
                return {
                    "my_courses": len(courses),
                    "recent_courses": [{"id": c.get("id"), "name": c.get("name")} for c in courses],
                    "quick_actions": [
                        {"action": "create_assignment", "label": "📝 New Assignment", "prompt": "Create an assignment"},
                        {"action": "create_module", "label": "📖 Add Module", "prompt": "Create a module"},
                        {"action": "list_courses", "label": "📚 My Courses", "prompt": "Show my courses"}
                    ]
                }
            else:  # student
                courses = canvas.list_courses()[:3]
                return {
                    "enrolled_courses": len(courses),
                    "recent_courses": [{"id": c.get("id"), "name": c.get("name")} for c in courses],
                    "quick_actions": [
                        {"action": "list_courses", "label": "📚 My Courses", "prompt": "Show my courses"},
                        {"action": "learning_plan", "label": "📋 Learning Plan", "prompt": "Generate my learning plan"},
                        {"action": "progress_tracker", "label": "📊 Progress", "prompt": "Show my progress tracker"},
                        {"action": "study_tips", "label": "💡 Study Tips", "prompt": "Get study recommendations"},
                        {"action": "prioritize", "label": "⏰ Prioritize", "prompt": "Help me prioritize assignments"},
                        {"action": "analytics", "label": "📈 Analytics", "prompt": "Show my learning analytics"}
                    ]
                }
        except Exception as e:
            return {"error": str(e), "quick_actions": []}

# Global cache instance
analytics_cache = AnalyticsCache()