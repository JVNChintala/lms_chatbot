from canvas_integration import CanvasLMS
from inference_systems.inference_manager import InferenceManager
from analytics_cache import analytics_cache
from student_features import StudentFeatures

class CanvasAgent:
    def __init__(self, canvas_url: str, canvas_token: str, user_id: int = None):
        self.canvas = CanvasLMS(canvas_url, canvas_token, as_user_id=user_id)
        self.admin_canvas = CanvasLMS(canvas_url, canvas_token)
        self.user_role = None
        self.user_info = None
        
        # Initialize plug-and-play inference manager
        self.inference_manager = InferenceManager()
        
    def process_message(self, user_message: str, conversation_history: list, user_role: str = None, user_info: dict = None) -> dict:
        if user_role:
            self.user_role = user_role
        if user_info:
            self.user_info = user_info
            
        # Define Canvas tools (same for all inference systems)
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
                "name": "get_learning_analytics",
                "description": "Personal learning analytics and insights",
                "input_schema": {"type": "object", "properties": {}}
            },
            {
                "name": "get_study_buddy_suggestions",
                "description": "Find compatible study partners and groups",
                "input_schema": {"type": "object", "properties": {}}
            }
        ]
        
        # Filter tools by role
        if self.user_role == "student":
            # Students get Canvas tools + enhanced student features
            student_tools = ["list_courses", "list_modules", "generate_learning_plan", 
                           "get_progress_tracker", "get_study_recommendations", 
                           "get_assignment_prioritizer", "get_learning_analytics", 
                           "get_study_buddy_suggestions"]
            tools = [t for t in tools if t["name"] in student_tools]
        elif self.user_role not in ["admin", "teacher", "faculty", "instructor"]:
            tools = [t for t in tools if t["name"] not in ["create_user", "enroll_user"]]
            
        system_prompt = f"""You are a Canvas LMS assistant. User role: {self.user_role or 'unknown'}.

Rules:
1. Always use tools to get real Canvas data
2. Never make up course IDs or data
3. Be helpful and conversational
4. If user asks about courses, call list_courses first

For students, you have access to enhanced features:
- Learning Plan Generator
- Progress Tracker
- Study Recommendations
- Assignment Prioritizer
- Learning Analytics
- Study Buddy Suggestions"""
        
        messages = [{"role": "user", "content": user_message}]
        
        try:
            # Call inference manager (automatically selects best available system)
            result = self.inference_manager.call_with_tools(system_prompt, messages, tools)
            
            # Handle tool execution
            if result.get("needs_tool"):
                tool_result = self._execute_tool(result["tool_name"], result["tool_args"])
                
                # Get final response from inference system
                if hasattr(self.inference_manager.active_system, 'get_final_response'):
                    final_content = self.inference_manager.get_final_response(
                        messages, tool_result, result.get("tool_call_id") or result.get("tool_use_id") or result.get("response_text")
                    )
                else:
                    final_content = f"Executed {result['tool_name']}: {tool_result}"
                
                # Generate dynamic analytics for chat
                chat_analytics = self._generate_chat_analytics()
                
                return {
                    "content": final_content,
                    "tool_used": True,
                    "tool_results": [{"function_name": result["tool_name"], "result": tool_result}],
                    "inference_system": result.get("inference_system"),
                    "analytics": chat_analytics
                }
            
            # Generate dynamic analytics for chat
            chat_analytics = self._generate_chat_analytics()
            
            return {
                "content": result["content"],
                "tool_used": False,
                "inference_system": result.get("inference_system"),
                "analytics": chat_analytics
            }
            
        except Exception as e:
            return {"content": f"Error: {str(e)}", "tool_used": False}
    
    def _execute_tool(self, function_name: str, arguments: dict):
        """Execute Canvas tool (same for all inference systems)"""
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
                                 "get_study_recommendations", "get_assignment_prioritizer",
                                 "get_learning_analytics", "get_study_buddy_suggestions"]:
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
                elif function_name == "get_learning_analytics":
                    return student_features.get_learning_analytics(canvas_user_id)
                elif function_name == "get_study_buddy_suggestions":
                    return student_features.get_study_buddy_suggestions(canvas_user_id)
                
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            return {"error": str(e)}
    
    def _generate_chat_analytics(self):
        """Generate lightweight analytics for chat interface"""
        try:
            # Check cache first
            cached = analytics_cache.get_cached_analytics(self.user_role, self.user_info.get('canvas_user_id') if self.user_info else None)
            if cached:
                return cached
            
            # Generate fresh analytics with student features
            canvas_client = self.canvas if self.user_role != "admin" else self.admin_canvas
            analytics = analytics_cache.get_quick_analytics(canvas_client, self.user_role)
            
            # Add student-specific quick actions
            if self.user_role == "student":
                analytics["quick_actions"].extend([
                    {"action": "learning_plan", "label": "📋 Learning Plan", "prompt": "Generate my learning plan"},
                    {"action": "progress_tracker", "label": "📊 Progress Tracker", "prompt": "Show my progress"},
                    {"action": "study_recommendations", "label": "💡 Study Tips", "prompt": "Get study recommendations"},
                    {"action": "assignment_prioritizer", "label": "⏰ Prioritize Tasks", "prompt": "Help me prioritize assignments"}
                ])
            
            # Cache the result
            analytics_cache.cache_analytics(self.user_role, analytics, self.user_info.get('canvas_user_id') if self.user_info else None)
            
            return analytics
        except Exception as e:
            return {"error": str(e), "quick_actions": []}
    
    def get_inference_status(self):
        """Get status of inference systems"""
        return self.inference_manager.get_status()