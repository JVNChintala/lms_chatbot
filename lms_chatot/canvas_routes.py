from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv
from canvas_integration import CanvasLMS

load_dotenv()

router = APIRouter(prefix="/canvas", tags=["Canvas LMS"])

CANVAS_URL = os.getenv("CANVAS_URL", "")
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN", "")

class CourseCreate(BaseModel):
    account_id: int
    name: str
    course_code: str

class ModuleCreate(BaseModel):
    course_id: int
    name: str

@router.get("/courses")
async def list_courses(account_id: Optional[int] = None):
    try:
        canvas = CanvasLMS(CANVAS_URL, CANVAS_TOKEN)
        return canvas.list_courses(account_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/courses")
async def create_course(course: CourseCreate):
    try:
        canvas = CanvasLMS(CANVAS_URL, CANVAS_TOKEN)
        return canvas.create_course(course.account_id, course.name, course.course_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/courses/{course_id}/modules")
async def list_modules(course_id: int):
    try:
        canvas = CanvasLMS(CANVAS_URL, CANVAS_TOKEN)
        return canvas.list_modules(course_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/modules")
async def create_module(module: ModuleCreate):
    try:
        canvas = CanvasLMS(CANVAS_URL, CANVAS_TOKEN)
        return canvas.create_module(module.course_id, module.name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
