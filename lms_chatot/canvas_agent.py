from canvas_integration import CanvasLMS
import json
import os
import traceback
import time
from qwen_config import QwenConfig, performance_monitor

class CanvasAgent:
    def __init__(self, canvas_url: str, canvas_token: str, user_id: int = None):
        # Use admin token with as_user_id parameter for user-specific operations
        print(f"CanvasAgent initialized for user_id: {user_id}")
        self.canvas = CanvasLMS(canvas_url, canvas_token, as_user_id=user_id)
        self.admin_canvas = CanvasLMS(canvas_url, canvas_token)  # Admin operations without as_user_id
        self.conversation_state = {}
        self.user_role = None
        self.user_info = None
        self.is_admin_mode = not user_id
        
    def process_message(self, user_message: str, conversation_history: list, user_role: str = None, user_info: dict = None) -> dict:
        """Process user message and determine action"""
        if user_role:
            self.user_role = user_role
        if user_info:
            self.user_info = user_info
        
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
                    "name": "create_user",
                    "description": "Create a new user (admin only). Returns user_id needed for enrollment.",
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
            },
            {
                "type": "function",
                "function": {
                    "name": "create_page",
                    "description": "Create a content page in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "Course ID"},
                            "title": {"type": "string", "description": "Page title"},
                            "body": {"type": "string", "description": "Page content (HTML)"}
                        },
                        "required": ["course_id", "title", "body"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "publish_course",
                    "description": "Publish a course to make it available to students",
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
                    "name": "create_discussion",
                    "description": "Create a discussion forum in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "Course ID"},
                            "title": {"type": "string", "description": "Discussion title"},
                            "message": {"type": "string", "description": "Discussion prompt"}
                        },
                        "required": ["course_id", "title", "message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_announcement",
                    "description": "Create an announcement in a course",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "Course ID"},
                            "title": {"type": "string", "description": "Announcement title"},
                            "message": {"type": "string", "description": "Announcement message"}
                        },
                        "required": ["course_id", "title", "message"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "update_syllabus",
                    "description": "Add or update course syllabus",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "Course ID"},
                            "syllabus_body": {"type": "string", "description": "Syllabus content (HTML)"}
                        },
                        "required": ["course_id", "syllabus_body"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "publish_module",
                    "description": "Publish a module to make it visible to students",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "course_id": {"type": "integer", "description": "Course ID"},
                            "module_id": {"type": "integer", "description": "Module ID"}
                        },
                        "required": ["course_id", "module_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_users",
                    "description": "Search for existing users by name or email before creating",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "account_id": {"type": "integer", "description": "Account ID (use 1)"},
                            "search_term": {"type": "string", "description": "Name or email to search"}
                        },
                        "required": ["account_id", "search_term"]
                    }
                }
            }
        ]
        
        if self.user_role == "student":
            tools = [t for t in tools if t["function"]["name"] in ["list_courses", "list_modules"]]
        elif self.user_role not in ["admin", "teacher", "faculty", "instructor"]:
            tools = [t for t in tools if t["function"]["name"] not in ["create_user", "list_users", "enroll_user"]]
        
        role_context = ""
        if self.user_role == "admin":
            role_context = "The user is an ADMINISTRATOR. They can create users (teachers/students), create courses, enroll users in courses, and manage all aspects of Canvas."
        elif self.user_role == "student":
            role_context = "The user is a STUDENT. They can only view courses they are enrolled in. Do NOT offer to create courses or modules."
        elif self.user_role in ["teacher", "faculty", "instructor"]:
            role_context = "The user is a TEACHER/FACULTY. They can create courses, modules, assignments, and upload content (PDFs, documents, images)."
        else:
            role_context = "Ask the user if they are a student, teacher, or admin to provide appropriate assistance."
        
        # Use optimized Qwen2.5 system prompt
        system_prompt = QwenConfig.get_system_prompt(self.user_role) + f"\n\n{role_context}\n\nCRITICAL RULES - NEVER VIOLATE:\n1. NEVER make up, invent, or assume ANY data - courses, IDs, names, etc.\n2. ALWAYS use real data from Canvas API calls\n3. If you need information, ALWAYS fetch it first using tools\n4. When user asks about courses, IMMEDIATELY call list_courses tool\n5. NEVER provide example or placeholder data\n6. If no data exists, say \"No [items] found\" - don't make up examples\n\nWORKFLOW:\n1. User asks about existing items → Call appropriate list tool first\n2. User wants to create something → Gather details, then create\n3. Always use REAL data from tool results in responses\n4. Be conversational but factual\n\nYou must ALWAYS call tools to get real data before responding about Canvas content."
        
        messages = [{"role": "system", "content": system_prompt}] + conversation_history + [{"role": "user", "content": user_message}]
        
        try:
            return self._process_with_ollama(messages, tools)
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Agent Error: {error_details}")
            return {"content": f"I encountered an error: {str(e)}. Please check the server logs for details.", "tool_used": False}
    

    
    def _process_with_ollama(self, messages, tools):
        """Process with Ollama server with intelligent tool detection"""
        import requests
        import re
        
        ollama_url = os.getenv('OLLAMA_URL', 'http://10.21.34.238:11434')
        ollama_model = os.getenv('OLLAMA_MODEL', 'llama3.1')
        
        user_msg = messages[-1]['content']
        system_msg = messages[0]['content'] if messages[0]['role'] == 'system' else ''
        
        # Use intelligent tool detection with smaller LLM
        tool_decision = self._detect_tool_with_llm(user_msg, ollama_url, ollama_model)
        
        if tool_decision['needs_tool']:
            print(f"[DEBUG] LLM detected tool needed: {tool_decision['tool_name']}")
            return self._execute_ollama_tool(tool_decision['tool_name'], user_msg, system_msg, ollama_url, ollama_model, messages)
        
        print(f"[DEBUG] LLM determined no tool needed, using general response")
        
        # For general conversation, use Ollama
        return self._get_ollama_response(user_msg, system_msg, ollama_url, ollama_model, messages)
    
    def _detect_tool_with_llm(self, user_msg, ollama_url, ollama_model):
        """Use LLM to intelligently detect if a tool is needed with Qwen2.5 optimization"""
        import requests
        
        # Use optimized Qwen2.5 tool detection prompt
        detection_prompt = QwenConfig.get_tool_detection_prompt(user_msg)
        
        start_time = time.time()
        try:
            # Use optimized parameters for tool detection
            optimized_params = QwenConfig.get_optimized_params("tool_detection")
            
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": detection_prompt,
                    "stream": False,
                    "options": optimized_params
                },
                timeout=int(os.getenv("OLLAMA_TIMEOUT", "120"))
            )
            
            if response.status_code == 200:
                result = response.json()
                llm_response = result.get('response', '').strip()
                
                # Log performance
                response_time = (time.time() - start_time) * 1000
                performance_monitor.log_response_time("tool_detection", response_time)
                
                if llm_response.startswith('TOOL:'):
                    tool_name = llm_response.split(':', 1)[1].strip()
                    performance_monitor.log_tool_usage("tool_detection", True)
                    return {'needs_tool': True, 'tool_name': tool_name}
                else:
                    performance_monitor.log_tool_usage("tool_detection", True)
                    return {'needs_tool': False, 'tool_name': None}
            else:
                performance_monitor.log_tool_usage("tool_detection", False)
                return self._fallback_tool_detection(user_msg)
                
        except Exception as e:
            print(f"[DEBUG] LLM tool detection failed: {e}, using fallback")
            performance_monitor.log_tool_usage("tool_detection", False)
            return self._fallback_tool_detection(user_msg)
    
    def _fallback_tool_detection(self, user_msg):
        """Fallback pattern matching if LLM detection fails"""
        user_lower = user_msg.lower()
        
        if any(word in user_lower for word in ['list', 'show', 'view', 'my']) and 'course' in user_lower:
            return {'needs_tool': True, 'tool_name': 'list_courses'}
        elif 'create' in user_lower and 'course' in user_lower:
            return {'needs_tool': True, 'tool_name': 'create_course'}
        elif any(word in user_lower for word in ['list', 'show']) and 'module' in user_lower:
            return {'needs_tool': True, 'tool_name': 'list_modules'}
        elif 'create' in user_lower and 'module' in user_lower:
            return {'needs_tool': True, 'tool_name': 'create_module'}
        elif 'create' in user_lower and 'assignment' in user_lower:
            return {'needs_tool': True, 'tool_name': 'create_assignment'}
        elif 'create' in user_lower and 'user' in user_lower:
            return {'needs_tool': True, 'tool_name': 'create_user'}
        elif any(word in user_lower for word in ['list', 'show']) and 'user' in user_lower:
            return {'needs_tool': True, 'tool_name': 'list_users'}
        else:
            return {'needs_tool': False, 'tool_name': None}
    
    def _execute_ollama_tool(self, tool_name, user_msg, system_msg, ollama_url, ollama_model, messages=None):
        """Execute Canvas tool and format response with Ollama"""
        import requests
        import re
        
        try:
            # Execute the Canvas tool
            if tool_name == 'list_courses':
                result = self._execute_tool('list_courses', {})
                
            elif tool_name == 'create_course':
                # Extract course details from user message
                name_match = re.search(r'(?:course|named?)\s+["\']?([^"\'\.\n]+)["\']?', user_msg, re.IGNORECASE)
                code_match = re.search(r'(?:code|id)\s+["\']?([A-Z0-9-]+)["\']?', user_msg, re.IGNORECASE)
                
                name = name_match.group(1).strip() if name_match else "New Course"
                code = code_match.group(1).strip() if code_match else name.replace(' ', '').upper()[:10]
                
                result = self._execute_tool('create_course', {'account_id': 1, 'name': name, 'course_code': code})
                
            elif tool_name == 'list_modules':
                # Extract course ID from message or use first available course
                course_id_match = re.search(r'course\s+(\d+)', user_msg, re.IGNORECASE)
                if course_id_match:
                    course_id = int(course_id_match.group(1))
                else:
                    courses = self._execute_tool('list_courses', {})
                    course_id = courses['courses'][0]['id'] if courses['courses'] else 1
                
                result = self._execute_tool('list_modules', {'course_id': course_id})
                
            elif tool_name == 'create_module':
                name_match = re.search(r'(?:module|named?)\s+["\']?([^"\'\.\n]+)["\']?', user_msg, re.IGNORECASE)
                course_id_match = re.search(r'course\s+(\d+)', user_msg, re.IGNORECASE)
                
                name = name_match.group(1).strip() if name_match else "New Module"
                if course_id_match:
                    course_id = int(course_id_match.group(1))
                else:
                    courses = self._execute_tool('list_courses', {})
                    course_id = courses['courses'][0]['id'] if courses['courses'] else 1
                
                result = self._execute_tool('create_module', {'course_id': course_id, 'name': name})
                
            elif tool_name == 'create_assignment':
                name_match = re.search(r'(?:assignment|named?)\s+["\']?([^"\'\.\n]+)["\']?', user_msg, re.IGNORECASE)
                points_match = re.search(r'(\d+)\s+points?', user_msg, re.IGNORECASE)
                course_id_match = re.search(r'course\s+(\d+)', user_msg, re.IGNORECASE)
                
                name = name_match.group(1).strip() if name_match else "New Assignment"
                points = int(points_match.group(1)) if points_match else 100
                if course_id_match:
                    course_id = int(course_id_match.group(1))
                else:
                    courses = self._execute_tool('list_courses', {})
                    course_id = courses['courses'][0]['id'] if courses['courses'] else 1
                
                result = self._execute_tool('create_assignment', {'course_id': course_id, 'name': name, 'points': points})
                
            else:
                result = self._execute_tool(tool_name, {})
            
            # Format response with Ollama
            tool_result_text = self._format_tool_result(tool_name, result)
            
            # Build conversation context
            if messages:
                conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages[-3:]])
            else:
                conversation_context = f"user: {user_msg}"
            
            # Get Ollama to provide a natural response based on REAL data
            prompt = f"{system_msg}\n\nConversation context:\n{conversation_context}\n\nCanvas operation completed: {tool_result_text}\n\nProvide a helpful, conversational response using ONLY the real Canvas data above. Be natural but factual:\n\nAssistant:"
            
            ollama_response = self._get_ollama_text(prompt, ollama_url, ollama_model, "tool_execution")
            
            return {
                "content": ollama_response,
                "tool_used": True,
                "tool_results": [{"function_name": tool_name, "result": result}]
            }
            
        except Exception as e:
            return {"content": f"Error executing {tool_name}: {str(e)}", "tool_used": False}
    
    def _format_tool_result(self, tool_name, result):
        """Format tool results for Ollama context"""
        if tool_name == 'list_courses':
            if result.get('courses'):
                courses_list = "\n".join([f"- {c['name']} ({c['course_code']}) - {c['workflow_state']}" for c in result['courses']])
                return f"Found {result['total_courses']} courses:\n{courses_list}"
            return "No courses found"
        
        elif tool_name == 'create_course':
            return f"Created course: {result.get('name', 'Unknown')} (ID: {result.get('id', 'Unknown')})"
        
        elif tool_name == 'list_modules':
            if isinstance(result, list) and result:
                modules_list = "\n".join([f"- {m.get('name', 'Unnamed')}" for m in result])
                return f"Found {len(result)} modules:\n{modules_list}"
            return "No modules found"
        
        return str(result)
    
    def _get_ollama_response(self, user_msg, system_msg, ollama_url, ollama_model, messages=None):
        """Get general response from Ollama with conversation awareness"""
        # Build conversation context from messages
        if messages:
            conversation_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages[-4:]])
        else:
            conversation_context = f"user: {user_msg}"
        
        # For general queries, suggest using tools to get real data
        if any(word in user_msg.lower() for word in ['course', 'module', 'assignment', 'user', 'student', 'details', 'information']):
            prompt = f"{system_msg}\n\nConversation so far:\n{conversation_context}\n\nThe user is asking about Canvas content but no specific tool was triggered. You MUST NOT make up any data. Instead, ask the user to be more specific about what they want to see. Suggest specific commands like 'list all courses' or 'show my courses'.\n\nAssistant:"
        else:
            prompt = f"{system_msg}\n\nConversation so far:\n{conversation_context}\n\nRespond helpfully and naturally:\n\nAssistant:"
        
        response_text = self._get_ollama_text(prompt, ollama_url, ollama_model)
        return {"content": response_text, "tool_used": False}
    
    def _get_ollama_text(self, prompt, ollama_url, ollama_model, operation_type="general"):
        """Get text response from Ollama server with Qwen2.5 optimization"""
        import requests
        
        start_time = time.time()
        try:
            # Use optimized parameters based on operation type
            optimized_params = QwenConfig.get_optimized_params(operation_type)
            
            response = requests.post(
                f"{ollama_url}/api/generate",
                json={
                    "model": ollama_model,
                    "prompt": prompt,
                    "stream": False,
                    "options": optimized_params
                },
                timeout=int(os.getenv("OLLAMA_TIMEOUT", "120"))
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', 'No response from Ollama')
                
                # Log performance
                response_time = (time.time() - start_time) * 1000
                performance_monitor.log_response_time(f"ollama_{operation_type}", response_time)
                
                # Clean up response
                response_text = response_text.strip()
                if response_text.startswith('Assistant:'):
                    response_text = response_text[10:].strip()
                
                performance_monitor.log_tool_usage(f"ollama_{operation_type}", True)
                return response_text
            else:
                performance_monitor.log_tool_usage(f"ollama_{operation_type}", False)
                return f"Ollama server error: {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            performance_monitor.log_tool_usage(f"ollama_{operation_type}", False)
            return f"Cannot connect to Ollama server. Error: {str(e)}"
    
    def _execute_tool(self, function_name: str, arguments: dict):
        """Execute Canvas LMS tool"""
        try:
            print(f"Executing tool: {function_name} with args: {arguments}")
            if function_name == "list_courses":
                if self.user_role == "admin" and self.is_admin_mode:
                    courses = self.admin_canvas.list_account_courses()
                else:
                    # Use user-specific Canvas instance to get only their enrolled courses
                    courses = self.canvas.list_courses()
                    print(f"[DEBUG] Raw courses response: {courses}")
                    print(f"[DEBUG] User ID: {self.canvas.as_user_id}")
                    print(f"[DEBUG] User role: {self.user_role}")
                result = {
                    "total_courses": len(courses),
                    "courses": [{"id": c.get("id"), "name": c.get("name"), "course_code": c.get("course_code"), "workflow_state": c.get("workflow_state")} for c in courses]
                }
            elif function_name == "create_course":
                # Use admin token for course creation, then enroll the teacher
                canvas_client = self.admin_canvas if self.admin_canvas else self.canvas
                created = canvas_client.create_course(**arguments)
                
                # Auto-enroll the teacher in the created course
                if self.user_role == "teacher" and created.get("id") and self.user_info.get("canvas_user_id"):
                    try:
                        canvas_client.enroll_user(created["id"], self.user_info["canvas_user_id"], "TeacherEnrollment")
                        print(f"Auto-enrolled teacher {self.user_info['canvas_user_id']} in course {created['id']}")
                    except Exception as e:
                        print(f"Failed to enroll teacher: {e}")
                
                result = created
            elif function_name == "create_user":
                # Admin-only operations use admin token
                canvas_client = self.admin_canvas if self.admin_canvas else self.canvas
                result = canvas_client.create_user(**arguments)
            elif function_name == "enroll_user":
                # Use admin token for enrollment operations
                canvas_client = self.admin_canvas if self.admin_canvas else self.canvas
                result = canvas_client.enroll_user(**arguments)
            elif function_name == "list_users":
                # Admin-only operations use admin token
                canvas_client = self.admin_canvas if self.admin_canvas else self.canvas
                users = canvas_client.list_users()
                result = {"total_users": len(users), "users": [{"id": u.get("id"), "name": u.get("name"), "login_id": u.get("login_id")} for u in users[:20]]}
            elif function_name == "list_modules":
                result = self.canvas.list_modules(arguments["course_id"])
            elif function_name == "create_module":
                result = self.canvas.create_module(**arguments)
            elif function_name == "create_assignment":
                result = self.canvas.create_assignment(**arguments)
            elif function_name == "create_page":
                result = self.canvas.create_page(**arguments)
            elif function_name == "publish_course":
                result = self.canvas.publish_course(arguments["course_id"])
            elif function_name == "create_discussion":
                result = self.canvas.create_discussion(**arguments)
            elif function_name == "create_announcement":
                result = self.canvas.create_announcement(**arguments)
            elif function_name == "update_syllabus":
                result = self.canvas.update_course_settings(arguments["course_id"], syllabus_body=arguments["syllabus_body"])
            elif function_name == "publish_module":
                result = self.canvas.publish_module(**arguments)
            elif function_name == "search_users":
                result = self.canvas.search_users(**arguments)

            else:
                result = {"error": f"Unknown function: {function_name}"}
            print(f"Tool result: {result}")
            return result
        except Exception as e:
            error_msg = f"{str(e)} - {traceback.format_exc()}"
            print(f"Tool execution error: {error_msg}")
            return {"error": str(e)}
    

