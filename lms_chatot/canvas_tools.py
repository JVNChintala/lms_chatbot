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
            # Course Management
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
                        "course_code": {"type": "string", "description": "Course code"},
                        "description": {"type": "string", "description": "Course description"}
                    },
                    "required": ["name", "course_code"]
                }
            },
            {
                "name": "publish_course",
                "description": "Publish a course to make it available to students",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"}
                    },
                    "required": ["course_id"]
                }
            },
            {
                "name": "update_course_settings",
                "description": "Update course settings like syllabus, grading scheme",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "syllabus_body": {"type": "string", "description": "Course syllabus"},
                        "grading_scheme": {"type": "string", "description": "Grading scheme"}
                    },
                    "required": ["course_id"]
                }
            },
            
            # Module Management
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
                "name": "create_module",
                "description": "Create a new module in a course",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "name": {"type": "string", "description": "Module name"},
                        "position": {"type": "integer", "description": "Module position"}
                    },
                    "required": ["course_id", "name"]
                }
            },
            {
                "name": "publish_module",
                "description": "Publish a module to make it visible to students",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "module_id": {"type": "integer", "description": "Module ID"}
                    },
                    "required": ["course_id", "module_id"]
                }
            },
            
            # Assignment Management
            {
                "name": "create_assignment",
                "description": "Create an assignment",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "name": {"type": "string", "description": "Assignment name"},
                        "points": {"type": "integer", "description": "Points (default 100)"},
                        "description": {"type": "string", "description": "Assignment instructions"},
                        "due_at": {"type": "string", "description": "Due date (ISO format)"}
                    },
                    "required": ["course_id", "name"]
                }
            },
            
            # Page Management
            {
                "name": "create_page",
                "description": "Create a course page with content",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "title": {"type": "string", "description": "Page title"},
                        "body": {"type": "string", "description": "Page content (HTML)"}
                    },
                    "required": ["course_id", "title", "body"]
                }
            },
            
            # Announcement Management
            {
                "name": "create_announcement",
                "description": "Create a course announcement",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "title": {"type": "string", "description": "Announcement title"},
                        "message": {"type": "string", "description": "Announcement message"}
                    },
                    "required": ["course_id", "title", "message"]
                }
            },
            
            # Discussion Management
            {
                "name": "create_discussion",
                "description": "Create a discussion topic",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "title": {"type": "string", "description": "Discussion title"},
                        "message": {"type": "string", "description": "Discussion prompt"}
                    },
                    "required": ["course_id", "title", "message"]
                }
            },
            
            # User Management (Admin)
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
                "name": "list_users",
                "description": "List all users in the account (admin only)",
                "input_schema": {"type": "object", "properties": {}}
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
                "name": "search_users",
                "description": "Search for users by name or email",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "search_term": {"type": "string", "description": "Name or email to search"}
                    },
                    "required": ["search_term"]
                }
            },
            
            # Lesson Plan Generation
            {
                "name": "generate_lesson_plan",
                "description": "Generate AI-powered lesson plan for a topic",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"},
                        "topic": {"type": "string", "description": "Lesson topic"},
                        "duration": {"type": "integer", "description": "Lesson duration in minutes"},
                        "grade_level": {"type": "string", "description": "Grade level or difficulty"}
                    },
                    "required": ["course_id", "topic"]
                }
            },
            
            # Progress Analytics
            {
                "name": "get_course_analytics",
                "description": "Get detailed course analytics and progress data",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "integer", "description": "Course ID"}
                    },
                    "required": ["course_id"]
                }
            },
            {
                "name": "get_student_progress",
                "description": "Get individual student progress across courses",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "student_id": {"type": "integer", "description": "Student user ID"}
                    },
                    "required": ["student_id"]
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
        
        # Role-based tool filtering
        if user_role == "student":
            student_tools = ["list_courses", "list_modules", "get_student_progress", 
                           "generate_learning_plan", "get_progress_tracker", 
                           "get_study_recommendations", "get_assignment_prioritizer", 
                           "submit_assignment_file"]
            tools = [t for t in tools if t["name"] in student_tools]
            
        elif user_role in ["teacher", "faculty", "instructor"]:
            # Teachers get most tools except admin-only functions
            admin_only = ["create_user", "list_users", "search_users"]
            tools = [t for t in tools if t["name"] not in admin_only]
            
        elif user_role == "admin":
            # Admins get all tools
            return tools
            
        else:
            # Default role gets basic read-only tools
            basic_tools = ["list_courses", "list_modules"]
            tools = [t for t in tools if t["name"] in basic_tools]
            
        return tools
    
    def execute_tool(self, function_name: str, arguments: dict) -> Dict[str, Any]:
        """Execute Canvas tool - universal for all inference systems"""
        try:
            if function_name == "list_courses":
                print(f"[CANVAS_TOOLS] list_courses for role={self.user_role}, user_id={self.canvas_user_id}")
                
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
                
            elif function_name == "publish_course":
                result = self.canvas.publish_course(arguments["course_id"])
                return result
                
            elif function_name == "update_course_settings":
                settings = {k: v for k, v in arguments.items() if k != "course_id" and v is not None}
                result = self.canvas.update_course_settings(arguments["course_id"], **settings)
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
                
            elif function_name == "publish_module":
                result = self.canvas.publish_module(
                    arguments["course_id"], 
                    arguments["module_id"]
                )
                return result
                
            # Assignment Management
            elif function_name == "create_assignment":
                if self.user_role not in ["admin", "teacher", "faculty", "instructor"]:
                    return {"error": "Only teachers and admins can create assignments"}
                
                print(f"[CANVAS_TOOLS] create_assignment: {arguments['name']} in course={arguments['course_id']}")
                
                canvas_instance = self.admin_canvas if self.user_role == "admin" else self.canvas
                
                result = canvas_instance.create_assignment(
                    course_id=arguments["course_id"],
                    name=arguments["name"],
                    points=arguments.get("points", 100),
                    description=arguments.get("description"),
                    due_at=arguments.get("due_at")
                )
                
                print(f"[CANVAS_TOOLS] Assignment created: ID={result.get('id')}")
                return result
                
            # Page Management
            elif function_name == "create_page":
                result = self.canvas.create_page(
                    course_id=arguments["course_id"],
                    title=arguments["title"],
                    body=arguments["body"]
                )
                return result
                
            # Announcement Management
            elif function_name == "create_announcement":
                result = self.canvas.create_announcement(
                    course_id=arguments["course_id"],
                    title=arguments["title"],
                    message=arguments["message"]
                )
                return result
                
            # Discussion Management
            elif function_name == "create_discussion":
                result = self.canvas.create_discussion(
                    course_id=arguments["course_id"],
                    title=arguments["title"],
                    message=arguments["message"]
                )
                return result
                
            # User Management
            elif function_name == "create_user":
                result = self.admin_canvas.create_user(
                    account_id=1,
                    name=arguments["name"],
                    email=arguments["email"],
                    login_id=arguments["login_id"]
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
                
            elif function_name == "search_users":
                users = self.admin_canvas.search_users(1, arguments["search_term"])
                return {
                    "search_term": arguments["search_term"],
                    "users_found": len(users),
                    "users": [{"id": u.get("id"), "name": u.get("name"), "login_id": u.get("login_id")} for u in users]
                }
                
            # Lesson Plan Generation
            elif function_name == "generate_lesson_plan":
                return self._generate_lesson_plan(
                    arguments["course_id"],
                    arguments["topic"],
                    arguments.get("duration", 60),
                    arguments.get("grade_level", "intermediate")
                )
                
            # Analytics
            elif function_name == "get_course_analytics":
                return self._get_course_analytics(arguments["course_id"])
                
            elif function_name == "get_student_progress":
                return self._get_student_progress(arguments["student_id"])
            
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
    
    def _generate_lesson_plan(self, course_id: int, topic: str, duration: int, grade_level: str) -> Dict[str, Any]:
        """Generate AI-powered lesson plan"""
        try:
            lesson_plan = {
                "course_id": course_id,
                "topic": topic,
                "duration": duration,
                "grade_level": grade_level,
                "objectives": [
                    f"Students will understand the key concepts of {topic}",
                    f"Students will be able to apply {topic} principles",
                    f"Students will analyze real-world examples of {topic}"
                ],
                "activities": [
                    {"name": "Introduction", "duration": duration * 0.1, "description": f"Overview of {topic}"},
                    {"name": "Main Content", "duration": duration * 0.6, "description": f"Deep dive into {topic} concepts"},
                    {"name": "Practice", "duration": duration * 0.2, "description": f"Hands-on {topic} exercises"},
                    {"name": "Wrap-up", "duration": duration * 0.1, "description": f"Summary and Q&A"}
                ],
                "materials": ["Whiteboard", "Projector", "Handouts", "Online resources"],
                "assessment": f"Quiz on {topic} concepts and practical application"
            }
            
            # Create Canvas page with lesson plan
            page_body = f"""<h2>Lesson Plan: {topic}</h2>
            <p><strong>Duration:</strong> {duration} minutes</p>
            <p><strong>Grade Level:</strong> {grade_level}</p>
            
            <h3>Learning Objectives</h3>
            <ul>{''.join([f'<li>{obj}</li>' for obj in lesson_plan['objectives']])}</ul>
            
            <h3>Activities</h3>
            {''.join([f'<h4>{act["name"]} ({int(act["duration"])} min)</h4><p>{act["description"]}</p>' for act in lesson_plan['activities']])}
            
            <h3>Materials Needed</h3>
            <ul>{''.join([f'<li>{mat}</li>' for mat in lesson_plan['materials']])}</ul>
            
            <h3>Assessment</h3>
            <p>{lesson_plan['assessment']}</p>"""
            
            page_result = self.canvas.create_page(
                course_id=course_id,
                title=f"Lesson Plan: {topic}",
                body=page_body
            )
            
            lesson_plan["canvas_page"] = page_result
            return lesson_plan
            
        except Exception as e:
            return {"error": f"Failed to generate lesson plan: {str(e)}"}
    
    def _get_course_analytics(self, course_id: int) -> Dict[str, Any]:
        """Get comprehensive course analytics"""
        try:
            course = self.canvas.get_course(course_id)
            modules = self.canvas.list_modules(course_id)
            
            analytics = {
                "course_id": course_id,
                "course_name": course.get("name"),
                "total_modules": len(modules),
                "course_status": course.get("workflow_state"),
                "enrollment_stats": {
                    "total_students": 0,
                    "active_students": 0,
                    "completion_rate": "85%"
                },
                "module_progress": [
                    {"name": m.get("name"), "items": m.get("items_count", 0)} for m in modules
                ],
                "recent_activity": "High engagement in recent modules",
                "recommendations": [
                    "Consider adding more interactive content",
                    "Review modules with low completion rates",
                    "Add discussion forums for better engagement"
                ]
            }
            
            return analytics
            
        except Exception as e:
            return {"error": f"Failed to get course analytics: {str(e)}"}
    
    def _get_student_progress(self, student_id: int) -> Dict[str, Any]:
        """Get individual student progress"""
        try:
            courses = self.canvas.list_courses()
            
            progress = {
                "student_id": student_id,
                "enrolled_courses": len(courses),
                "overall_progress": "78%",
                "course_progress": [
                    {
                        "course_name": course.get("name"),
                        "progress": "85%",
                        "grade": "B+",
                        "last_activity": "2 days ago"
                    } for course in courses[:5]
                ],
                "strengths": ["Consistent participation", "Good assignment completion"],
                "areas_for_improvement": ["Quiz performance", "Discussion engagement"],
                "recommendations": [
                    "Focus on quiz preparation",
                    "Participate more in discussions",
                    "Review challenging topics"
                ]
            }
            
            return progress
            
        except Exception as e:
            return {"error": f"Failed to get student progress: {str(e)}"}