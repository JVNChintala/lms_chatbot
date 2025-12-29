# File Upload Feature - Documentation

## Overview
The Canvas LMS Chatbot supports file uploads for various Canvas operations including assignment creation, module content, and assignment submissions.

## Supported Operations

### 1. Assignment Creation with File
Upload a file and create a Canvas assignment with the file attached as reference material.

**Use Case**: Teacher uploads assignment instructions (PDF, DOCX) and creates the assignment.

**API Endpoint**: `POST /upload-file`

**Parameters**:
- `file`: File to upload (multipart/form-data)
- `upload_type`: "assignment"
- `course_id`: Canvas course ID
- `item_name`: Assignment name
- `points`: Points possible (default: 100)
- `description`: Assignment description (optional)

**Example**:
```bash
curl -X POST http://localhost:8001/upload-file \
  -F "file=@assignment_instructions.pdf" \
  -F "upload_type=assignment" \
  -F "course_id=123" \
  -F "item_name=Week 1 Assignment" \
  -F "points=100" \
  -F "description=Complete the exercises in the attached PDF"
```

**Response**:
```json
{
  "success": true,
  "assignment": {
    "id": 456,
    "name": "Week 1 Assignment",
    "points_possible": 100
  },
  "file_info": {
    "canvas_file_id": 789,
    "canvas_file_url": "https://canvas.com/files/789",
    "display_name": "assignment_instructions.pdf"
  },
  "message": "Assignment 'Week 1 Assignment' created with file attachment"
}
```

### 2. Add File to Module
Upload a file and add it to an existing Canvas module.

**Use Case**: Teacher uploads lecture notes, slides, or resources to a course module.

**Parameters**:
- `file`: File to upload
- `upload_type`: "module"
- `course_id`: Canvas course ID
- `module_id`: Canvas module ID
- `item_name`: Display name for the file in module

**Example**:
```bash
curl -X POST http://localhost:8001/upload-file \
  -F "file=@lecture_slides.pptx" \
  -F "upload_type=module" \
  -F "course_id=123" \
  -F "module_id=45" \
  -F "item_name=Week 1 Lecture Slides"
```

**Response**:
```json
{
  "success": true,
  "module_item": {
    "id": 678,
    "title": "Week 1 Lecture Slides",
    "type": "File"
  },
  "file_info": {
    "canvas_file_id": 789,
    "display_name": "lecture_slides.pptx"
  },
  "message": "File 'Week 1 Lecture Slides' added to module"
}
```

### 3. Assignment Submission
Upload a file as an assignment submission (student).

**Use Case**: Student submits completed assignment work.

**Parameters**:
- `file`: File to upload
- `upload_type`: "submission"
- `course_id`: Canvas course ID
- `assignment_id`: Canvas assignment ID
- `comment`: Submission comment (optional)

**Example**:
```bash
curl -X POST http://localhost:8001/upload-file \
  -F "file=@my_homework.pdf" \
  -F "upload_type=submission" \
  -F "course_id=123" \
  -F "assignment_id=456" \
  -F "comment=Completed all exercises"
```

**Response**:
```json
{
  "success": true,
  "submission": {
    "id": 890,
    "assignment_id": 456,
    "submitted_at": "2024-01-15T10:30:00Z"
  },
  "file_info": {
    "canvas_file_id": 789,
    "display_name": "my_homework.pdf"
  },
  "message": "Assignment submitted with file: my_homework.pdf"
}
```

## Supported File Types

### Documents
- PDF (.pdf)
- Microsoft Word (.doc, .docx)
- Text files (.txt, .rtf)
- OpenDocument (.odt)

### Presentations
- PowerPoint (.ppt, .pptx)
- OpenDocument Presentation (.odp)

### Spreadsheets
- Excel (.xls, .xlsx)
- CSV (.csv)
- OpenDocument Spreadsheet (.ods)

### Images
- PNG (.png)
- JPEG (.jpg, .jpeg)
- GIF (.gif)
- BMP (.bmp)
- SVG (.svg)

### Videos
- MP4 (.mp4)
- AVI (.avi)
- MOV (.mov)
- WMV (.wmv)
- WebM (.webm)
- FLV (.flv)

### Audio
- MP3 (.mp3)
- WAV (.wav)
- OGG (.ogg)
- AAC (.aac)
- M4A (.m4a)

### Archives
- ZIP (.zip)
- RAR (.rar)
- 7-Zip (.7z)
- TAR (.tar, .gz)

## File Size Limits
- Maximum file size: **100 MB**
- Files exceeding this limit will be rejected

## Canvas Upload Process

The file upload follows Canvas API's 3-step process:

### Step 1: Request Upload URL
```python
POST /api/v1/courses/{course_id}/files
{
  "name": "filename.pdf",
  "size": 12345,
  "content_type": "application/pdf",
  "parent_folder_path": "Uploaded Files"
}
```

### Step 2: Upload File
```python
POST {upload_url}
# Multipart form data with file and upload_params
```

### Step 3: Confirm Upload
```python
# Canvas returns file info via Location header or response body
```

## Frontend Integration

### Vue.js File Upload Widget

The dashboard includes a file upload widget accessible to teachers and admins:

```javascript
// Upload file
async uploadFile() {
  const formData = new FormData();
  formData.append('file', this.selectedFile);
  formData.append('upload_type', this.uploadType);
  formData.append('course_id', this.uploadCourseId);
  formData.append('item_name', this.uploadItemName);
  
  const response = await fetch('/upload-file', {
    method: 'POST',
    body: formData
  });
  
  const result = await response.json();
  // Handle result
}
```

### Widget Features
- File selection with type validation
- Upload type selection (assignment/module/submission)
- Course and item configuration
- Progress indication
- Success/error feedback
- Auto-cleanup after upload

## Security Features

### 1. Filename Sanitization
All uploaded filenames are sanitized to prevent path traversal attacks:
```python
def secure_filename(filename: str) -> str:
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    # Keep only safe characters
    safe_chars = set('abcdefghijklmnopqrstuvwxyz...0123456789.-_')
    return ''.join(c if c in safe_chars else '_' for c in filename)
```

### 2. File Type Validation
Only allowed file extensions are accepted:
```python
def is_allowed_file(filename: str) -> bool:
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions
```

### 3. File Size Validation
Files exceeding 100MB are rejected before processing.

### 4. Temporary Storage
Files are stored temporarily and cleaned up after Canvas upload:
```python
def cleanup_local_file(file_path: str):
    if os.path.exists(file_path):
        os.remove(file_path)
```

### 5. Unique Filenames
Each uploaded file gets a unique identifier to prevent conflicts:
```python
unique_id = str(uuid.uuid4())[:8]
final_filename = f"{unique_id}_{secure_name}"
```

## Error Handling

### Common Errors

**File Type Not Allowed**
```json
{
  "success": false,
  "error": "File type not allowed"
}
```

**File Too Large**
```json
{
  "success": false,
  "error": "File too large (max 100MB)"
}
```

**Canvas Upload Failed**
```json
{
  "success": false,
  "error": "Canvas upload failed: [details]"
}
```

**Missing Required Parameters**
```json
{
  "success": false,
  "error": "Module ID required for module upload"
}
```

**Canvas Not Configured**
```json
{
  "success": false,
  "error": "Canvas not configured"
}
```

## Testing

### Run File Upload Tests
```bash
python test_file_upload.py
```

### Manual Testing

1. **Start the application**:
   ```bash
   python lms_chatot/main.py
   ```

2. **Access dashboard**:
   ```
   http://localhost:8001
   ```

3. **Login as teacher/admin**

4. **Navigate to AI Assistant**

5. **Click "Upload Files" button**

6. **Select file and configure upload**

7. **Click "Upload to Canvas"**

8. **Verify success message**

### Test with cURL

**Assignment Creation**:
```bash
curl -X POST http://localhost:8001/upload-file \
  -F "file=@test.pdf" \
  -F "upload_type=assignment" \
  -F "course_id=1" \
  -F "item_name=Test Assignment" \
  -F "points=100"
```

**Module Upload**:
```bash
curl -X POST http://localhost:8001/upload-file \
  -F "file=@slides.pptx" \
  -F "upload_type=module" \
  -F "course_id=1" \
  -F "module_id=1" \
  -F "item_name=Lecture Slides"
```

**Assignment Submission**:
```bash
curl -X POST http://localhost:8001/upload-file \
  -F "file=@homework.pdf" \
  -F "upload_type=submission" \
  -F "course_id=1" \
  -F "assignment_id=1" \
  -F "comment=Completed"
```

## Troubleshooting

### Upload Fails Immediately
- Check Canvas credentials in `.env`
- Verify Canvas API token has file upload permissions
- Ensure course/module/assignment IDs are valid

### File Not Appearing in Canvas
- Check Canvas folder permissions
- Verify file was uploaded (check Canvas Files)
- Check module item was created (check Canvas Modules)

### Large Files Fail
- Ensure file is under 100MB
- Check Canvas instance file size limits
- Consider compressing large files

### Permission Errors
- Verify user role has upload permissions
- Check Canvas API token permissions
- Ensure course enrollment is active

## Best Practices

1. **File Naming**: Use descriptive, clear filenames
2. **File Size**: Compress large files before upload
3. **File Types**: Use standard formats (PDF, DOCX, MP4)
4. **Organization**: Use appropriate folders in Canvas
5. **Cleanup**: System auto-cleans temporary files
6. **Testing**: Test uploads in a test course first
7. **Validation**: Always check upload success before proceeding

## API Reference

### FileManager Class

```python
class FileManager:
    def __init__(self, canvas: CanvasLMS, upload_folder: str = "uploads")
    
    def save_uploaded_file(self, file_data: bytes, filename: str) -> Dict
    def upload_to_canvas(self, file_info: Dict, course_id: int, folder_name: str) -> Dict
    def create_assignment_with_file(self, course_id: int, assignment_name: str, 
                                   file_info: Dict, points: int, description: str) -> Dict
    def add_file_to_module(self, course_id: int, module_id: int, 
                          file_info: Dict, item_title: str) -> Dict
    def submit_assignment(self, course_id: int, assignment_id: int, 
                         file_info: Dict, comment: str) -> Dict
    def cleanup_local_file(self, file_path: str)
```

## Future Enhancements

- [ ] Batch file uploads
- [ ] Drag-and-drop interface
- [ ] Upload progress tracking
- [ ] File preview before upload
- [ ] Direct Canvas folder selection
- [ ] File versioning support
- [ ] Automatic file conversion
- [ ] Cloud storage integration (S3, Google Drive)
- [ ] File scanning for malware
- [ ] Thumbnail generation for images/videos

## Support

For issues or questions:
1. Check error messages in response
2. Review Canvas API logs
3. Test with smaller files
4. Verify Canvas permissions
5. Check `test_file_upload.py` results
6. Create GitHub issue with details

---

**Last Updated**: 2024
**Version**: 2.0.0
**Status**: ✅ Production Ready
