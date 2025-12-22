import os
import uuid
import mimetypes
import requests
from typing import Dict, Any
from canvas_integration import CanvasLMS

class FileManager:
    """Handle file uploads and Canvas integration"""
    
    def __init__(self, canvas: CanvasLMS, upload_folder: str = "uploads"):
        self.canvas = canvas
        self.upload_folder = upload_folder
        self.allowed_extensions = {
            'png', 'jpg', 'jpeg', 'gif', 'bmp', 'svg',
            'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',
            'ppt', 'pptx', 'odp', 'xls', 'xlsx', 'ods', 'csv',
            'mp4', 'avi', 'mov', 'wmv', 'flv', 'webm',
            'mp3', 'wav', 'ogg', 'aac', 'm4a',
            'zip', 'rar', '7z', 'tar', 'gz'
        }
        self.max_file_size = 100 * 1024 * 1024  # 100MB
        os.makedirs(upload_folder, exist_ok=True)
    
    def secure_filename(self, filename: str) -> str:
        """Make filename safe for filesystem"""
        # Remove path components
        filename = filename.split('/')[-1].split('\\')[-1]
        # Keep only alphanumeric, dots, dashes, underscores
        safe_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_')
        return ''.join(c if c in safe_chars else '_' for c in filename)
    
    def is_allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        if '.' not in filename:
            return False
        ext = filename.rsplit('.', 1)[1].lower()
        return ext in self.allowed_extensions
    
    def save_uploaded_file(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """Save uploaded file locally"""
        try:
            if not self.is_allowed_file(filename):
                return {"success": False, "error": "File type not allowed"}
            
            if len(file_data) > self.max_file_size:
                return {"success": False, "error": "File too large (max 100MB)"}
            
            secure_name = self.secure_filename(filename)
            unique_id = str(uuid.uuid4())[:8]
            final_filename = f"{unique_id}_{secure_name}"
            file_path = os.path.join(self.upload_folder, final_filename)
            
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            return {
                "success": True,
                "filename": final_filename,
                "original_name": filename,
                "file_path": file_path,
                "file_size": len(file_data),
                "mime_type": mimetypes.guess_type(filename)[0] or 'application/octet-stream'
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def upload_to_canvas(self, file_info: Dict[str, Any], course_id: int, folder_name: str = "Uploaded Files") -> Dict[str, Any]:
        """Upload file to Canvas using proper 3-step process"""
        try:
            # Step 1: Tell Canvas about the file
            upload_url = f"{self.canvas.base_url}/api/v1/courses/{course_id}/files"
            upload_params = {
                "name": file_info["original_name"],
                "size": file_info["file_size"],
                "content_type": file_info["mime_type"],
                "parent_folder_path": folder_name
            }
            
            response = requests.post(upload_url, headers=self.canvas.headers, data=upload_params)
            response.raise_for_status()
            upload_data = response.json()
            
            # Step 2: Upload file to Canvas storage
            with open(file_info["file_path"], 'rb') as f:
                files = {'file': (file_info["original_name"], f, file_info["mime_type"])}
                upload_response = requests.post(
                    upload_data['upload_url'],
                    data=upload_data['upload_params'],
                    files=files
                )
                upload_response.raise_for_status()
            
            # Step 3: Get file info from location header or response
            if upload_response.status_code == 201:
                canvas_file = upload_response.json()
            elif 'Location' in upload_response.headers:
                confirm_url = upload_response.headers['Location']
                confirm_response = requests.get(confirm_url, headers=self.canvas.headers)
                confirm_response.raise_for_status()
                canvas_file = confirm_response.json()
            else:
                canvas_file = upload_response.json()
            
            return {
                "success": True,
                "canvas_file_id": canvas_file.get("id"),
                "canvas_file_url": canvas_file.get("url"),
                "display_name": canvas_file.get("display_name", file_info["original_name"])
            }
        except Exception as e:
            return {"success": False, "error": f"Canvas upload failed: {str(e)}"}
    
    def create_assignment_with_file(self, course_id: int, assignment_name: str, file_info: Dict[str, Any], 
                                  points: int = 100, description: str = "") -> Dict[str, Any]:
        """Create Canvas assignment with uploaded file"""
        try:
            canvas_upload = self.upload_to_canvas(file_info, course_id, "Assignment Files")
            if not canvas_upload["success"]:
                return canvas_upload
            
            assignment_desc = f"{description}\n\n<p><strong>Assignment File:</strong> "
            assignment_desc += f'<a href="{canvas_upload["canvas_file_url"]}">{canvas_upload["display_name"]}</a></p>'
            
            assignment_data = {
                "name": assignment_name,
                "points_possible": points,
                "description": assignment_desc,
                "submission_types": ["online_upload"],
                "published": True
            }
            
            assignment = self.canvas.create_assignment(course_id, assignment_data)
            
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
            canvas_upload = self.upload_to_canvas(file_info, course_id, "Module Files")
            if not canvas_upload["success"]:
                return canvas_upload
            
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
        """Submit assignment with file upload"""
        try:
            canvas_upload = self.upload_to_canvas(file_info, course_id, "Assignment Submissions")
            if not canvas_upload["success"]:
                return canvas_upload
            
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

_file_manager = None

def get_file_manager(canvas: CanvasLMS) -> FileManager:
    """Get or create file manager instance"""
    global _file_manager
    if _file_manager is None:
        _file_manager = FileManager(canvas)
    return _file_manager