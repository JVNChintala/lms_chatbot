import os
import sys
import warnings
from typing import Optional, List, Dict, Any

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

warnings.filterwarnings("ignore", category=UserWarning)

sys.path.insert(0, os.path.dirname(__file__))

# Routers
from canvas_routes import router as canvas_router
from fast_analytics import router as analytics_router
from file_upload_routes import router as file_upload_router

# Core services
from inference_systems.openai_inference import OpenAIInference
from canvas_agent import CanvasAgent
from canvas_integration import CanvasLMS
from dashboard_widgets import DashboardWidgets

# Auth / session / storage
from session_manager import session_manager
from auth import (
    create_demo_token,
    CanvasAuth,
    get_user_by_login,
    create_user_access_token,
)
from user_store import user_store
from conversations_db import conversations_db
from usage_tracker import usage_tracker

# ---------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------

load_dotenv()

CANVAS_URL = os.getenv("CANVAS_URL", "")
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN", "")

app = FastAPI(title="LLM Inference API")

app.include_router(canvas_router)
app.include_router(analytics_router)
app.include_router(file_upload_router)

# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------

class InferenceRequest(BaseModel):
    model: str
    messages: List[Dict[str, Any]]
    temperature: float = 0.7
    max_tokens: int = 1000
    session_id: Optional[str] = None
    user_role: Optional[str] = None
    canvas_user_id: Optional[int] = None
    conversation_id: Optional[int] = None


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


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def get_or_create_session(session_id: Optional[str], role: Optional[str]) -> str:
    if not session_id or not session_manager.get_session(session_id):
        session_id = session_manager.create_session(role)
    if role:
        session_manager.set_role(session_id, role)
    return session_id


def load_html(template_name: str) -> HTMLResponse:
    path = os.path.join(os.path.dirname(__file__), "templates", template_name)
    with open(path, encoding="utf-8") as f:
        return HTMLResponse(content=f.read())


def resolve_canvas_user_id(role: str, provided_id: Optional[int]) -> Optional[int]:
    if provided_id:
        return provided_id

    for _, user in user_store.users.items():
        if user.get("role") == role:
            return user.get("canvas_user_id")
    return None


# ---------------------------------------------------------------------
# Core Endpoints
# ---------------------------------------------------------------------

@app.post("/inference")
async def inference(req: InferenceRequest):
    try:
        session_id = get_or_create_session(req.session_id, req.user_role)
        user_role = req.user_role or session_manager.get_session(session_id).get("role")

        # ---- Canvas-enabled inference
        if CANVAS_URL and CANVAS_TOKEN:
            canvas_user_id = resolve_canvas_user_id(user_role, req.canvas_user_id)

            user_info = {
                "canvas_user_id": canvas_user_id,
                "role": user_role,
            }

            # Conversation tracking
            conv_id = None
            if canvas_user_id:
                conv_id = req.conversation_id or conversations_db.create_conversation(
                    canvas_user_id, "New Chat"
                )
                conversations_db.add_message(
                    conv_id, "user", req.messages[-1]["content"]
                )

            agent = CanvasAgent(
                CANVAS_URL,
                CANVAS_TOKEN,
                as_user_id=None if user_role == "admin" else canvas_user_id,
            )

            result = agent.process_message(
                req.messages[-1]["content"],
                req.messages[:-1],
                user_role,
                user_info,
            )

            if conv_id:
                conversations_db.add_message(conv_id, "assistant", result["content"])

            return {
                "content": result["content"],
                "model": req.model,
                "usage": {},
                "session_id": session_id,
            }

        # ---- Fallback OpenAI inference
        openai = OpenAIInference(use_multi_model=False)
        if not openai.is_available():
            return {
                "content": "Canvas LMS assistant is currently unavailable.",
                "model": req.model,
                "usage": {},
                "session_id": session_id,
            }

        result = openai.call_with_tools(
            "You are a friendly Canvas LMS assistant.",
            req.messages,
            [],
        )

        return {
            "content": result.get("content", ""),
            "model": req.model,
            "usage": result.get("usage", {}),
            "session_id": session_id,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return HTMLResponse("<script>location.href='/canvas-login'</script>")


@app.get("/canvas-login")
async def canvas_login():
    return load_html("canvas_login.html")


@app.get("/canvas-dashboard")
async def canvas_dashboard():
    return load_html("vue_dashboard.html")


@app.get("/canvas-embed")
async def canvas_embed():
    return load_html("canvas_embed.html")


# ---------------------------------------------------------------------
# Auth & User Management
# ---------------------------------------------------------------------

@app.post("/demo-login")
async def demo_login(req: LoginRequest):
    demo_user = user_store.authenticate(req.username, req.password)
    if demo_user:
        token = create_demo_token(demo_user["login_id"], demo_user["role"])
        return {
            "token": token,
            "role": demo_user["role"],
            "username": demo_user["login_id"],
            "canvas_user_id": demo_user["canvas_user_id"],
        }

    if not (CANVAS_URL and CANVAS_TOKEN):
        role = "teacher" if "teacher" in req.username.lower() else "student"
        canvas_user_id = hash(req.username) % 10000
        user_store.add_user(req.username, req.password, role, canvas_user_id)
        return {
            "token": create_demo_token(req.username, role),
            "role": role,
            "username": req.username,
            "canvas_user_id": canvas_user_id,
        }

    canvas_user = get_user_by_login(CANVAS_URL, CANVAS_TOKEN, req.username)
    if not canvas_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    role = "student"
    enrollments_url = f"{CANVAS_URL.rstrip('/').replace('/api/v1','')}/api/v1/users/{canvas_user['id']}/enrollments"
    r = requests.get(enrollments_url, headers={"Authorization": f"Bearer {CANVAS_TOKEN}"})
    if r.ok:
        for e in r.json():
            if "teacher" in e.get("type", "").lower():
                role = "teacher"
                break

    create_user_access_token(CANVAS_URL, CANVAS_TOKEN, canvas_user["id"])
    user_store.add_user(req.username, req.password, role, canvas_user["id"])

    return {
        "token": create_demo_token(req.username, role),
        "role": role,
        "username": req.username,
        "canvas_user_id": canvas_user["id"],
    }


@app.post("/register-user")
async def register_user(req: UserCreateRequest):
    user_store.add_user(req.login_id, req.password, req.role, req.canvas_user_id)
    return {"success": True}


# ---------------------------------------------------------------------
# Conversations & Analytics
# ---------------------------------------------------------------------

@app.get("/conversations")
async def get_conversations(canvas_user_id: int):
    return {"conversations": conversations_db.get_conversations(canvas_user_id)}


@app.post("/conversations")
async def create_conversation(payload: Dict[str, Any]):
    conv_id = conversations_db.create_conversation(
        payload["canvas_user_id"], payload.get("title", "New Conversation")
    )
    return {"conversation_id": conv_id}


@app.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: int):
    return {"messages": conversations_db.get_messages(conversation_id)}


@app.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    conversations_db.delete_conversation(conversation_id)
    return {"success": True}


@app.put("/conversations/{conversation_id}/title")
async def update_title(conversation_id: int, payload: Dict[str, Any]):
    conversations_db.update_conversation_title(
        conversation_id, payload.get("title", "Untitled")
    )
    return {"success": True}


@app.get("/usage-stats")
async def usage_stats(canvas_user_id: Optional[int] = None, days: int = 30):
    return {"usage_stats": usage_tracker.get_usage_stats(canvas_user_id, days)}


@app.get("/dashboard-widgets")
async def dashboard_widgets(user_role: str, canvas_user_id: Optional[int] = None):
    canvas = CanvasLMS(
        CANVAS_URL,
        CANVAS_TOKEN,
        as_user_id=None if user_role == "admin" else canvas_user_id,
    )
    manager = DashboardWidgets(canvas)

    if user_role == "student":
        widgets = manager.get_student_widgets()
    elif user_role == "teacher":
        widgets = manager.get_teacher_widgets()
    elif user_role == "admin":
        widgets = manager.get_admin_widgets()
    else:
        widgets = {}

    return {"widgets": widgets}


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
