from typing import Dict, List, Any
from canvas_integration import CanvasLMS
from student_features import StudentFeatures
from video_generators.video_manager import VideoManager

class CanvasTools:
    """Universal Canvas LMS tools for all inference systems"""
    
    def __init__(self, canvas: CanvasLMS, admin_canvas: CanvasLMS, user_role: str = None, user_info: dict = None):
        self.canvas = canvas
        self.admin_canvas = admin_canvas
        self.user_role = user_role
        self.user_info = user_info
        self.canvas_user_id = user_info.get('canvas_user_id') if user_info else None
        print(f"[CANVAS_TOOLS] Initialized for user_id={self.canvas_user_id}, role={self.user_role}")
    
    @staticmethod
    def get_tool_definitions(user_role: str = None) -> List[Dict[str, Any]]:
        """Get comprehensive Canvas tool definitions for all inference systems"""
        tools = [
            # Core Canvas operations mapped to intents
            {
                "type": "function",
                "function": {
                    "name": "list_user_courses",
                    "description": "List courses for the user",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function", 
                "function": {
                    "name": "get_course",
                    "description": "Get detailed course information",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "Course ID"}
                        },
                        "required": ["course_id"]
                    }
                }
            },

            {
                "type": "function",
                "function": {
                    "name": "create_course",
                    "description": "Create a new course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "description": "Course name"},
                            "course_code": {"type": "string", "description": "Course code"},
                            "description": {"type": "string", "description": "Course description"}
                        },
                        "required": ["name", "course_code"]
                    }
                }
            },

            
            {
                "type": "function",
                "function": {
                    "name": "list_modules",
                    "description": "List modules in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "Course ID"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_module",
                    "description": "Create a new module in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "Course ID"},
                            "name": {"type": "string", "description": "Module name"},
                            "position": {"type": "integer", "description": "Module position"}
                        },
                        "required": ["course_id", "name"]
                    }
                }
            },

            
            {
                "type": "function",
                "function": {
                    "name": "list_assignments",
                    "description": "List assignments in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "Course ID"}
                        },
                        "required": ["course_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_assignment",
                    "description": "Get specific assignment details",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "Course ID"},
                            "assignment_id": {"type": "integer", "description": "Assignment ID"}
                        },
                        "required": ["course_id", "assignment_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "grade_assignment",
                    "description": "Grade an assignment submission",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "Course ID"},
                            "assignment_id": {"type": "integer", "description": "Assignment ID"},
                            "user_id": {"type": "integer", "description": "Student ID"},
                            "grade": {"type": "number", "description": "Grade to assign"}
                        },
                        "required": ["course_id", "assignment_id", "user_id", "grade"]
                    }
                }
            },

            
            {
                "type": "function",
                "function": {
                    "name": "enroll_user",
                    "description": "Enroll user in course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "Course ID"},
                            "user_id": {"type": "integer", "description": "User ID"},
                            "role": {"type": "string", "description": "StudentEnrollment or TeacherEnrollment"}
                        },
                        "required": ["course_id", "user_id", "role"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_users",
                    "description": "List all users in the account (admin only)",
                    "parameters": {"type": "object", "properties": {}}
                }
            },

        ]
        
        # Role-based tool filtering
        if user_role == "student":
            student_tools = ["list_user_courses", "list_modules", "get_course", "list_assignments", "get_assignment"]
            tools = [t for t in tools if t["function"]["name"] in student_tools]
            
        elif user_role in ["teacher", "faculty", "instructor"]:
            # Teachers get most tools except admin-only functions
            admin_only = ["list_users"]
            tools = [t for t in tools if t["function"]["name"] not in admin_only]
            
        elif user_role == "admin":
            # Admins get all tools
            return tools
            
        else:
            # Default role gets basic read-only tools
            basic_tools = ["list_user_courses", "list_modules", "get_course"]
            tools = [t for t in tools if t["function"]["name"] in basic_tools]
            
        return tools
    
    def execute_tool(self, function_name: str, arguments: dict) -> Dict[str, Any]:
        """Execute Canvas tool - universal for all inference systems"""
        try:
            if function_name == "list_user_courses":
                print(f"[CANVAS_TOOLS] list_user_courses for role={self.user_role}, user_id={self.canvas_user_id}")
                
                if self.user_role == "admin":
                    courses = self.admin_canvas.list_account_courses()
                else:
                    courses = self.canvas.list_courses()
                
                print(f"[CANVAS_TOOLS] Found {len(courses)} courses")
                return {
                    "total_courses": len(courses),
                    "courses": [{
                        "id": c.get("id"), 
                        "name": c.get("name"), 
                        "course_code": c.get("course_code"),
                        "workflow_state": c.get("workflow_state")
                    } for c in courses]
                }
                
            elif function_name == "get_course":
                course = self.canvas.get_course(arguments["course_id"])
                return course
                
            elif function_name == "list_assignments":
                assignments = self.canvas.list_assignments(arguments["course_id"])
                return {"assignments": assignments}
                
            elif function_name == "get_assignment":
                assignment = self.canvas.get_assignment(arguments["course_id"], arguments["assignment_id"])
                return assignment
                
            elif function_name == "grade_assignment":
                if self.user_role not in ["admin", "teacher", "faculty", "instructor"]:
                    return {"error": "Only teachers and admins can grade assignments"}
                
                result = self.canvas.grade_assignment(
                    course_id=arguments["course_id"],
                    assignment_id=arguments["assignment_id"],
                    user_id=arguments["user_id"],
                    grade=arguments["grade"]
                )
                return result
                
            elif function_name == "list_courses":
                # Legacy support - redirect to list_user_courses
                return self.execute_tool("list_user_courses", {})
                
            # Course Management
            elif function_name == "create_course":
                print(f"[CANVAS_TOOLS] create_course: {arguments['name']} by role={self.user_role}")
                
                result = self.admin_canvas.create_course(
                    account_id=1,
                    name=arguments["name"],
                    course_code=arguments["course_code"],
                    description=arguments.get("description")
                )
                
                if self.user_role in ["teacher", "faculty", "instructor"] and self.canvas_user_id and result.get("id"):
                    try:
                        print(f"[CANVAS_TOOLS] Auto-enrolling teacher {self.canvas_user_id} in course {result['id']}")
                        self.admin_canvas.enroll_user(
                            course_id=result["id"],
                            user_id=self.canvas_user_id,
                            role="TeacherEnrollment"
                        )
                        result["auto_enrolled"] = True
                    except Exception as e:
                        print(f"[CANVAS_TOOLS] Auto-enrollment failed: {e}")
                
                print(f"[CANVAS_TOOLS] Course created: ID={result.get('id')}")
                return result
                

                
            # Module Management
            elif function_name == "list_modules":
                modules = self.canvas.list_modules(arguments["course_id"])
                return modules
                
            elif function_name == "create_module":
                result = self.canvas.create_module(
                    course_id=arguments["course_id"],
                    name=arguments["name"],
                    position=arguments.get("position")
                )
                return result
                

                

                

                

                
            elif function_name == "list_users":
                users = self.admin_canvas.list_users()
                return {
                    "total_users": len(users),
                    "users": [{"id": u.get("id"), "name": u.get("name"), "login_id": u.get("login_id")} for u in users]
                }
                
            elif function_name == "enroll_user":
                result = self.admin_canvas.enroll_user(
                    course_id=arguments["course_id"],
                    user_id=arguments["user_id"],
                    role=arguments["role"]
                )
                return result
                

                

                
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            return {"error": str(e)}
    
