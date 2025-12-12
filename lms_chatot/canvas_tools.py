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
    
    @staticmethod
    def get_tool_definitions(user_role: str = None) -> List[Dict[str, Any]]:
        """Get Canvas tool definitions for all inference systems"""
        tools = [
            {
                "name": "list_courses",
                "description": "List courses for the user",
                "input_schema": {"type": "object", "properties": {}}
            },
            {
                "name": "create_course",
                "description": "Create a new course",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Course name"},
                        "course_code": {"type": "string", "description": "Course code"}
                    },
                    "required": ["name", "course_code"]
                }
            },
            {
                "name": "list_modules",
                "description": "List modules in a course",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"}
                    },
                    "required": ["course_id"]
                }
            },
            {
                "name": "create_assignment",
                "description": "Create an assignment",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "name": {"type": "string", "description": "Assignment name"},
                        "points": {"type": "integer", "description": "Points (default 100)"}
                    },
                    "required": ["course_id", "name"]
                }
            },
            {
                "name": "create_user",
                "description": "Create a new user (admin only)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Full name"},
                        "email": {"type": "string", "description": "Email address"},
                        "login_id": {"type": "string", "description": "Login username"}
                    },
                    "required": ["name", "email", "login_id"]
                }
            },
            {
                "name": "enroll_user",
                "description": "Enroll user in course",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "user_id": {"type": "integer", "description": "User ID"},
                        "role": {"type": "string", "description": "StudentEnrollment or TeacherEnrollment"}
                    },
                    "required": ["course_id", "user_id", "role"]
                }
            },
            {
                "name": "generate_learning_plan",
                "description": "Generate personalized learning plan for student",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "study_hours_per_week": {"type": "integer", "description": "Hours per week (default 10)"}
                    },
                    "required": ["course_id"]
                }
            },
            {
                "name": "get_progress_tracker",
                "description": "Get learning progress across all courses",
                "input_schema": {"type": "object", "properties": {}}
            },
            {
                "name": "get_study_recommendations",
                "description": "Get AI-powered study recommendations",
                "input_schema": {"type": "object", "properties": {}}
            },
            {
                "name": "get_assignment_prioritizer",
                "description": "Smart assignment prioritization and scheduling",
                "input_schema": {"type": "object", "properties": {}}
            },
            {
                "name": "generate_video_quiz",
                "description": "Generate AI video quiz for a course topic (teacher only)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Quiz topic"},
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "duration": {"type": "integer", "description": "Video duration in seconds (default 300)"},
                        "difficulty": {"type": "string", "description": "Quiz difficulty: easy, medium, hard"}
                    },
                    "required": ["topic", "course_id"]
                }
            },
            {
                "name": "generate_educational_video",
                "description": "Generate AI educational video content (teacher only)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "topic": {"type": "string", "description": "Video topic"},
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "duration": {"type": "integer", "description": "Video duration in seconds (default 300)"},
                        "style": {"type": "string", "description": "Video style: lecture, tutorial, animated, documentary"}
                    },
                    "required": ["topic", "course_id"]
                }
            },
            {
                "name": "upload_assignment_file",
                "description": "Upload file and create assignment (teacher only)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "assignment_name": {"type": "string", "description": "Assignment name"},
                        "file_path": {"type": "string", "description": "Local file path"},
                        "points": {"type": "integer", "description": "Points possible (default 100)"},
                        "description": {"type": "string", "description": "Assignment description"}
                    },
                    "required": ["course_id", "assignment_name", "file_path"]
                }
            },
            {
                "name": "upload_module_file",
                "description": "Upload file to course module (teacher only)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "module_id": {"type": "integer", "description": "Module ID"},
                        "file_path": {"type": "string", "description": "Local file path"},
                        "title": {"type": "string", "description": "File title in module"}
                    },
                    "required": ["course_id", "module_id", "file_path"]
                }
            },
            {
                "name": "submit_assignment_file",
                "description": "Submit assignment with file upload (student only)",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "assignment_id": {"type": "integer", "description": "Assignment ID"},
                        "file_path": {"type": "string", "description": "Local file path"},
                        "comment": {"type": "string", "description": "Submission comment"}
                    },
                    "required": ["course_id", "assignment_id", "file_path"]
                }
            }
        ]
        
        # Filter tools by role
        if user_role == "student":
            student_tools = ["list_courses", "list_modules", "generate_learning_plan", 
                           "get_progress_tracker", "get_study_recommendations", 
                           "get_assignment_prioritizer", "submit_assignment_file"]
            tools = [t for t in tools if t["name"] in student_tools]
        elif user_role in ["teacher", "faculty", "instructor"]:
            # Teachers get all tools including video generation and file uploads
            pass
        elif user_role not in ["admin", "teacher", "faculty", "instructor"]:
            # Remove admin, video generation, and teacher file upload tools for other roles
            restricted_tools = ["create_user", "enroll_user", "generate_video_quiz", 
                              "generate_educational_video", "upload_assignment_file", "upload_module_file"]
            tools = [t for t in tools if t["name"] not in restricted_tools]
            
        return tools
    
    def execute_tool(self, function_name: str, arguments: dict) -> Dict[str, Any]:
        """Execute Canvas tool - universal for all inference systems"""
        try:
            if function_name == "list_courses":
                if self.user_role == "admin":
                    courses = self.admin_canvas.list_account_courses()
                else:
                    courses = self.canvas.list_courses()
                return {
                    "total_courses": len(courses),
                    "courses": [{"id": c.get("id"), "name": c.get("name"), "course_code": c.get("course_code")} for c in courses]
                }
                
            elif function_name == "create_course":
                result = self.admin_canvas.create_course(
                    account_id=1,
                    name=arguments["name"],
                    course_code=arguments["course_code"]
                )
                return result
                
            elif function_name == "list_modules":
                modules = self.canvas.list_modules(arguments["course_id"])
                return modules
                
            elif function_name == "create_assignment":
                result = self.canvas.create_assignment(
                    course_id=arguments["course_id"],
                    name=arguments["name"],
                    points=arguments.get("points", 100)
                )
                return result
                
            elif function_name == "create_user":
                result = self.admin_canvas.create_user(
                    account_id=1,
                    name=arguments["name"],
                    email=arguments["email"],
                    login_id=arguments["login_id"]
                )
                return result
                
            elif function_name == "enroll_user":
                result = self.admin_canvas.enroll_user(
                    course_id=arguments["course_id"],
                    user_id=arguments["user_id"],
                    role=arguments["role"]
                )
                return result
            
            # Student-specific enhanced features
            elif function_name in ["generate_learning_plan", "get_progress_tracker", 
                                 "get_study_recommendations", "get_assignment_prioritizer"]:
                student_features = StudentFeatures(self.canvas)
                canvas_user_id = self.user_info.get('canvas_user_id') if self.user_info else None
                
                if function_name == "generate_learning_plan":
                    return student_features.generate_learning_plan(
                        arguments["course_id"], 
                        arguments.get("study_hours_per_week", 10)
                    )
                elif function_name == "get_progress_tracker":
                    return student_features.get_progress_tracker(canvas_user_id)
                elif function_name == "get_study_recommendations":
                    return student_features.get_study_recommendations(canvas_user_id)
                elif function_name == "get_assignment_prioritizer":
                    return student_features.get_assignment_prioritizer(canvas_user_id)
            
            # Video generation features (teacher only)
            elif function_name in ["generate_video_quiz", "generate_educational_video"]:
                if self.user_role not in ["teacher", "faculty", "instructor", "admin"]:
                    return {"error": "Video generation is only available for teachers"}
                
                video_manager = VideoManager()
                
                if function_name == "generate_video_quiz":
                    result = video_manager.generate_video_quiz(
                        topic=arguments["topic"],
                        course_id=arguments["course_id"],
                        duration=arguments.get("duration", 300),
                        difficulty=arguments.get("difficulty", "medium")
                    )
                    
                    # If successful, create Canvas assignment
                    if result["success"] and "canvas_data" in result:
                        canvas_data = result["canvas_data"]
                        try:
                            assignment = self.canvas.create_assignment(
                                course_id=canvas_data["course_id"],
                                name=canvas_data["assignment_name"],
                                points=canvas_data["points_possible"],
                                description=canvas_data["description"]
                            )
                            result["canvas_assignment"] = assignment
                        except Exception as e:
                            result["canvas_error"] = str(e)
                    
                    return result
                
                elif function_name == "generate_educational_video":
                    result = video_manager.generate_educational_video(
                        topic=arguments["topic"],
                        course_id=arguments["course_id"],
                        duration=arguments.get("duration", 300),
                        style=arguments.get("style", "lecture")
                    )
                    
                    # If successful, create Canvas page
                    if result["success"] and "canvas_data" in result:
                        canvas_data = result["canvas_data"]
                        try:
                            page = self.canvas.create_page(
                                course_id=canvas_data["course_id"],
                                title=canvas_data["page_title"],
                                body=canvas_data["page_body"]
                            )
                            result["canvas_page"] = page
                        except Exception as e:
                            result["canvas_error"] = str(e)
                    
                    return result
            
            # File upload features
            elif function_name in ["upload_assignment_file", "upload_module_file", "submit_assignment_file"]:
                from file_manager import get_file_manager
                import os
                
                file_manager = get_file_manager(self.canvas)
                
                # Check if file exists
                file_path = arguments.get("file_path")
                if not file_path or not os.path.exists(file_path):
                    return {"error": "File not found. Please provide a valid file path."}
                
                # Read file data
                try:
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                    filename = os.path.basename(file_path)
                    
                    # Save file locally first
                    file_info = file_manager.save_uploaded_file(file_data, filename)
                    if not file_info["success"]:
                        return file_info
                    
                    # Execute specific file operation
                    if function_name == "upload_assignment_file":
                        if self.user_role not in ["teacher", "faculty", "instructor", "admin"]:
                            return {"error": "Only teachers can upload assignment files"}
                        
                        result = file_manager.create_assignment_with_file(
                            course_id=arguments["course_id"],
                            assignment_name=arguments["assignment_name"],
                            file_info=file_info,
                            points=arguments.get("points", 100),
                            description=arguments.get("description", "")
                        )
                    
                    elif function_name == "upload_module_file":
                        if self.user_role not in ["teacher", "faculty", "instructor", "admin"]:
                            return {"error": "Only teachers can upload module files"}
                        
                        result = file_manager.add_file_to_module(
                            course_id=arguments["course_id"],
                            module_id=arguments["module_id"],
                            file_info=file_info,
                            item_title=arguments.get("title")
                        )
                    
                    elif function_name == "submit_assignment_file":
                        if self.user_role not in ["student"]:
                            return {"error": "Only students can submit assignment files"}
                        
                        result = file_manager.submit_assignment(
                            course_id=arguments["course_id"],
                            assignment_id=arguments["assignment_id"],
                            file_info=file_info,
                            comment=arguments.get("comment", "")
                        )
                    
                    # Cleanup local file after upload
                    file_manager.cleanup_local_file(file_info["file_path"])
                    
                    return result
                    
                except Exception as e:
                    return {"error": f"File upload failed: {str(e)}"}
                
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            return {"error": str(e)}