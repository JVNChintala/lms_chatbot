import os
import sys
import warnings
from typing import Optional, List, Dict, Any

import requests
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import logging

warnings.filterwarnings("ignore", category=UserWarning)

sys.path.insert(0, os.path.dirname(__file__))

# Core services
from inference_systems.openai_inference import OpenAIInference
from canvas_agent import CanvasAgent
from canvas_integration import CanvasLMS

# Auth / session / storage
from session_manager import session_manager
from auth import create_demo_token, get_user_by_login
from conversations_db import conversations_db
from usage_tracker import usage_tracker

# Routers
from lti_routes import router as lti_router

# ---------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------

load_dotenv()

CANVAS_URL = os.getenv("CANVAS_URL", "")
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN", "")

app = FastAPI(title="LLM Inference API")

# Enable CORS for Canvas domains
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this to match your Canvas domain(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(lti_router)

# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------

class InferenceRequest(BaseModel):
    messages: List[Dict[str, Any]]
    temperature: float = 0.7
    max_tokens: int = 1000
    session_id: Optional[str] = None
    user_role: Optional[str] = None
    canvas_user_id: Optional[int] = None
    conversation_id: Optional[int] = None
    pending_tool: Optional[str] = None
    pending_tool_def: Optional[Dict[str, Any]] = None
    state: Optional[Dict[str, Any]] = None


class LoginRequest(BaseModel):
    username: str
    password: str


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


# ---------------------------------------------------------------------
# Core Endpoints
# ---------------------------------------------------------------------

@app.post("/inference")
async def inference(req: InferenceRequest):
    logger = logging.getLogger('main process')
    logger.info("Inference request: %s", req.model_dump())
    try:
        session_id = get_or_create_session(req.session_id, req.user_role)
        user_role = req.user_role or session_manager.get_session(session_id).get("role")

        # ---- Canvas-enabled inference
        if CANVAS_URL and CANVAS_TOKEN:
            canvas_user_id = req.canvas_user_id

            user_info = {
                "canvas_user_id": canvas_user_id,
                "role": user_role,
            }

            # Conversation tracking
            conv_id = req.conversation_id
            if canvas_user_id and not conv_id:
                conv_id = conversations_db.create_conversation(
                    canvas_user_id, "New Chat"
                )
            
            if conv_id:
                conversations_db.add_message(
                    conv_id, "user", req.messages[-1]["content"]
                )

            # Debug logging
            print(f"[MAIN] Creating CanvasAgent with canvas_user_id={canvas_user_id}, user_role={user_role}")
            
            # Restore state if provided
            if req.state:
                print(f"[MAIN] Restoring state: {req.state}")
            
            agent = CanvasAgent(
                CANVAS_URL,
                CANVAS_TOKEN,
                as_user_id=canvas_user_id if user_role != "admin" else None,
            )
            
            # Restore execution state if provided
            if req.state:
                agent.inference.execution_state = req.state

            result = agent.process_message(
                req.messages[-1]["content"],
                req.messages[:-1],
                user_role,
                user_info,
                pending_tool=req.pending_tool,
                pending_tool_def=req.pending_tool_def,
            )

            if conv_id:
                conversations_db.add_message(conv_id, "assistant", result["content"])

            return {
                "content": result["content"],
                "model": "gpt-4o-mini",
                "usage": result.get("usage", {}),
                "session_id": session_id,
                "conversation_id": conv_id,
                "analytics": result.get("analytics", {"quick_actions": []}),
                "tool_used": result.get("tool_used", False),
                "inference_system": result.get("inference_system", "OpenAI"),
                "pending_tool": result.get("pending_tool"),
                "pending_tool_def": result.get("pending_tool_def"),
                "state": result.get("state", {}),
                "status": result.get("status", "completed"),
            }

        # ---- Fallback OpenAI inference
        openai = OpenAIInference()
        if not openai.is_available():
            return {
                "content": "Canvas LMS assistant is currently unavailable.",
                "model": "gpt-4o-mini",
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
            "model": "gpt-4o-mini",
            "usage": result.get("usage", {}),
            "session_id": session_id,
        }

    except Exception as e:
        logger.exception("Inference error")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return load_html("canvas_widget.html")


@app.get("/canvas-embed")
async def canvas_embed():
    return load_html("canvas_embed.html")



# ---------------------------------------------------------------------
# Auth & User Management
# ---------------------------------------------------------------------

@app.post("/demo-login")
async def demo_login(req: LoginRequest):
    if not (CANVAS_URL and CANVAS_TOKEN):
        raise HTTPException(status_code=503, detail="Canvas LMS not configured")

    canvas_user = get_user_by_login(CANVAS_URL, CANVAS_TOKEN, req.username)
    if not canvas_user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    role = "student"
    try:
        enrollments_url = f"{CANVAS_URL.rstrip('/').replace('/api/v1','')}/api/v1/users/{canvas_user['id']}/enrollments"
        r = requests.get(enrollments_url, headers={"Authorization": f"Bearer {CANVAS_TOKEN}"}, timeout=5)
        if r.ok:
            for e in r.json():
                if "teacher" in e.get("type", "").lower():
                    role = "teacher"
                    break
    except Exception:
        pass

    return {
        "token": create_demo_token(req.username, role),
        "role": role,
        "username": req.username,
        "canvas_user_id": canvas_user["id"],
    }


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


# ---------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    
    # SSL configuration
    ssl_keyfile = os.getenv("SSL_KEYFILE")
    ssl_certfile = os.getenv("SSL_CERTFILE")
    
    if ssl_keyfile and ssl_certfile:
        # Production with SSL
        uvicorn.run(
            app, 
            host="0.0.0.0", 
            port=8001,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile
        )
    else:
        # Development without SSL
        uvicorn.run(app, host="0.0.0.0", port=8001)
