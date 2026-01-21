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

    @staticmethod
    def unpublish_course() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "unpublish_course",
                "description": "Unpublish a course",
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
    def update_course() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "update_course",
                "description": "Update course details like name, code, or description",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                        "name": {"type": "string"},
                        "course_code": {"type": "string"},
                        "description": {"type": "string"},
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
    # Discussions
    # ------------------------------------------------------------------

    @staticmethod
    def create_discussion() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_discussion",
                "description": "Create a discussion topic in a course",
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
    # Quizzes
    # ------------------------------------------------------------------

    @staticmethod
    def create_quiz() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_quiz",
                "description": "Create a quiz in a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                        "title": {"type": "string"},
                        "description": {"type": "string"},
                        "quiz_type": {
                            "type": "string",
                            "description": "practice_quiz, assignment, or graded_survey",
                        },
                    },
                    "required": ["course_id", "title"],
                },
            },
        }# ------------------------------------------------------------------
    # Pages
    # ------------------------------------------------------------------

    @staticmethod
    def create_page() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_page",
                "description": "Create a content page in a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                        "title": {"type": "string"},
                        "body": {"type": "string"},
                    },
                    "required": ["course_id", "title", "body"],
                },
            },
        }# ------------------------------------------------------------------
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

    @staticmethod
    def update_course():
        return {
            "type": "function",
            "function": {
                "name": "update_course",
                "description": "Update course settings",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "name": {"type": "string", "description": "New course name"},
                        "course_code": {"type": "string", "description": "New course code"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    @staticmethod
    def update_assignment():
        return {
            "type": "function",
            "function": {
                "name": "update_assignment",
                "description": "Update an assignment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "assignment_id": {"type": "integer", "description": "Assignment ID"},
                        "name": {"type": "string", "description": "Assignment name"},
                        "points_possible": {"type": "number", "description": "Points possible"},
                    },
                    "required": ["course_id", "assignment_id"],
                },
            },
        }

    @staticmethod
    def delete_assignment():
        return {
            "type": "function",
            "function": {
                "name": "delete_assignment",
                "description": "Delete an assignment",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "assignment_id": {"type": "integer", "description": "Assignment ID"},
                    },
                    "required": ["course_id", "assignment_id"],
                },
            },
        }

    @staticmethod
    def get_module():
        return {
            "type": "function",
            "function": {
                "name": "get_module",
                "description": "Get module details",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "module_id": {"type": "integer", "description": "Module ID"},
                    },
                    "required": ["course_id", "module_id"],
                },
            },
        }

    @staticmethod
    def update_module():
        return {
            "type": "function",
            "function": {
                "name": "update_module",
                "description": "Update a module",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "module_id": {"type": "integer", "description": "Module ID"},
                        "name": {"type": "string", "description": "Module name"},
                    },
                    "required": ["course_id", "module_id"],
                },
            },
        }

    @staticmethod
    def delete_module():
        return {
            "type": "function",
            "function": {
                "name": "delete_module",
                "description": "Delete a module",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "module_id": {"type": "integer", "description": "Module ID"},
                    },
                    "required": ["course_id", "module_id"],
                },
            },
        }

    @staticmethod
    def create_user():
        return {
            "type": "function",
            "function": {
                "name": "create_user",
                "description": "Create a new user",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "User full name"},
                        "email": {"type": "string", "description": "User email"},
                        "login_id": {"type": "string", "description": "Login ID"},
                    },
                    "required": ["name", "email", "login_id"],
                },
            },
        }

    @staticmethod
    def unenroll_user():
        return {
            "type": "function",
            "function": {
                "name": "unenroll_user",
                "description": "Unenroll a user from a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "enrollment_id": {"type": "integer", "description": "Enrollment ID"},
                    },
                    "required": ["course_id", "enrollment_id"],
                },
            },
        }

    @staticmethod
    def list_announcements():
        return {
            "type": "function",
            "function": {
                "name": "list_announcements",
                "description": "List course announcements",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    @staticmethod
    def list_discussions():
        return {
            "type": "function",
            "function": {
                "name": "list_discussions",
                "description": "List course discussions",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    @staticmethod
    def list_quizzes():
        return {
            "type": "function",
            "function": {
                "name": "list_quizzes",
                "description": "List course quizzes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    @staticmethod
    def create_quiz():
        return {
            "type": "function",
            "function": {
                "name": "create_quiz",
                "description": "Create a quiz",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "title": {"type": "string", "description": "Quiz title"},
                    },
                    "required": ["course_id", "title"],
                },
            },
        }

    @staticmethod
    def list_pages():
        return {
            "type": "function",
            "function": {
                "name": "list_pages",
                "description": "List course pages",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    @staticmethod
    def list_files():
        return {
            "type": "function",
            "function": {
                "name": "list_files",
                "description": "List course files",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    @staticmethod
    def upload_file():
        return {
            "type": "function",
            "function": {
                "name": "upload_file",
                "description": "Upload a file to course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "file_name": {"type": "string", "description": "File name"},
                    },
                    "required": ["course_id", "file_name"],
                },
            },
        }

    @staticmethod
    def get_grades():
        return {
            "type": "function",
            "function": {
                "name": "get_grades",
                "description": "Get student grades",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "user_id": {"type": "integer", "description": "User ID (optional)"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    @staticmethod
    def view_gradebook():
        return {
            "type": "function",
            "function": {
                "name": "view_gradebook",
                "description": "View course gradebook",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    @staticmethod
    def create_quiz_question():
        return {
            "type": "function",
            "function": {
                "name": "create_quiz_question",
                "description": "Create a question in a quiz",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "quiz_id": {"type": "integer", "description": "Quiz ID"},
                        "question_name": {"type": "string", "description": "Question name"},
                        "question_text": {"type": "string", "description": "Question text"},
                        "question_type": {"type": "string", "description": "Question type (multiple_choice_question, true_false_question, essay_question)"},
                        "points_possible": {"type": "integer", "description": "Points possible"},
                        "answers": {
                            "type": "array",
                            "description": "Array of answer objects with text and weight (100 for correct, 0 for incorrect)",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "weight": {"type": "integer"}
                                }
                            }
                        }
                    },
                    "required": ["course_id", "quiz_id", "question_name", "question_text"],
                },
            },
        }

    @staticmethod
    def add_module_item():
        return {
            "type": "function",
            "function": {
                "name": "add_module_item",
                "description": "Add item to module. For Page: use page_url from list_pages url field. For Assignment/Quiz: use content_id.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "module_id": {"type": "integer", "description": "Module ID"},
                        "item_type": {"type": "string", "description": "Type: Assignment, Quiz, Page, Discussion"},
                        "content_id": {"type": "integer", "description": "ID for Assignment/Quiz/Discussion"},
                        "page_url": {"type": "string", "description": "URL slug for Page (from url field in list_pages)"},
                        "title": {"type": "string", "description": "Display title for the item"},
                    },
                    "required": ["course_id", "module_id", "item_type"],
                },
            },
        }

    @staticmethod
    def list_module_items():
        return {
            "type": "function",
            "function": {
                "name": "list_module_items",
                "description": "List all items in a module",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "module_id": {"type": "integer", "description": "Module ID"},
                    },
                    "required": ["course_id", "module_id"],
                },
            },
        }

    @staticmethod
    def list_pages():
        return {
            "type": "function",
            "function": {
                "name": "list_pages",
                "description": "List all pages in a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    @staticmethod
    def list_course_users():
        return {
            "type": "function",
            "function": {
                "name": "list_course_users",
                "description": "List all users enrolled in a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    @staticmethod
    def post_discussion_reply():
        return {
            "type": "function",
            "function": {
                "name": "post_discussion_reply",
                "description": "Post a reply to a discussion topic",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "topic_id": {"type": "integer", "description": "Discussion topic ID"},
                        "message": {"type": "string", "description": "Reply message"},
                    },
                    "required": ["course_id", "topic_id", "message"],
                },
            },
        }

    @staticmethod
    def get_upcoming_assignments():
        return {
            "type": "function",
            "function": {
                "name": "get_upcoming_assignments",
                "description": "Get upcoming assignments and events across all courses",
                "parameters": {"type": "object", "properties": {}},
            },
        }

    @staticmethod
    def get_course_progress():
        return {
            "type": "function",
            "function": {
                "name": "get_course_progress",
                "description": "Get student progress and analytics in a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                    },
                    "required": ["course_id"],
                },
            },
        }

    @staticmethod
    def create_multiple_modules():
        return {
            "type": "function",
            "function": {
                "name": "create_multiple_modules",
                "description": "Create multiple modules at once in a course",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "module_names": {
                            "type": "array",
                            "description": "Array of module names to create",
                            "items": {"type": "string"}
                        },
                    },
                    "required": ["course_id", "module_names"],
                },
            },
        }





    @staticmethod
    def get_rubric():
        return {
            "type": "function",
            "function": {
                "name": "get_rubric",
                "description": "Get assignment rubric and grading criteria",
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
    def get_page_content():
        return {
            "type": "function",
            "function": {
                "name": "get_page_content",
                "description": "Get page content for context-aware help",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                        "page_url": {"type": "string"},
                    },
                    "required": ["course_id", "page_url"],
                },
            },
        }

    @staticmethod
    def get_student_analytics():
        return {
            "type": "function",
            "function": {
                "name": "get_student_analytics",
                "description": "Get detailed student performance analytics",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer"},
                        "user_id": {"type": "integer"},
                    },
                    "required": ["course_id", "user_id"],
                },
            },
        }
