import warnings
warnings.filterwarnings("ignore", category=UserWarning)

from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from litellm import completion
import os
import sys
import requests
from dotenv import load_dotenv
from typing import Optional
sys.path.insert(0, os.path.dirname(__file__))
from canvas_routes import router as canvas_router
from fast_analytics import router as analytics_router
from file_upload_routes import router as file_upload_router
from canvas_agent import CanvasAgent
from session_manager import session_manager
from auth import create_demo_token, verify_demo_token, CanvasAuth, get_user_by_login, create_user_access_token
from user_store import user_store
from canvas_integration import CanvasLMS
from conversation_db import conversation_db
from dashboard_widgets import DashboardWidgets
from conversations_db import conversations_db


load_dotenv()

app = FastAPI(title="LLM Inference API")
app.include_router(canvas_router)
app.include_router(analytics_router)
app.include_router(file_upload_router)

class InferenceRequest(BaseModel):
    model: str
    messages: list[dict]
    temperature: float = 0.7
    max_tokens: int = 1000
    session_id: Optional[str] = None
    user_role: Optional[str] = None
    canvas_user_id: Optional[int] = None
    conversation_id: Optional[int] = None



@app.post("/inference")
async def inference(request: InferenceRequest):
    try:
        canvas_url = os.getenv("CANVAS_URL", "")
        canvas_token = os.getenv("CANVAS_TOKEN", "")
        
        session_id = request.session_id
        if not session_id:
            session_id = session_manager.create_session(request.user_role)
        
        session = session_manager.get_session(session_id)
        if not session:
            session_id = session_manager.create_session(request.user_role)
            session = session_manager.get_session(session_id)
        
        user_role = request.user_role or session.get("role")
        if request.user_role:
            session_manager.set_role(session_id, request.user_role)
        
        if canvas_url and canvas_token:
            # Get user's Canvas ID - either from request (real Canvas embed) or user store (demo)
            canvas_user_id = request.canvas_user_id
            user_info = {}
            
            print(f"[INFERENCE] Initial canvas_user_id from request: {canvas_user_id}")
            print(f"[INFERENCE] User role: {user_role}")
            
            if not canvas_user_id:
                print(f"[INFERENCE] No canvas_user_id in request, checking user_store...")
                # Find user by role in user_store as fallback
                for username, user_data in user_store.users.items():
                    if user_data.get("role") == user_role:
                        canvas_user_id = user_data.get("canvas_user_id")
                        print(f"[INFERENCE] Found user {username} with canvas_user_id: {canvas_user_id}")
                        break
            
            user_info = {"canvas_user_id": canvas_user_id}
            
            print(f"[INFERENCE] Final canvas_user_id: {canvas_user_id}")
            
            # For admin, don't use as_user_id; for others, use their canvas_user_id
            print(f"User role: {user_role}, Canvas user ID: {canvas_user_id}")
            
            # Save to conversations DB if canvas_user_id exists
            if canvas_user_id:
                # Create or get conversation
                if not hasattr(request, 'conversation_id') or not request.conversation_id:
                    conv_id = conversations_db.create_conversation(canvas_user_id, "New Chat")
                else:
                    conv_id = request.conversation_id
                
                conversations_db.add_message(conv_id, "user", request.messages[-1]["content"])
            
            agent = CanvasAgent(canvas_url, canvas_token, canvas_user_id if user_role != "admin" else None)
            result = agent.process_message(request.messages[-1]["content"], request.messages[:-1], user_role, user_info)
            
            # Save assistant response
            if canvas_user_id:
                conversations_db.add_message(conv_id, "assistant", result["content"])
            
            return {"content": result["content"], "model": request.model, "usage": {}, "session_id": session_id}
        else:
            print("\n" + "="*80)
            print("[MAIN.PY] Using direct LiteLLM completion (no Canvas integration)")
            print(f"Model requested: {request.model}")
            print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT SET')[:20]}..." if os.getenv('OPENAI_API_KEY') else "OPENAI_API_KEY: NOT SET")
            print("="*80 + "\n")
            
            response = completion(
                model=request.model,
                messages=request.messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens
            )
            
            print(f"\n[MAIN.PY] Response model used: {response.model}\n")
            
            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": response.usage.dict(),
                "session_id": session_id
            }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Inference Error: {error_details}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/performance")
async def get_performance_stats():
    """Get AWS Bedrock Agent performance statistics"""
    try:
        return {
            "performance": {
                "status": "AWS Bedrock agent active",
                "type": "Claude 3 Sonnet with Canvas tools",
                "dependencies": "AWS Bedrock, Claude 3 Sonnet",
                "memory_usage": "Minimal"
            }
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLResponse(content="<script>window.location.href='/canvas-login'</script>")

@app.get("/canvas-login", response_class=HTMLResponse)
async def canvas_login():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "canvas_login.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/canvas-dashboard", response_class=HTMLResponse)
async def canvas_dashboard():
    template_path = os.path.join(os.path.dirname(__file__), "templates", "vue_dashboard.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/canvas-embed", response_class=HTMLResponse)
async def canvas_embed():
    """Embeddable chatbot for real Canvas LMS"""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "canvas_embed.html")
    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()

class LoginRequest(BaseModel):
    username: str
    password: str

class UserCreateRequest(BaseModel):
    login_id: str
    password: str
    name: str
    email: str
    role: str
    canvas_user_id: int

@app.post("/demo-login")
async def demo_login(request: LoginRequest):
    canvas_url = os.getenv("CANVAS_URL", "")
    canvas_token = os.getenv("CANVAS_TOKEN", "")
    
    print(f"Login attempt: username={request.username}")
    
    # First check demo user store (for admin and created users)
    demo_user = user_store.authenticate(request.username, request.password)
    if demo_user:
        print(f"User found in demo store: {request.username}")
        token = create_demo_token(demo_user["login_id"], demo_user["role"])
        return {"token": token, "role": demo_user["role"], "username": demo_user["login_id"], "canvas_user_id": demo_user["canvas_user_id"]}
    
    print(f"User not in demo store, checking Canvas API...")
    
    # If not in demo store, check Canvas API
    if canvas_url and canvas_token:
        canvas_user = get_user_by_login(canvas_url, canvas_token, request.username)
        print(f"Canvas user lookup result: {canvas_user}")
        
        if canvas_user:
            try:
                # Check if this user owns the admin token
                token_owner_url = f"{canvas_url.rstrip('/').replace('/api/v1', '')}/api/v1/users/self"
                token_owner_response = requests.get(token_owner_url, headers={"Authorization": f"Bearer {canvas_token}"})
                token_owner_id = token_owner_response.json().get('id') if token_owner_response.ok else None
                
                # If user owns the admin token, they're an admin
                if token_owner_id == canvas_user['id']:
                    role = "admin"
                    print(f"User owns the admin token - setting role to admin")
                else:
                    # Use admin token to get user enrollments
                    url = f"{canvas_url.rstrip('/').replace('/api/v1', '')}/api/v1/users/{canvas_user['id']}/enrollments"
                    headers = {"Authorization": f"Bearer {canvas_token}"}
                    response = requests.get(url, headers=headers)
                    enrollments = response.json() if response.ok else []
                    
                    print(f"User enrollments: {len(enrollments)} found")
                    
                    # Determine role from enrollments
                    role = "student"
                    for enrollment in enrollments:
                        role_type = enrollment.get('type', '').lower()
                        if 'teacher' in role_type or 'instructor' in role_type:
                            role = "teacher"
                            break
                    
                    print(f"Determined role: {role}")
                
                # Generate user-specific Canvas access token
                user_canvas_token = create_user_access_token(canvas_url, canvas_token, canvas_user['id'])
                
                # Register in demo store for future logins
                user_store.add_user(request.username, request.password, role, canvas_user['id'], user_canvas_token)
                
                token = create_demo_token(request.username, role)
                return {"token": token, "role": role, "username": request.username, "canvas_user_id": canvas_user['id']}
            except Exception as e:
                print(f"Error processing Canvas user: {e}")
                import traceback
                traceback.print_exc()
    else:
        print("Canvas URL or token not configured")
    
    print(f"Login failed for: {request.username}")
    raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/register-user")
async def register_user(request: UserCreateRequest):
    """Register a Canvas user in demo system"""
    user_store.add_user(request.login_id, request.password, request.role, request.canvas_user_id)
    return {"success": True, "message": f"User {request.login_id} registered"}

@app.post("/canvas-auth")
async def canvas_auth(access_token: str):
    """Authenticate with real Canvas LMS and get user role"""
    try:
        canvas_url = os.getenv("CANVAS_URL", "")
        auth = CanvasAuth(canvas_url)
        profile = auth.get_user_profile(access_token)
        role = auth.determine_primary_role(access_token)
        return {"user": profile, "role": role}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@app.get("/conversations")
async def get_conversations(canvas_user_id: int):
    """Get all conversations for a user"""
    try:
        conversations = conversations_db.get_conversations(canvas_user_id)
        return {"conversations": conversations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/conversations")
async def create_conversation(request: dict):
    """Create a new conversation"""
    try:
        canvas_user_id = request.get("canvas_user_id")
        title = request.get("title", "New Conversation")
        conv_id = conversations_db.create_conversation(canvas_user_id, title)
        return {"conversation_id": conv_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: int):
    """Get messages for a conversation"""
    try:
        messages = conversations_db.get_messages(conversation_id)
        return {"messages": messages}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """Delete a conversation"""
    try:
        conversations_db.delete_conversation(conversation_id)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/conversations/{conversation_id}/title")
async def update_conversation_title(conversation_id: int, request: dict):
    """Update conversation title"""
    try:
        title = request.get("title", "Untitled")
        conversations_db.update_conversation_title(conversation_id, title)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics")
async def get_analytics(user_role: str, canvas_user_id: Optional[int] = None):
    """Get real-time analytics from Canvas API"""
    try:
        canvas_url = os.getenv("CANVAS_URL", "")
        admin_canvas_token = os.getenv("CANVAS_TOKEN", "")
        
        if not canvas_url or not admin_canvas_token:
            return {"analytics": {}}
        
        # Get canvas_user_id from user_store if not provided
        if user_role != "admin" and not canvas_user_id:
            for username, user_data in user_store.users.items():
                if user_data.get("role") == user_role:
                    canvas_user_id = user_data.get("canvas_user_id")
                    break
        
        canvas = CanvasLMS(canvas_url, admin_canvas_token, as_user_id=canvas_user_id if user_role != "admin" else None)
        admin_canvas = CanvasLMS(canvas_url, admin_canvas_token)
        
        if user_role == "admin":
            courses = admin_canvas.list_account_courses()
            users = admin_canvas.list_users()
            
            # Enhanced admin analytics
            course_details = []
            total_enrollments = 0
            total_modules = 0
            
            for course in courses[:10]:  # Top 10 courses for performance
                try:
                    enrollments_url = f"{canvas_url.rstrip('/').replace('/api/v1', '')}/api/v1/courses/{course.get('id')}/enrollments"
                    enrollments_response = requests.get(enrollments_url, headers={"Authorization": f"Bearer {admin_canvas_token}"})
                    enrollments = enrollments_response.json() if enrollments_response.ok else []
                    
                    modules = admin_canvas.list_modules(course.get("id"))
                    total_modules += len(modules)
                    
                    students = len([e for e in enrollments if e.get('type') == 'StudentEnrollment'])
                    teachers = len([e for e in enrollments if e.get('type') == 'TeacherEnrollment'])
                    total_enrollments += len(enrollments)
                    
                    course_details.append({
                        "id": course.get("id"),
                        "name": course.get("name"),
                        "students": students,
                        "teachers": teachers,
                        "modules": len(modules),
                        "state": course.get("workflow_state")
                    })
                except:
                    pass
            
            user_roles = {}
            for user in users:
                # Simplified role detection
                role = "student"  # default
                user_roles[role] = user_roles.get(role, 0) + 1
            
            analytics = {
                "total_courses": len(courses),
                "published_courses": len([c for c in courses if c.get("workflow_state") == "available"]),
                "total_users": len(users),
                "total_enrollments": total_enrollments,
                "total_modules": total_modules,
                "course_details": course_details,
                "user_distribution": user_roles,
                "quick_actions": [
                    {"action": "create_course", "label": "📚 Create Course"},
                    {"action": "create_user", "label": "👤 Add User"},
                    {"action": "list_courses", "label": "📋 View All Courses"}
                ]
            }
        elif user_role in ["teacher", "faculty", "instructor"]:
            courses = canvas.list_courses()
            total_modules = 0
            total_assignments = 0
            student_progress = []
            course_details = []
            
            for course in courses:
                try:
                    modules = canvas.list_modules(course.get("id"))
                    total_modules += len(modules)
                    
                    # Get course enrollments for student progress
                    enrollments_url = f"{canvas_url.rstrip('/').replace('/api/v1', '')}/api/v1/courses/{course.get('id')}/enrollments"
                    enrollments_response = requests.get(enrollments_url, headers={"Authorization": f"Bearer {admin_canvas_token}"})
                    enrollments = enrollments_response.json() if enrollments_response.ok else []
                    
                    students = [e for e in enrollments if e.get('type') == 'StudentEnrollment']
                    course_details.append({
                        "id": course.get("id"),
                        "name": course.get("name"),
                        "students": len(students),
                        "modules": len(modules),
                        "state": course.get("workflow_state")
                    })
                    
                    for student in students[:5]:  # Top 5 students per course
                        student_progress.append({
                            "course": course.get("name"),
                            "student": student.get("user", {}).get("name", "Unknown"),
                            "progress": f"{student.get('grades', {}).get('current_score', 0) or 0:.1f}%"
                        })
                except:
                    pass
            
            analytics = {
                "total_courses": len(courses),
                "published_courses": len([c for c in courses if c.get("workflow_state") == "available"]),
                "total_modules": total_modules,
                "total_students": sum([c["students"] for c in course_details]),
                "course_details": course_details,
                "student_progress": student_progress,
                "quick_actions": [
                    {"action": "create_course", "label": "📚 Create Course"},
                    {"action": "create_module", "label": "📖 Add Module"},
                    {"action": "create_assignment", "label": "📝 Create Assignment"}
                ]
            }
        else:  # student
            courses = canvas.list_courses()
            analytics = {
                "enrolled_courses": len(courses),
                "active_courses": len([c for c in courses if c.get("workflow_state") == "available"]),
                "quick_actions": [
                    {"action": "list_courses", "label": "📚 My Courses"},
                    {"action": "view_assignments", "label": "📝 Assignments"}
                ]
            }
        
        return {"analytics": analytics}
    except Exception as e:
        import traceback
        print(f"Analytics error: {traceback.format_exc()}")
        return {"analytics": {}}

@app.get("/dashboard-widgets")
async def get_dashboard_widgets(user_role: str, canvas_user_id: Optional[int] = None):
    """Get role-based dashboard widgets"""
    try:
        canvas_url = os.getenv("CANVAS_URL", "")
        admin_canvas_token = os.getenv("CANVAS_TOKEN", "")
        
        if not canvas_url or not admin_canvas_token:
            return {"widgets": {}}
        
        # Get canvas_user_id from user_store
        print(f"[DASHBOARD] Looking for user with role={user_role}, current canvas_user_id={canvas_user_id}")
        print(f"[DASHBOARD] All users in store: {list(user_store.users.keys())}")
        if user_role != "admin" and not canvas_user_id:
            # This is a fallback - ideally canvas_user_id should be passed from frontend
            print(f"[DASHBOARD] Warning: No canvas_user_id provided for {user_role}")
            canvas_user_id = None
        
        print(f"[DASHBOARD] Creating CanvasLMS with as_user_id={canvas_user_id}, role={user_role}")
        canvas = CanvasLMS(canvas_url, admin_canvas_token, as_user_id=canvas_user_id if user_role != "admin" else None)
        widgets_manager = DashboardWidgets(canvas)
        
        if user_role == "student":
            widgets = widgets_manager.get_student_widgets()
        elif user_role == "teacher":
            widgets = widgets_manager.get_teacher_widgets()
        elif user_role == "admin":
            widgets = widgets_manager.get_admin_widgets()
        else:
            widgets = {}
        
        return {"widgets": widgets}
    except Exception as e:
        import traceback
        print(f"Widget error: {traceback.format_exc()}")
        return {"widgets": {}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
