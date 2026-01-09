import logging
import re
from typing import Dict, List, Any, Callable
from canvas_integration import CanvasLMS
from canvas_tools_schemas import CanvasToolSchemas

logger = logging.getLogger(__name__)

class CanvasTools:
    """Universal Canvas LMS tool executor"""

    def __init__(
        self,
        canvas: CanvasLMS,
        admin_canvas: CanvasLMS,
        user_role: str | None = None,
        user_info: dict | None = None,
    ):
        self.canvas = canvas
        self.admin_canvas = admin_canvas
        self.user_role = user_role or "default"
        self.user_info = user_info or {}
        self.canvas_user_id = self.user_info.get("canvas_user_id")

        logger.info(
            f"Initialized role={self.user_role}, "
            f"user_id={self.canvas_user_id}"
        )

        self._dispatch: Dict[str, Callable[[dict], Any]] = {
            "list_user_courses": self._list_user_courses,
            "get_course": self._get_course,
            "create_course": self._create_course,
            "update_course": self._update_course,
            "publish_course": self._publish_course,
            "unpublish_course": self._unpublish_course,
            "list_modules": self._list_modules,
            "get_module": self._get_module,
            "create_module": self._create_module,
            "create_multiple_modules": self._create_multiple_modules,
            "update_module": self._update_module,
            "delete_module": self._delete_module,
            "add_module_item": self._add_module_item,
            "list_module_items": self._list_module_items,
            "list_assignments": self._list_assignments,
            "get_assignment": self._get_assignment,
            "create_assignment": self._create_assignment,
            "update_assignment": self._update_assignment,
            "delete_assignment": self._delete_assignment,
            "grade_assignment": self._grade_assignment,
            "submit_assignment": self._submit_assignment,
            "list_users": self._list_users,
            "create_user": self._create_user,
            "enroll_user": self._enroll_user,
            "unenroll_user": self._unenroll_user,
            "list_enrollments": self._list_enrollments,
            "list_course_users": self._list_course_users,
            "get_user_profile": self._get_user_profile,
            "list_announcements": self._list_announcements,
            "create_announcement": self._create_announcement,
            "list_discussions": self._list_discussions,
            "create_discussion": self._create_discussion,
            "list_quizzes": self._list_quizzes,
            "create_quiz": self._create_quiz,
            "create_quiz_question": self._create_quiz_question,
            "list_pages": self._list_pages,
            "create_page": self._create_page,
            "list_files": self._list_files,
            "upload_file": self._upload_file,
            "get_grades": self._get_grades,
            "view_gradebook": self._view_gradebook,
        }

    # ------------------------------------------------------------------
    # Tool definitions (LLM-visible)
    # ------------------------------------------------------------------

    @staticmethod
    def get_tool_definitions(user_role: str | None = None) -> List[Dict[str, Any]]:
        tools = [
            CanvasToolSchemas.list_user_courses(),
            CanvasToolSchemas.get_course(),
            CanvasToolSchemas.create_course(),
            CanvasToolSchemas.update_course(),
            CanvasToolSchemas.publish_course(),
            CanvasToolSchemas.unpublish_course(),
            CanvasToolSchemas.list_modules(),
            CanvasToolSchemas.create_module(),
            CanvasToolSchemas.create_multiple_modules(),
            CanvasToolSchemas.add_module_item(),
            CanvasToolSchemas.list_module_items(),
            CanvasToolSchemas.list_assignments(),
            CanvasToolSchemas.get_assignment(),
            CanvasToolSchemas.create_assignment(),
            CanvasToolSchemas.grade_assignment(),
            # CanvasToolSchemas.submit_assignment(),
            CanvasToolSchemas.enroll_user(),
            CanvasToolSchemas.list_users(),
            CanvasToolSchemas.list_course_users(),
            CanvasToolSchemas.create_page(),
            CanvasToolSchemas.list_pages(),
            CanvasToolSchemas.create_discussion(),
            CanvasToolSchemas.create_quiz(),
            CanvasToolSchemas.list_quizzes(),
            CanvasToolSchemas.create_quiz_question(),
            # CanvasToolSchemas.list_enrollments(),
            # CanvasToolSchemas.get_user_profile(),
        ]

        role = user_role or "default"

        ROLE_MAP = {
            "student": {
                "list_user_courses", "get_course", "list_modules", "get_module",
                "list_assignments", "get_assignment", "submit_assignment",
                "list_announcements", "list_discussions", "list_quizzes",
                "list_pages", "list_files", "get_grades", "get_user_profile"
            },
            "teacher": {
                "list_user_courses", "get_course", "create_course", "update_course", "publish_course", "unpublish_course",
                "list_modules", "get_module", "create_module", "update_module", "delete_module", "add_module_item", "list_module_items", "create_multiple_modules",
                "list_assignments", "get_assignment", "create_assignment", "update_assignment", "delete_assignment", "grade_assignment",
                "enroll_user", "list_enrollments", "list_course_users",
                "list_announcements", "create_announcement",
                "list_discussions", "create_discussion",
                "list_quizzes", "create_quiz", "create_quiz_question",
                "list_pages", "create_page", "create_page",
                "list_files", "upload_file",
                "get_grades", "view_gradebook"
            },
            "admin": {t["function"]["name"] for t in tools},
        }
        ROLE_MAP['faculty'] = ROLE_MAP['teacher']
        ROLE_MAP['instructor'] = ROLE_MAP['teacher']
        
        allowed = ROLE_MAP.get(role, {"list_user_courses", "get_course"})
        return [t for t in tools if t["function"]["name"] in allowed]

    # ------------------------------------------------------------------
    # Tool executor
    # ------------------------------------------------------------------

    def execute_tool(self, function_name: str, arguments: dict) -> Dict[str, Any]:
        handler = self._dispatch.get(function_name)
        if not handler:
            return {"error": f"Unknown function: {function_name}"}

        try:
            logger.info(f"Executing Tool: {function_name}")
            result = handler(arguments)
            print(f"Tool Result: {result}")
            return result
        except Exception as exc:
            logger.error(f"execute_tool exception: {exc}", exc_info=True)
            return {"error": str(exc)}

    # ------------------------------------------------------------------
    # Tool handlers
    # ------------------------------------------------------------------

    def _list_user_courses(self, _: dict):
        courses = (
            self.admin_canvas.list_account_courses()
            if self.user_role == "admin"
            else self.canvas.list_courses()
        )
        return {
            "total_courses": len(courses),
            "courses": [
                {
                    "id": c.get("id"),
                    "name": c.get("name"),
                    "course_code": c.get("course_code"),
                    "workflow_state": c.get("workflow_state"),
                }
                for c in courses
            ],
        }

    def _get_course(self, args: dict):
        print(f"[CANVAS_TOOLS] [Arguments] {args}")
        return self.canvas.get_course(args["course_id"])

    def _create_course(self, args: dict):
        print(f"[CANVAS_TOOLS] [Arguments] {args}")
        # Ensure there's a course_code; generate one from the name if missing
        name = args.get("name")
        course_code = args.get("course_code")
        if not course_code and name:
            # Uppercase, keep alphanumeric, truncate to 10 chars
            cleaned = re.sub(r'[^0-9A-Za-z]', '', name).upper()
            course_code = cleaned[:10] if cleaned else f"C{int(__import__('time').time())}"

        course = self.admin_canvas.create_course(
            account_id=1,
            name=name,
            course_code=course_code,
            description=args.get("description"),
        )
        print(f"[CANVAS_TOOLS] create_course result type: {type(course)}")
        print(f"[CANVAS_TOOLS] create_course result: {course}")

        if (
            self.user_role in {"teacher", "faculty", "instructor"}
            and self.canvas_user_id
            and course.get("id")
        ):
            self.admin_canvas.enroll_user(
                course_id=course["id"],
                user_id=self.canvas_user_id,
                role="TeacherEnrollment",
            )
            course["auto_enrolled"] = True

        return course

    def _publish_course(self, args: dict):
        print(f"[CANVAS_TOOLS] [Arguments] {args}")
        return self.admin_canvas.update_course(
            args["course_id"], {"event": "offer"}
        )

    def _unpublish_course(self, args: dict):
        print(f"[CANVAS_TOOLS] [Arguments] {args}")
        return self.admin_canvas.update_course(
            args["course_id"], {"event": "claim"}
        )

    def _list_modules(self, args: dict):
        print(f"[CANVAS_TOOLS] [Arguments] {args}")
        return self.canvas.list_modules(args["course_id"])

    def _create_module(self, args: dict):
        print(f"[CANVAS_TOOLS] [Arguments] {args}")
        return self.canvas.create_module(
            course_id=args["course_id"],
            name=args["name"],
            position=args.get("position"),
        )

    def _create_multiple_modules(self, args: dict):
        course_id = args["course_id"]
        module_names = args["module_names"]
        results = []
        for idx, name in enumerate(module_names, start=1):
            try:
                result = self.canvas.create_module(
                    course_id=course_id,
                    name=name,
                    position=idx
                )
                results.append({"name": name, "status": "created", "id": result.get("id")})
            except Exception as e:
                results.append({"name": name, "status": "failed", "error": str(e)})
        return {"course_id": course_id, "modules": results}

    def _list_assignments(self, args: dict):
        print(f"[CANVAS_TOOLS] [Arguments] {args}")
        return self.canvas.list_assignments(args["course_id"])

    def _get_assignment(self, args: dict):
        return self.canvas.get_assignment(
            args["course_id"], args["assignment_id"]
        )

    def _create_assignment(self, args: dict):
        print(f"[CANVAS_TOOLS] [Arguments] {args}")
        return self.canvas.create_assignment(args["course_id"], args)

    def _grade_assignment(self, args: dict):
        print(f"[CANVAS_TOOLS] [Arguments] {args}")
        if self.user_role not in {"admin", "teacher", "faculty", "instructor"}:
            return {"error": "Permission denied"}
        return self.canvas.grade_assignment(**args)

    def _submit_assignment(self, args: dict):
        print(f"[CANVAS_TOOLS] [Arguments] {args}")
        return self.canvas.submit_assignment(**args)

    def _list_users(self, _: dict):
        users = self.admin_canvas.list_users()
        return {
            "total_users": len(users),
            "users": [
                {
                    "id": u.get("id"),
                    "name": u.get("name"),
                    "login_id": u.get("login_id"),
                }
                for u in users
            ],
        }

    def _enroll_user(self, args: dict):
        print(f"[CANVAS_TOOLS] [Arguments] {args}")
        return self.admin_canvas.enroll_user(**args)

    def _list_enrollments(self, args: dict):
        print(f"[CANVAS_TOOLS] [Arguments] {args}")
        return self.canvas.list_enrollments(args["course_id"])

    def _get_user_profile(self, args: dict):
        print(f"[CANVAS_TOOLS] [Arguments] {args}")
        return self.canvas.get_user_profile(args["user_id"])

    def _update_course(self, args: dict):
        return self.admin_canvas.update_course(args["course_id"], args)

    def _update_assignment(self, args: dict):
        return self.canvas.update_assignment(args["course_id"], args["assignment_id"], args)

    def _delete_assignment(self, args: dict):
        return self.canvas.delete_assignment(args["course_id"], args["assignment_id"])

    def _get_module(self, args: dict):
        return self.canvas.get_module(args["course_id"], args["module_id"])

    def _update_module(self, args: dict):
        return self.canvas.update_module(args["course_id"], args["module_id"], args)

    def _delete_module(self, args: dict):
        return self.canvas.delete_module(args["course_id"], args["module_id"])

    def _create_user(self, args: dict):
        return self.admin_canvas.create_user(1, args["name"], args["email"], args["login_id"])

    def _unenroll_user(self, args: dict):
        return self.admin_canvas.unenroll_user(args["course_id"], args["enrollment_id"])

    def _list_announcements(self, args: dict):
        return self.canvas.list_announcements(args["course_id"])

    def _create_announcement(self, args: dict):
        return self.canvas.create_announcement(args["course_id"], args["title"], args["message"])

    def _list_discussions(self, args: dict):
        return self.canvas.list_discussions(args["course_id"])

    def _create_discussion(self, args: dict):
        return self.canvas.create_discussion(args["course_id"], args["title"], args["message"])

    def _list_quizzes(self, args: dict):
        return self.canvas.list_quizzes(args["course_id"])

    def _create_quiz(self, args: dict):
        return self.canvas.create_quiz(args["course_id"], args["title"])

    def _create_quiz_question(self, args: dict):
        return self.canvas.create_quiz_question(
            args["course_id"],
            args["quiz_id"],
            args["question_name"],
            args["question_text"],
            args.get("question_type", "multiple_choice_question"),
            args.get("points_possible", 1),
            args.get("answers")
        )

    def _list_pages(self, args: dict):
        return self.canvas.list_pages(args["course_id"])

    def _create_page(self, args: dict):
        return self.canvas.create_page(args["course_id"], args["title"], args.get("body", ""))

    def _list_files(self, args: dict):
        return self.canvas.list_files(args["course_id"])

    def _upload_file(self, args: dict):
        return self.canvas.upload_file(args["course_id"], args["file_name"])

    def _get_grades(self, args: dict):
        return self.canvas.get_grades(args["course_id"], args.get("user_id"))

    def _view_gradebook(self, args: dict):
        return self.canvas.view_gradebook(args["course_id"])

    def _add_module_item(self, args: dict):
        return self.canvas.add_module_item(
            args["course_id"],
            args["module_id"],
            args["item_type"],
            content_id=args.get("content_id"),
            title=args.get("title"),
            page_url=args.get("page_url")
        )

    def _list_module_items(self, args: dict):
        return self.canvas.list_module_items(args["course_id"], args["module_id"])

    def _list_course_users(self, args: dict):
        return self.canvas.list_course_users(args["course_id"])
