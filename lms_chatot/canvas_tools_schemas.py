from typing import Dict, Any


class CanvasToolSchemas:
    """
    Central registry of Canvas LMS LLM tool schemas.
    These define WHAT the model can call.
    Execution happens inside CanvasTools.
    """

    # ------------------------------------------------------------------
    # Courses
    # ------------------------------------------------------------------

    @staticmethod
    def list_user_courses() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_user_courses",
                "description": "List all courses for the current user",
                "parameters": {"type": "object", "properties": {}},
            },
        }

    @staticmethod
    def get_course() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_course",
                "description": "Get detailed information about a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    @staticmethod
    def create_course() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_course",
                "description": "Create a new Canvas course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "course_code": {"type": "string"},
                        "description": {"type": "string"},
                    },
                    "required": ["name", "course_code"],
                },
            },
        }

    @staticmethod
    def publish_course() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "publish_course",
                "description": "Publish a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    # ------------------------------------------------------------------
    # Modules
    # ------------------------------------------------------------------

    @staticmethod
    def list_modules() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_modules",
                "description": "List all modules in a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    @staticmethod
    def create_module() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_module",
                "description": "Create a new module in a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                        "name": {"type": "string"},
                        "position": {"type": "integer"},
                    },
                    "required": ["course_id", "name"],
                },
            },
        }

    # ------------------------------------------------------------------
    # Assignments
    # ------------------------------------------------------------------

    @staticmethod
    def list_assignments() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_assignments",
                "description": "List assignments in a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    @staticmethod
    def get_assignment() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "get_assignment",
                "description": "Get details of a specific assignment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                        "assignment_id": {"type": "integer"},
                    },
                    "required": ["course_id", "assignment_id"],
                },
            },
        }

    @staticmethod
    def create_assignment() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_assignment",
                "description": "Create an assignment in a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "points_possible": {"type": "number"},
                        "due_at": {"type": "string"},
                    },
                    "required": ["course_id", "name"],
                },
            },
        }

    @staticmethod
    def grade_assignment() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "grade_assignment",
                "description": "Grade a student's assignment submission",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                        "assignment_id": {"type": "integer"},
                        "user_id": {"type": "integer"},
                        "grade": {"type": "number"},
                    },
                    "required": [
                        "course_id",
                        "assignment_id",
                        "user_id",
                        "grade",
                    ],
                },
            },
        }

    # ------------------------------------------------------------------
    # Enrollments & Users
    # ------------------------------------------------------------------

    @staticmethod
    def enroll_user() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "enroll_user",
                "description": "Enroll a user into a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                        "user_id": {"type": "integer"},
                        "role": {
                            "type": "string",
                            "description": "StudentEnrollment or TeacherEnrollment",
                        },
                    },
                    "required": ["course_id", "user_id", "role"],
                },
            },
        }

    @staticmethod
    def list_users() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_users",
                "description": "List all users in the Canvas account (admin only)",
                "parameters": {"type": "object", "properties": {}},
            },
        }

    # ------------------------------------------------------------------
    # Submissions & Grades
    # ------------------------------------------------------------------

    @staticmethod
    def list_submissions() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_submissions",
                "description": "List student submissions for an assignment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                        "assignment_id": {"type": "integer"},
                    },
                    "required": ["course_id", "assignment_id"],
                },
            },
        }

    # ------------------------------------------------------------------
    # Announcements
    # ------------------------------------------------------------------

    @staticmethod
    def create_announcement() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_announcement",
                "description": "Post an announcement to a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                        "title": {"type": "string"},
                        "message": {"type": "string"},
                    },
                    "required": ["course_id", "title", "message"],
                },
            },
        }

    # ------------------------------------------------------------------
    # Files
    # ------------------------------------------------------------------

    @staticmethod
    def list_course_files() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "list_course_files",
                "description": "List files uploaded to a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def all() -> list:
        """Return all schemas"""
        return [
            CanvasToolSchemas.list_user_courses(),
            CanvasToolSchemas.get_course(),
            CanvasToolSchemas.create_course(),
            CanvasToolSchemas.publish_course(),
            CanvasToolSchemas.list_modules(),
            CanvasToolSchemas.create_module(),
            CanvasToolSchemas.list_assignments(),
            CanvasToolSchemas.get_assignment(),
            CanvasToolSchemas.create_assignment(),
            CanvasToolSchemas.grade_assignment(),
            CanvasToolSchemas.enroll_user(),
            CanvasToolSchemas.list_users(),
            CanvasToolSchemas.list_submissions(),
            CanvasToolSchemas.create_announcement(),
            CanvasToolSchemas.list_course_files(),
        ]
