from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from file_manager import get_file_manager
from canvas_integration import CanvasLMS
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

@router.post("/upload-file")
async def upload_file(
    file: UploadFile = File(...),
    upload_type: str = Form(...),
    course_id: int = Form(...),
    item_name: str = Form(...),
    assignment_id: int = Form(None),
    module_id: int = Form(None),
    points: int = Form(100),
    description: str = Form(""),
    comment: str = Form("")
):
    """Handle file uploads and Canvas integration"""
    try:
        # Get Canvas connection
        canvas_url = os.getenv("CANVAS_URL", "")
        canvas_token = os.getenv("CANVAS_TOKEN", "")
        
        if not canvas_url or not canvas_token:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Canvas not configured"}
            )
        
        canvas = CanvasLMS(canvas_url, canvas_token)
        file_manager = get_file_manager(canvas)
        
        # Read file data
        file_data = await file.read()
        
        # Save file locally
        file_info = file_manager.save_uploaded_file(file_data, file.filename)
        if not file_info["success"]:
            return JSONResponse(
                status_code=400,
                content=file_info
            )
        
        # Execute based on upload type
        if upload_type == "assignment":
            result = file_manager.create_assignment_with_file(
                course_id=course_id,
                assignment_name=item_name,
                file_info=file_info,
                points=points,
                description=description
            )
        
        elif upload_type == "module":
            if not module_id:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "Module ID required for module upload"}
                )
            
            result = file_manager.add_file_to_module(
                course_id=course_id,
                module_id=module_id,
                file_info=file_info,
                item_title=item_name
            )
        
        elif upload_type == "submission":
            if not assignment_id:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": "Assignment ID required for submission"}
                )
            
            result = file_manager.submit_assignment(
                course_id=course_id,
                assignment_id=assignment_id,
                file_info=file_info,
                comment=comment
            )
        
        else:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Invalid upload type"}
            )
        
        # Cleanup local file
        file_manager.cleanup_local_file(file_info["file_path"])
        
        return JSONResponse(content=result)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )