import os
import uuid
import mimetypes
import requests
from typing import Dict, List, Any, Optional
from werkzeug.utils import secure_filename
from canvas_integration import CanvasLMS

class FileManager:
    """Handle file uploads and Canvas integration"""
    
    def __init__(self, canvas: CanvasLMS, upload_folder: str = "uploads"):
        self.canvas = canvas
        self.upload_folder = upload_folder
        self.allowed_extensions = {
            'images': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg'},
            'documents': {'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt'},
            'presentations': {'ppt', 'pptx', 'odp'},
            'spreadsheets': {'xls', 'xlsx', 'ods', 'csv'},
            'videos': {'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'},
            'audio': {'mp3', 'wav', 'ogg', 'aac', 'm4a'},
            'archives': {'zip', 'rar', '7z', 'tar', 'gz'}
        }
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        
        # Create upload directory
        os.makedirs(upload_folder, exist_ok=True)
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        if '.' not in filename:
            return False
        
        ext = filename.rsplit('.', 1)[1].lower()
        all_extensions = set()
        for extensions in self.allowed_extensions.values():
            all_extensions.update(extensions)
        
        return ext in all_extensions
    
    def get_file_type(self, filename: str) -> str:
        """Get file type category"""
        if '.' not in filename:
            return 'unknown'
        
        ext = filename.rsplit('.', 1)[1].lower()
        for file_type, extensions in self.allowed_extensions.items():
            if ext in extensions:
                return file_type
        return 'unknown'
    
    def save_uploaded_file(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Save uploaded file locally"""
        try:
            if not self.is_allowed_file(filename):
                return {"success": False, "error": "File type not allowed"}
            
            if len(file_data) > self.max_file_size:
                return {"success": False, "error": "File too large (max 100MB)"}
            
            # Generate unique filename
            secure_name = secure_filename(filename)
            unique_id = str(uuid.uuid4())[:8]
            final_filename = f"{unique_id}_{secure_name}"
            file_path = os.path.join(self.upload_folder, final_filename)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            return {
                "success": True,
                "filename": final_filename,
                "original_name": filename,
                "file_path": file_path,
                "file_size": len(file_data),
                "file_type": self.get_file_type(filename),
                "mime_type": mimetypes.guess_type(filename)[0]
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def upload_to_canvas(self, file_info: Dict[str, Any], course_id: int, folder_name: str = "Uploaded Files") -> Dict[str, Any]:
        """Upload file to Canvas course"""
        try:
            # Canvas file upload API call
            upload_url = f"{self.canvas.base_url}/api/v1/courses/{course_id}/files"
            
            # Step 1: Request upload URL
            upload_data = {
                "name": file_info["original_name"],
                "size": file_info["file_size"],
                "content_type": file_info["mime_type"],
                "parent_folder_path": folder_name
            }
            
            response = requests.post(upload_url, headers=self.canvas.headers, data=upload_data)
            response.raise_for_status()
            upload_info = response.json()
            
            # Step 2: Upload file to Canvas
            with open(file_info["file_path"], 'rb') as f:
                files = {'file': f}
                upload_response = requests.post(
                    upload_info['upload_url'],
                    data=upload_info['upload_params'],
                    files=files
                )
                upload_response.raise_for_status()
            
            # Step 3: Confirm upload
            confirm_response = requests.post(upload_info['upload_url'], data=upload_info['upload_params'])
            canvas_file = confirm_response.json()
            
            return {
                "success": True,
                "canvas_file_id": canvas_file.get("id"),
                "canvas_file_url": canvas_file.get("url"),
                "display_name": canvas_file.get("display_name"),
                "folder": folder_name
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def create_assignment_with_file(self, course_id: int, assignment_name: str, file_info: Dict[str, Any], 
                                  points: int = 100, description: str = "") -> Dict[str, Any]:
        """Create Canvas assignment with uploaded file"""
        try:
            # Upload file to Canvas first
            canvas_upload = self.upload_to_canvas(file_info, course_id, "Assignment Files")
            
            if not canvas_upload["success"]:
                return canvas_upload
            
            # Create assignment with file attachment
            assignment_description = f"{description}\n\n<p><strong>Assignment File:</strong></p>"
            assignment_description += f'<p><a href="{canvas_upload["canvas_file_url"]}" target="_blank">'
            assignment_description += f'{canvas_upload["display_name"]}</a></p>'
            
            assignment = self.canvas.create_assignment(
                course_id=course_id,
                name=assignment_name,
                points=points,
                description=assignment_description
            )
            
            return {
                "success": True,
                "assignment": assignment,
                "file_info": canvas_upload,
                "message": f"Assignment '{assignment_name}' created with file attachment"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def add_file_to_module(self, course_id: int, module_id: int, file_info: Dict[str, Any], 
                          item_title: str = None) -> Dict[str, Any]:
        """Add uploaded file to Canvas module"""
        try:
            # Upload file to Canvas
            canvas_upload = self.upload_to_canvas(file_info, course_id, "Module Files")
            
            if not canvas_upload["success"]:
                return canvas_upload
            
            # Add file to module
            title = item_title or file_info["original_name"]
            module_item = self.canvas.add_module_item(
                course_id=course_id,
                module_id=module_id,
                item_type="File",
                content_id=canvas_upload["canvas_file_id"],
                title=title
            )
            
            return {
                "success": True,
                "module_item": module_item,
                "file_info": canvas_upload,
                "message": f"File '{title}' added to module"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def submit_assignment(self, course_id: int, assignment_id: int, file_info: Dict[str, Any], 
                         comment: str = "") -> Dict[str, Any]:
        """Submit assignment with file upload (student)"""
        try:
            # Upload file to Canvas
            canvas_upload = self.upload_to_canvas(file_info, course_id, "Assignment Submissions")
            
            if not canvas_upload["success"]:
                return canvas_upload
            
            # Submit assignment
            submission_url = f"{self.canvas.base_url}/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions"
            
            submission_data = {
                "submission[submission_type]": "online_upload",
                "submission[file_ids][]": canvas_upload["canvas_file_id"]
            }
            
            if comment:
                submission_data["comment[text_comment]"] = comment
            
            response = requests.post(submission_url, headers=self.canvas.headers, data=submission_data)
            response.raise_for_status()
            submission = response.json()
            
            return {
                "success": True,
                "submission": submission,
                "file_info": canvas_upload,
                "message": f"Assignment submitted with file: {file_info['original_name']}"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def cleanup_local_file(self, file_path: str):
        """Clean up local uploaded file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Failed to cleanup file {file_path}: {e}")

# Global file manager instance
file_manager = None

def get_file_manager(canvas: CanvasLMS) -> FileManager:
    """Get or create file manager instance"""
    global file_manager
    if file_manager is None:
        file_manager = FileManager(canvas)
    return file_manager