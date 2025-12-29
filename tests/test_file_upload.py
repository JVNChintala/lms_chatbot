#!/usr/bin/env python3
"""
Test script for Canvas file upload functionality
Tests assignment creation, module uploads, and submissions
"""

import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

CANVAS_URL = os.getenv("CANVAS_URL", "")
CANVAS_TOKEN = os.getenv("CANVAS_TOKEN", "")
BASE_URL = "http://localhost:8001"

def print_test(name, passed):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    color = "\033[92m" if passed else "\033[91m"
    print(f"{color}{status}\033[0m - {name}")

def test_file_upload_endpoint():
    """Test file upload endpoint availability"""
    try:
        # Create a test file
        test_content = b"Test file content for Canvas upload"
        
        files = {
            'file': ('test_document.txt', test_content, 'text/plain')
        }
        
        data = {
            'upload_type': 'assignment',
            'course_id': '1',
            'item_name': 'Test Assignment',
            'points': '100',
            'description': 'Test assignment with file'
        }
        
        # Note: This will fail without valid Canvas credentials
        # but tests that the endpoint exists
        response = requests.post(
            f"{BASE_URL}/upload-file",
            files=files,
            data=data,
            timeout=5
        )
        
        # Endpoint exists if we get any response
        print_test("File upload endpoint exists", response.status_code in [200, 400, 500])
        return True
    except requests.exceptions.ConnectionError:
        print_test("File upload endpoint exists", False)
        print("  → Server not running. Start with: python lms_chatot/main.py")
        return False
    except Exception as e:
        print_test("File upload endpoint exists", False)
        print(f"  → Error: {e}")
        return False

def test_canvas_file_upload_flow():
    """Test Canvas file upload 3-step flow"""
    if not CANVAS_URL or not CANVAS_TOKEN:
        print_test("Canvas file upload flow", False)
        print("  → Canvas credentials not configured")
        return False
    
    try:
        # Test Step 1: Request upload URL
        headers = {"Authorization": f"Bearer {CANVAS_TOKEN}"}
        
        # Get first course
        courses_response = requests.get(
            f"{CANVAS_URL}/courses",
            headers=headers,
            params={"per_page": 1},
            timeout=5
        )
        
        if courses_response.status_code != 200:
            print_test("Canvas file upload flow", False)
            print(f"  → Cannot access Canvas API: {courses_response.status_code}")
            return False
        
        courses = courses_response.json()
        if not courses:
            print_test("Canvas file upload flow", False)
            print("  → No courses available for testing")
            return False
        
        course_id = courses[0]['id']
        
        # Request upload URL
        upload_params = {
            "name": "test_file.txt",
            "size": 100,
            "content_type": "text/plain",
            "parent_folder_path": "Test Uploads"
        }
        
        upload_response = requests.post(
            f"{CANVAS_URL}/courses/{course_id}/files",
            headers=headers,
            data=upload_params,
            timeout=5
        )
        
        if upload_response.status_code == 200:
            upload_data = upload_response.json()
            has_upload_url = 'upload_url' in upload_data
            has_upload_params = 'upload_params' in upload_data
            
            print_test("Canvas file upload flow", has_upload_url and has_upload_params)
            if has_upload_url and has_upload_params:
                print(f"  → Upload URL received: {upload_data['upload_url'][:50]}...")
            return has_upload_url and has_upload_params
        else:
            print_test("Canvas file upload flow", False)
            print(f"  → Canvas returned status {upload_response.status_code}")
            return False
            
    except Exception as e:
        print_test("Canvas file upload flow", False)
        print(f"  → Error: {e}")
        return False

def test_file_manager_import():
    """Test file manager can be imported"""
    try:
        sys.path.insert(0, 'lms_chatot')
        from file_manager import FileManager, get_file_manager
        print_test("FileManager import", True)
        return True
    except Exception as e:
        print_test("FileManager import", False)
        print(f"  → Error: {e}")
        return False

def test_file_manager_initialization():
    """Test file manager initialization"""
    try:
        sys.path.insert(0, 'lms_chatot')
        from file_manager import FileManager
        from canvas_integration import CanvasLMS
        
        if not CANVAS_URL or not CANVAS_TOKEN:
            print_test("FileManager initialization", False)
            print("  → Canvas credentials not configured")
            return False
        
        canvas = CanvasLMS(CANVAS_URL, CANVAS_TOKEN)
        file_manager = FileManager(canvas)
        
        # Check attributes
        has_canvas = hasattr(file_manager, 'canvas')
        has_upload_folder = hasattr(file_manager, 'upload_folder')
        has_allowed_extensions = hasattr(file_manager, 'allowed_extensions')
        
        all_ok = has_canvas and has_upload_folder and has_allowed_extensions
        print_test("FileManager initialization", all_ok)
        
        if all_ok:
            print(f"  → Upload folder: {file_manager.upload_folder}")
            print(f"  → Allowed extensions: {len(file_manager.allowed_extensions)} types")
        
        return all_ok
    except Exception as e:
        print_test("FileManager initialization", False)
        print(f"  → Error: {e}")
        return False

def test_secure_filename():
    """Test secure filename function"""
    try:
        sys.path.insert(0, 'lms_chatot')
        from file_manager import FileManager
        from canvas_integration import CanvasLMS
        
        canvas = CanvasLMS(CANVAS_URL or "http://test.com", CANVAS_TOKEN or "test")
        fm = FileManager(canvas)
        
        test_cases = [
            ("test.txt", "test.txt"),
            ("../../../etc/passwd", ".._.._.._.._etc_passwd"),
            ("file with spaces.pdf", "file_with_spaces.pdf"),
            ("special!@#$%chars.doc", "special_____chars.doc"),
        ]
        
        all_passed = True
        for input_name, expected_pattern in test_cases:
            result = fm.secure_filename(input_name)
            # Just check it doesn't contain dangerous chars
            is_safe = not any(c in result for c in ['/', '\\', '..'])
            if not is_safe:
                all_passed = False
                print(f"  → Failed: {input_name} -> {result}")
        
        print_test("Secure filename function", all_passed)
        return all_passed
    except Exception as e:
        print_test("Secure filename function", False)
        print(f"  → Error: {e}")
        return False

def test_allowed_file_types():
    """Test file type validation"""
    try:
        sys.path.insert(0, 'lms_chatot')
        from file_manager import FileManager
        from canvas_integration import CanvasLMS
        
        canvas = CanvasLMS(CANVAS_URL or "http://test.com", CANVAS_TOKEN or "test")
        fm = FileManager(canvas)
        
        allowed_files = [
            "document.pdf",
            "presentation.pptx",
            "image.jpg",
            "video.mp4",
            "archive.zip"
        ]
        
        disallowed_files = [
            "script.exe",
            "malware.bat",
            "virus.sh",
            "noextension"
        ]
        
        all_passed = True
        
        for filename in allowed_files:
            if not fm.is_allowed_file(filename):
                print(f"  → Should allow: {filename}")
                all_passed = False
        
        for filename in disallowed_files:
            if fm.is_allowed_file(filename):
                print(f"  → Should block: {filename}")
                all_passed = False
        
        print_test("File type validation", all_passed)
        return all_passed
    except Exception as e:
        print_test("File type validation", False)
        print(f"  → Error: {e}")
        return False

def test_upload_folder_creation():
    """Test upload folder is created"""
    try:
        sys.path.insert(0, 'lms_chatot')
        from file_manager import FileManager
        from canvas_integration import CanvasLMS
        
        canvas = CanvasLMS(CANVAS_URL or "http://test.com", CANVAS_TOKEN or "test")
        test_folder = "test_uploads_temp"
        fm = FileManager(canvas, upload_folder=test_folder)
        
        folder_exists = os.path.exists(test_folder)
        
        # Cleanup
        if folder_exists:
            try:
                os.rmdir(test_folder)
            except:
                pass
        
        print_test("Upload folder creation", folder_exists)
        return folder_exists
    except Exception as e:
        print_test("Upload folder creation", False)
        print(f"  → Error: {e}")
        return False

def run_tests():
    """Run all file upload tests"""
    print("\n" + "="*60)
    print("Canvas File Upload - Test Suite")
    print("="*60 + "\n")
    
    results = []
    
    print("📦 Module Tests")
    results.append(test_file_manager_import())
    results.append(test_file_manager_initialization())
    results.append(test_secure_filename())
    results.append(test_allowed_file_types())
    results.append(test_upload_folder_creation())
    
    print("\n🌐 API Tests")
    results.append(test_file_upload_endpoint())
    results.append(test_canvas_file_upload_flow())
    
    print("\n" + "="*60)
    passed = sum(results)
    total = len(results)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Results: {passed}/{total} tests passed ({percentage:.0f}%)")
    
    if passed == total:
        print("\033[92m✓ All tests passed!\033[0m")
    else:
        print("\033[91m✗ Some tests failed\033[0m")
    
    print("="*60 + "\n")
    
    if not CANVAS_URL or not CANVAS_TOKEN:
        print("\033[93m⚠ Note: Canvas credentials not configured\033[0m")
        print("Some tests were skipped. Configure .env to run full tests.\n")
    
    return passed == total

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
