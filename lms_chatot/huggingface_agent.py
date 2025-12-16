from canvas_integration import CanvasLMS
import json
import os
import traceback
import re
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import torch
from dotenv import load_dotenv

load_dotenv()

class HuggingFaceCanvasAgent:
    def __init__(self, canvas_url: str, canvas_token: str, user_id: int = None):
        print(f"HuggingFaceCanvasAgent initialized for user_id: {user_id}")
        self.canvas = CanvasLMS(canvas_url, canvas_token, as_user_id=user_id)
        self.admin_canvas = CanvasLMS(canvas_url, canvas_token)
        self.user_role = None
        self.user_info = None
        self.is_admin_mode = not user_id
        
        # Initialize Hugging Face model
        self.model_name = os.getenv("HF_MODEL", "microsoft/DialoGPT-medium")
        self.device = os.getenv("HF_DEVICE", "cpu")
        self.max_length = int(os.getenv("HF_MAX_LENGTH", "512"))
        self.temperature = float(os.getenv("HF_TEMPERATURE", "0.7"))
        self.do_sample = os.getenv("HF_DO_SAMPLE", "true").lower() == "true"
        
        self._load_model()
        
    def _load_model(self):
        """Load the Hugging Face model"""
        try:
            print(f"Loading model: {self.model_name}")
            
            # Use text generation pipeline for simplicity
            self.generator = pipeline(
                "text-generation",
                model=self.model_name,
                tokenizer=self.model_name,
                device=0 if self.device == "cuda" and torch.cuda.is_available() else -1,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            print(f"Model loaded successfully on {self.device}")
            
        except Exception as e:
            print(f"Error loading model: {e}")
            # Fallback to a smaller model
            try:
                print("Falling back to distilgpt2...")
                self.generator = pipeline(
                    "text-generation",
                    model="distilgpt2",
                    device=-1
                )
                print("Fallback model loaded successfully")
            except Exception as fallback_error:
                print(f"Fallback model failed: {fallback_error}")
                self.generator = None
    
    def process_message(self, user_message: str, conversation_history: list, user_role: str = None, user_info: dict = None) -> dict:
        """Process user message with tool detection and execution"""
        if user_role:
            self.user_role = user_role
        if user_info:
            self.user_info = user_info
        
        try:
            # Check if tool is needed
            tool_result = self._detect_and_execute_tool(user_message)
            if tool_result:
                return tool_result
            
            # Generate conversational response
            return self._generate_response(user_message, conversation_history)
            
        except Exception as e:
            error_details = traceback.format_exc()
            print(f"Agent Error: {error_details}")
            return {"content": f"I encountered an error: {str(e)}", "tool_used": False}
    
    def _detect_and_execute_tool(self, user_message):
        """Simple pattern-based tool detection and execution"""
        msg = user_message.lower()
        
        # List courses
        if any(word in msg for word in ['list', 'show', 'view']) and 'course' in msg:
            result = self._execute_tool('list_courses', {})
            return {
                "content": self._format_tool_response('list_courses', result),
                "tool_used": True,
                "tool_results": [{"function_name": "list_courses", "result": result}]
            }
        
        # Create course
        if 'create' in msg and 'course' in msg:
            name_match = re.search(r'course[\\s\\"\\\']+([^\\"\\\'\\n\\.]+)', user_message, re.IGNORECASE)
            name = name_match.group(1).strip() if name_match else "New Course"
            code = name.replace(' ', '').upper()[:10]
            
            args = {'account_id': 1, 'name': name, 'course_code': code}
            result = self._execute_tool('create_course', args)
            return {
                "content": self._format_tool_response('create_course', result),
                "tool_used": True,
                "tool_results": [{"function_name": "create_course", "result": result}]
            }
        
        # List modules
        if any(word in msg for word in ['list', 'show', 'view']) and 'module' in msg:
            # Try to extract course ID or use first available course
            course_id_match = re.search(r'course[\\s]+(\\d+)', user_message, re.IGNORECASE)
            if course_id_match:
                course_id = int(course_id_match.group(1))
            else:
                # Get first available course
                courses_result = self._execute_tool('list_courses', {})
                if courses_result.get('courses'):
                    course_id = courses_result['courses'][0]['id']
                else:
                    return {
                        "content": "No courses found. Please create a course first.",
                        "tool_used": False
                    }
            
            result = self._execute_tool('list_modules', {'course_id': course_id})
            return {
                "content": self._format_tool_response('list_modules', result),
                "tool_used": True,
                "tool_results": [{"function_name": "list_modules", "result": result}]
            }
        
        # Create module
        if 'create' in msg and 'module' in msg:
            name_match = re.search(r'module[\\s\\"\\\']+([^\\"\\\'\\n\\.]+)', user_message, re.IGNORECASE)
            name = name_match.group(1).strip() if name_match else "New Module"
            
            # Get course ID
            course_id_match = re.search(r'course[\\s]+(\\d+)', user_message, re.IGNORECASE)
            if course_id_match:
                course_id = int(course_id_match.group(1))
            else:
                courses_result = self._execute_tool('list_courses', {})
                if courses_result.get('courses'):
                    course_id = courses_result['courses'][0]['id']
                else:
                    return {
                        "content": "No courses found. Please create a course first.",
                        "tool_used": False
                    }
            
            args = {'course_id': course_id, 'name': name}
            result = self._execute_tool('create_module', args)
            return {
                "content": self._format_tool_response('create_module', result),
                "tool_used": True,
                "tool_results": [{"function_name": "create_module", "result": result}]
            }
        
        # Create assignment
        if 'create' in msg and 'assignment' in msg:
            name_match = re.search(r'assignment[\\s\\"\\\']+([^\\"\\\'\\n\\.]+)', user_message, re.IGNORECASE)
            name = name_match.group(1).strip() if name_match else "New Assignment"
            
            course_id_match = re.search(r'course[\\s]+(\\d+)', user_message, re.IGNORECASE)
            if course_id_match:
                course_id = int(course_id_match.group(1))
            else:
                courses_result = self._execute_tool('list_courses', {})
                if courses_result.get('courses'):
                    course_id = courses_result['courses'][0]['id']
                else:
                    return {
                        "content": "No courses found. Please create a course first.",
                        "tool_used": False
                    }
            
            args = {'course_id': course_id, 'name': name, 'points': 100}
            result = self._execute_tool('create_assignment', args)
            return {
                "content": self._format_tool_response('create_assignment', result),
                "tool_used": True,
                "tool_results": [{"function_name": "create_assignment", "result": result}]
            }
        
        # Admin tools
        if self.user_role == "admin":
            if 'list' in msg and 'user' in msg:
                result = self._execute_tool('list_users', {})
                return {
                    "content": self._format_tool_response('list_users', result),
                    "tool_used": True,
                    "tool_results": [{"function_name": "list_users", "result": result}]
                }
        
        return None
    
    def _generate_response(self, user_message, conversation_history):
        """Generate conversational response using Hugging Face model"""
        if not self.generator:
            return {"content": "I'm having trouble with the language model. Please try a specific Canvas command like 'list courses' or 'create course'.", "tool_used": False}
        
        try:
            # Build context
            role_context = self._get_role_context()
            system_prompt = f"You are a Canvas LMS assistant. {role_context} Be helpful and concise."
            
            # Prepare input
            context = f"{system_prompt}\\n\\nUser: {user_message}\\nAssistant:"
            
            # Generate response
            outputs = self.generator(
                context,
                max_length=len(context.split()) + 100,
                temperature=self.temperature,
                do_sample=self.do_sample,
                pad_token_id=self.generator.tokenizer.eos_token_id,
                num_return_sequences=1
            )
            
            # Extract response
            generated_text = outputs[0]['generated_text']
            response = generated_text.split("Assistant:")[-1].strip()
            
            # Clean up response
            if not response or len(response) < 10:
                response = "I can help you with Canvas LMS tasks. Try asking me to 'list courses', 'create a course', or 'show modules'."
            
            return {"content": response, "tool_used": False}
            
        except Exception as e:
            print(f"Generation error: {e}")
            return {"content": "I can help you with Canvas LMS. Try commands like 'list courses', 'create course', or 'show modules'.", "tool_used": False}
    
    def _get_role_context(self):
        """Get role-specific context"""
        if self.user_role == "admin":
            return "You have administrator privileges and can manage users and courses."
        elif self.user_role == "teacher":
            return "You can create and manage courses, modules, and assignments."
        elif self.user_role == "student":
            return "You can view courses and modules you're enrolled in."
        return "Ask me about Canvas LMS courses, modules, and assignments."
    
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
                
            elif function_name == "list_modules":
                return self.canvas.list_modules(arguments["course_id"])
                
            elif function_name == "create_module":
                return self.canvas.create_module(**arguments)
                
            elif function_name == "create_assignment":
                return self.canvas.create_assignment(**arguments)
                
            elif function_name == "list_users" and self.user_role == "admin":
                users = self.admin_canvas.list_users()
                return {"total_users": len(users), "users": [{"id": u.get("id"), "name": u.get("name"), "login_id": u.get("login_id")} for u in users[:20]]}
                
            else:
                return {"error": f"Unknown or unauthorized function: {function_name}"}
                
        except Exception as e:
            error_msg = f"{str(e)} - {traceback.format_exc()}"
            print(f"Tool execution error: {error_msg}")
            return {"error": str(e)}
    
    def _format_tool_response(self, tool_name, result):
        """Format tool results for user"""
        if tool_name == 'list_courses':
            if result.get('courses'):
                courses_list = "\\n".join([f"• {c['name']} ({c['course_code']}) - {c['workflow_state']}" for c in result['courses']])
                return f"📚 Found {result['total_courses']} courses:\\n{courses_list}"
            return "No courses found."
            
        elif tool_name == 'create_course':
            return f"✅ Created course: {result.get('name', 'Unknown')} (ID: {result.get('id', 'Unknown')})"
            
        elif tool_name == 'list_modules':
            if isinstance(result, list) and result:
                modules_list = "\\n".join([f"• {m.get('name', 'Unnamed')}" for m in result])
                return f"📖 Found {len(result)} modules:\\n{modules_list}"
            return "No modules found."
            
        elif tool_name == 'create_module':
            return f"✅ Created module: {result.get('name', 'Unknown')}"
            
        elif tool_name == 'create_assignment':
            return f"✅ Created assignment: {result.get('name', 'Unknown')}"
            
        elif tool_name == 'list_users':
            if result.get('users'):
                users_list = "\\n".join([f"• {u['name']} ({u['login_id']})" for u in result['users']])
                return f"👥 Found {result['total_users']} users:\\n{users_list}"
            return "No users found."
        
        return f"Operation completed: {str(result)}"