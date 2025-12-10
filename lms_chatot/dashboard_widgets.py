from canvas_integration import CanvasLMS
from typing import Dict, List

class DashboardWidgets:
    def __init__(self, canvas: CanvasLMS):
        self.canvas = canvas
    
    def get_student_widgets(self) -> Dict:
        """Get widgets for student dashboard"""
        courses = self.canvas.list_courses()
        
        widgets = {
            "enrolled_courses": {
                "title": "My Courses",
                "count": len(courses),
                "items": [{"id": c.get("id"), "name": c.get("name"), "code": c.get("course_code")} for c in courses[:5]]
            },
            "pending_assignments": self._get_pending_assignments(courses),
            "recent_announcements": self._get_recent_announcements(courses)
        }
        return widgets
    
    def get_teacher_widgets(self) -> Dict:
        """Get widgets for teacher dashboard"""
        courses = self.canvas.list_courses()
        
        widgets = {
            "my_courses": {
                "title": "My Courses",
                "count": len(courses),
                "items": [{"id": c.get("id"), "name": c.get("name"), "code": c.get("course_code"), "published": c.get("workflow_state") == "available"} for c in courses[:8]]
            },
            "course_stats": self._get_course_stats(courses),
            "unpublished_courses": self._get_unpublished_courses(courses),
            "quick_actions": {
                "title": "Quick Actions",
                "actions": [
                    {"label": "Create Course", "action": "create_course"},
                    {"label": "Create Module", "action": "create_module"},
                    {"label": "Create Assignment", "action": "create_assignment"}
                ]
            }
        }
        return widgets
    
    def get_admin_widgets(self) -> Dict:
        """Get widgets for admin dashboard"""
        courses = self.canvas.list_account_courses()
        users = self.canvas.list_users()
        
        widgets = {
            "overview": {
                "title": "System Overview",
                "total_courses": len(courses),
                "total_users": len(users),
                "active_courses": len([c for c in courses if c.get("workflow_state") == "available"])
            },
            "recent_courses": {
                "title": "Recently Created Courses",
                "items": [{"id": c.get("id"), "name": c.get("name"), "code": c.get("course_code")} for c in courses[-5:]]
            }
        }
        return widgets
    
    def _get_pending_assignments(self, courses: List[Dict]) -> Dict:
        """Get pending assignments across all courses"""
        pending = []
        for course in courses[:3]:
            try:
                assignments = self.canvas.list_modules(course.get("id"))
                # Simplified - in real implementation, check due dates
                pending.extend([{"course": course.get("name"), "title": "Assignments available"} for _ in range(min(2, len(assignments)))])
            except:
                pass
        
        return {
            "title": "Pending Tasks",
            "count": len(pending),
            "items": pending[:5]
        }
    
    def _get_recent_announcements(self, courses: List[Dict]) -> Dict:
        """Get recent announcements"""
        announcements = []
        for course in courses[:3]:
            try:
                # Simplified - would fetch actual announcements
                announcements.append({
                    "course": course.get("name"),
                    "title": "Check course updates"
                })
            except:
                pass
        
        return {
            "title": "Recent Announcements",
            "count": len(announcements),
            "items": announcements[:3]
        }
    
    def _get_course_stats(self, courses: List[Dict]) -> Dict:
        """Get statistics for teacher's courses"""
        stats = {
            "title": "Course Statistics",
            "total_courses": len(courses),
            "published": len([c for c in courses if c.get("workflow_state") == "available"]),
            "unpublished": len([c for c in courses if c.get("workflow_state") != "available"])
        }
        return stats
    
    def _get_unpublished_courses(self, courses: List[Dict]) -> Dict:
        """Get unpublished courses that need attention"""
        unpublished = [c for c in courses if c.get("workflow_state") != "available"]
        return {
            "title": "Courses Needing Attention",
            "count": len(unpublished),
            "items": [{"id": c.get("id"), "name": c.get("name"), "action": "Publish course"} for c in unpublished[:3]]
        }
