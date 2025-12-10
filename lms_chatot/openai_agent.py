from canvas_integration import CanvasLMS
import json
import os
import traceback
import time
from openai import OpenAI
from litellm import completion

class OpenAICanvasAgent:
    def __init__(self, canvas_url: str, canvas_token: str, user_id: int = None):
        print(f"OpenAICanvasAgent initialized for user_id: {user_id}")
        self.canvas = CanvasLMS(canvas_url, canvas_token, as_user_id=user_id)
        self.admin_canvas = CanvasLMS(canvas_url, canvas_token)
        self.user_role = None
        self.user_info = None
        self.is_admin_mode = not user_id
        
        # Initialize OpenAI client with fallback
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key) if self.openai_api_key else None
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o")
        self.use_fallback = not self.openai_api_key or self.openai_api_key == "your_openai_api_key_here"
        
    def process_message(self, user_message: str, conversation_history: list, user_role: str = None, user_info: dict = None) -> dict:
        """Process user message with OpenAI function calling"""
        if user_role:
            self.user_role = user_role
        if user_info:
            self.user_info = user_info
        
        tools = self._get_available_tools()
        system_prompt = self._get_system_prompt()
        
        messages = [{"role": "system", "content": system_prompt}] + conversation_history + [{"role": "user", "content": user_message}]
        
        try:
            if self.use_fallback or not self.client:
                return self._process_with_fallback(messages, user_message)
            return self._process_with_openai(messages, tools)
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"OpenAI Error: {error_details}")
            print("Falling back to LiteLLM...")
            return self._process_with_fallback(messages, user_message)
    
    def _get_available_tools(self):
        """Get OpenAI function definitions"""
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "list_courses",
                    "description": "List courses. For admin, shows all account courses. For others, shows enrolled courses.",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_course",
                    "description": "Create a new course in Canvas LMS",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account_id": {"type": "integer", "description": "Account ID (use 1 for default)"},
                            "name": {"type": "string", "description": "Course name"},
                            "course_code": {"type": "string", "description": "Course code"}
                        },
                        "required": ["account_id", "name", "course_code"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_modules",
                    "description": "List all modules in a course",
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
                            "name": {"type": "string", "description": "Module name"}
                        },
                        "required": ["course_id", "name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_assignment",
                    "description": "Create an assignment in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "Course ID"},
                            "name": {"type": "string", "description": "Assignment name"},
                            "points": {"type": "integer", "description": "Points possible (default 100)"},
                            "description": {"type": "string", "description": "Assignment instructions and description"}
                        },
                        "required": ["course_id", "name"]
                    }
                }
            }
        ]
        
        # Add admin-only tools
        if self.user_role == "admin":
            admin_tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "create_user",
                        "description": "Create a new user (admin only)",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "account_id": {"type": "integer", "description": "Account ID (use 1)"},
                                "name": {"type": "string", "description": "Full name"},
                                "email": {"type": "string", "description": "Email address"},
                                "login_id": {"type": "string", "description": "Login username"}
                            },
                            "required": ["account_id", "name", "email", "login_id"]
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
                {
                    "type": "function",
                    "function": {
                        "name": "enroll_user",
                        "description": "Enroll a user in a course with a specific role",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "course_id": {"type": "integer", "description": "Course ID"},
                                "user_id": {"type": "integer", "description": "User ID"},
                                "role": {"type": "string", "description": "TeacherEnrollment or StudentEnrollment", "enum": ["TeacherEnrollment", "StudentEnrollment"]}
                            },
                            "required": ["course_id", "user_id", "role"]
                        }
                    }
                }
            ]
            tools.extend(admin_tools)
        
        # Filter tools for students
        if self.user_role == "student":
            tools = [t for t in tools if t["function"]["name"] in ["list_courses", "list_modules"]]
        
        return tools
    
    def _get_system_prompt(self):
        """Get role-specific system prompt"""
        role_context = ""
        if self.user_role == "admin":
            role_context = "You are an ADMINISTRATOR. You can create users, courses, enroll users, and manage all Canvas operations."
        elif self.user_role == "student":
            role_context = "You are assisting a STUDENT. They can only view courses and modules they're enrolled in."
        elif self.user_role in ["teacher", "faculty", "instructor"]:
            role_context = "You are assisting a TEACHER. They can create courses, modules, assignments, and manage their classes."
        
        return f"""You are a Canvas LMS assistant. Help users create and manage courses, modules, and content.
{role_context}

CRITICAL RULES:
1. NEVER make up or assume ANY data - courses, IDs, names, etc.
2. ALWAYS use real data from Canvas API calls
3. If you need information, fetch it first using available functions
4. When user asks about courses, call list_courses function first
5. NEVER provide example or placeholder data
6. If no data exists, say "No [items] found"

Always use functions to get real data before responding about Canvas content."""
    
    def _process_with_openai(self, messages, tools):
        """Process with OpenAI function calling"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000")),
                timeout=int(os.getenv("OPENAI_TIMEOUT", "60"))
            )
            
            message = response.choices[0].message
            
            # Check if the model wants to call functions
            if message.tool_calls:
                return self._handle_function_calls(message, messages, tools)
            else:
                return {"content": message.content, "tool_used": False}
                
        except Exception as e:
            return {"content": f"OpenAI API error: {str(e)}", "tool_used": False}
    
    def _handle_function_calls(self, message, messages, tools):
        """Handle OpenAI function calls"""
        tool_results = []
        
        # Add the assistant's message with tool calls to conversation
        messages.append({
            "role": "assistant",
            "content": message.content,
            "tool_calls": [{"id": tc.id, "type": tc.type, "function": {"name": tc.function.name, "arguments": tc.function.arguments}} for tc in message.tool_calls]
        })
        
        # Execute each function call
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            try:
                arguments = json.loads(tool_call.function.arguments)
                result = self._execute_tool(function_name, arguments)
                tool_results.append({"function_name": function_name, "result": result})
                
                # Add function result to conversation
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
                
            except Exception as e:
                error_result = {"error": str(e)}
                tool_results.append({"function_name": function_name, "result": error_result})
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(error_result)
                })
        
        # Get final response from OpenAI
        try:
            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.1")),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000"))
            )
            
            return {
                "content": final_response.choices[0].message.content,
                "tool_used": True,
                "tool_results": tool_results
            }
            
        except Exception as e:
            return {
                "content": f"Error generating final response: {str(e)}",
                "tool_used": True,
                "tool_results": tool_results
            }
    
    def _execute_tool(self, function_name: str, arguments: dict):
        """Execute Canvas LMS tool"""
        try:
            print(f"Executing tool: {function_name} with args: {arguments}")
            
            if function_name == "list_courses":
                if self.user_role == "admin" and self.is_admin_mode:
                    courses = self.admin_canvas.list_account_courses()
                else:
                    courses = self.canvas.list_courses()
                return {
                    "total_courses": len(courses),
                    "courses": [{"id": c.get("id"), "name": c.get("name"), "course_code": c.get("course_code"), "workflow_state": c.get("workflow_state")} for c in courses]
                }
                
            elif function_name == "create_course":
                canvas_client = self.admin_canvas if self.admin_canvas else self.canvas
                created = canvas_client.create_course(**arguments)
                
                # Auto-enroll teacher
                if self.user_role == "teacher" and created.get("id") and self.user_info.get("canvas_user_id"):
                    try:
                        canvas_client.enroll_user(created["id"], self.user_info["canvas_user_id"], "TeacherEnrollment")
                    except Exception as e:
                        print(f"Failed to enroll teacher: {e}")
                
                return created
                
            elif function_name == "create_user":
                return self.admin_canvas.create_user(**arguments)
                
            elif function_name == "enroll_user":
                return self.admin_canvas.enroll_user(**arguments)
                
            elif function_name == "list_users":
                users = self.admin_canvas.list_users()
                return {"total_users": len(users), "users": [{"id": u.get("id"), "name": u.get("name"), "login_id": u.get("login_id")} for u in users[:20]]}
                
            elif function_name == "list_modules":
                result = self.canvas.list_modules(arguments["course_id"])
                return result
                
            elif function_name == "create_module":
                return self.canvas.create_module(**arguments)
                
            elif function_name == "create_assignment":
                return self.canvas.create_assignment(**arguments)
                
            else:
                return {"error": f"Unknown function: {function_name}"}
                
        except Exception as e:
            error_msg = f"{str(e)} - {traceback.format_exc()}"
            print(f"Tool execution error: {error_msg}")
            return {"error": str(e)}
    
    def _process_with_fallback(self, messages, user_message):
        """Fallback to LiteLLM when OpenAI is unavailable"""
        try:
            # Simple tool detection for fallback
            if self._needs_tool(user_message):
                tool_name, args = self._detect_tool_simple(user_message)
                if tool_name:
                    result = self._execute_tool(tool_name, args)
                    response_text = self._format_tool_response(tool_name, result)
                    return {"content": response_text, "tool_used": True, "tool_results": [{"function_name": tool_name, "result": result}]}
            
            # Use LiteLLM for general responses
            response = completion(
                model="gemini/gemini-1.5-flash",
                messages=messages,
                temperature=0.1,
                max_tokens=500
            )
            
            return {"content": response.choices[0].message.content, "tool_used": False}
            
        except Exception as e:
            return {"content": f"I'm having trouble connecting to AI services. Please try again later. Error: {str(e)}", "tool_used": False}
    
    def _needs_tool(self, message):
        """Simple tool detection"""
        keywords = ['list', 'show', 'create', 'add', 'course', 'module', 'assignment', 'user']
        return any(word in message.lower() for word in keywords)
    
    def _detect_tool_simple(self, message):
        """Simple pattern-based tool detection"""
        msg = message.lower()
        
        if 'list' in msg and 'course' in msg:
            return 'list_courses', {}
        elif 'create' in msg and 'course' in msg:
            # Extract course name
            import re
            name_match = re.search(r'course[\s\"\']+(.*?)[\"\'\.]', message, re.IGNORECASE)
            name = name_match.group(1).strip() if name_match else "New Course"
            return 'create_course', {'account_id': 1, 'name': name, 'course_code': name.replace(' ', '').upper()[:10]}
        elif 'list' in msg and 'module' in msg:
            return 'list_modules', {'course_id': 1}  # Default course
        elif 'create' in msg and 'module' in msg:
            import re
            name_match = re.search(r'module[\s\"\']+(.*?)[\"\'\.]', message, re.IGNORECASE)
            name = name_match.group(1).strip() if name_match else "New Module"
            return 'create_module', {'course_id': 1, 'name': name}
        
        return None, {}
    
    def _format_tool_response(self, tool_name, result):
        """Format tool results for user"""
        if tool_name == 'list_courses':
            if result.get('courses'):
                courses_list = "\n".join([f"• {c['name']} ({c['course_code']}) - {c['workflow_state']}" for c in result['courses']])
                return f"Found {result['total_courses']} courses:\n{courses_list}"
            return "No courses found."
        elif tool_name == 'create_course':
            return f"✅ Created course: {result.get('name', 'Unknown')} (ID: {result.get('id', 'Unknown')})"
        elif tool_name == 'list_modules':
            if isinstance(result, list) and result:
                modules_list = "\n".join([f"• {m.get('name', 'Unnamed')}" for m in result])
                return f"Found {len(result)} modules:\n{modules_list}"
            return "No modules found."
        elif tool_name == 'create_module':
            return f"✅ Created module: {result.get('name', 'Unknown')}"
        
        return f"Operation completed: {str(result)}"