#!/usr/bin/env python3
"""
Verification script for Canvas LMS Chatbot
Tests all critical components after cleanup
"""

import os
import sys
from dotenv import load_dotenv

# Color codes for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
RESET = '\033[0m'

def print_status(message, status):
    """Print colored status message"""
    color = GREEN if status else RED
    symbol = "✓" if status else "✗"
    print(f"{color}{symbol}{RESET} {message}")

def print_section(title):
    """Print section header"""
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}{title}{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")

def check_environment():
    """Check environment variables"""
    print_section("Environment Configuration")
    
    load_dotenv()
    
    required_vars = {
        'OPENAI_API_KEY': 'OpenAI API Key',
        'CANVAS_URL': 'Canvas URL',
        'CANVAS_TOKEN': 'Canvas Token',        
    }
    
    all_present = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked = value[:10] + '...' if len(value) > 10 else value
            print_status(f"{description}: {masked}", True)
        else:
            print_status(f"{description}: Missing", False)
            all_present = False
    
    return all_present

def check_dependencies():
    """Check required Python packages"""
    print_section("Dependencies")
    
    required_packages = [
        'fastapi',
        'uvicorn',
        'openai',
        'requests',
        'python-dotenv',
        'python-jose',
        'passlib'
    ]
    
    all_installed = True
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print_status(f"{package}", True)
        except ImportError:
            print_status(f"{package}", False)
            all_installed = False
    
    return all_installed

def check_files():
    """Check critical files exist"""
    print_section("Critical Files")
    
    critical_files = [
        'lms_chatot/main.py',
        'lms_chatot/canvas_agent.py',
        'lms_chatot/canvas_integration.py',
        'lms_chatot/canvas_tools.py',
        'lms_chatot/intent_classifier.py',
        'lms_chatot/analytics_cache.py',
        'lms_chatot/inference_systems/openai_inference.py',
        'lms_chatot/templates/vue_dashboard.html',
        'lms_chatot/templates/canvas_login.html',
        'requirements.txt',
        '.env.example'
    ]
    
    all_exist = True
    for file_path in critical_files:
        exists = os.path.exists(file_path)
        print_status(f"{file_path}", exists)
        if not exists:
            all_exist = False
    
    return all_exist

def check_imports():
    """Check if main modules can be imported"""
    print_section("Module Imports")
    
    sys.path.insert(0, 'lms_chatot')
    
    modules = [
        ('canvas_integration', 'CanvasLMS'),
        ('canvas_agent', 'CanvasAgent'),
        ('canvas_tools', 'CanvasTools'),
        ('intent_classifier', 'IntentClassifier'),
        ('analytics_cache', 'analytics_cache'),
        ('inference_systems.openai_inference', 'OpenAIInference')
    ]
    
    all_imported = True
    for module_name, class_name in modules:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
            print_status(f"{module_name}.{class_name}", True)
        except Exception as e:
            print_status(f"{module_name}.{class_name}: {str(e)}", False)
            all_imported = False
    
    return all_imported

def check_openai_connection():
    """Test OpenAI API connection"""
    print_section("OpenAI Connection")
    
    try:
        from openai import OpenAI
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key:
            print_status("OpenAI API Key not configured", False)
            return False
        
        client = OpenAI(api_key=api_key)
        print_status("OpenAI client initialized", True)
        
        # Test with a simple request
        try:
            response = client.responses.create(
                model="gpt-4o-mini",
                input="Hi",
                max_output_tokens=16
            )
            print_status("OpenAI API connection successful", True)
            return True
        except Exception as e:
            print_status(f"OpenAI API test failed: {str(e)}", False)
            return False
            
    except Exception as e:
        print_status(f"OpenAI setup failed: {str(e)}", False)
        return False

def check_canvas_connection():
    """Test Canvas API connection"""
    print_section("Canvas Connection")
    
    try:
        import requests
        
        canvas_url = os.getenv('CANVAS_URL')
        canvas_token = os.getenv('CANVAS_TOKEN')
        
        if not canvas_url or not canvas_token:
            print_status("Canvas credentials not configured", False)
            return False
        
        # Test Canvas API
        headers = {"Authorization": f"Bearer {canvas_token}"}
        response = requests.get(f"{canvas_url}/courses", headers=headers, timeout=5)
        
        if response.status_code == 200:
            print_status("Canvas API connection successful", True)
            return True
        else:
            print_status(f"Canvas API returned status {response.status_code}", False)
            return False
            
    except Exception as e:
        print_status(f"Canvas connection failed: {str(e)}", False)
        return False

def check_database():
    """Check database files"""
    print_section("Database Files")
    
    db_files = [
        'lms_chatot/conversations.db',
        'lms_chatot/usage_tracker.db'
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            size = os.path.getsize(db_file)
            print_status(f"{db_file} ({size} bytes)", True)
        else:
            print_status(f"{db_file} (will be created on first run)", True)
    
    return True

def run_verification():
    """Run all verification checks"""
    print(f"\n{YELLOW}{'='*60}{RESET}")
    print(f"{YELLOW}Canvas LMS Chatbot - System Verification{RESET}")
    print(f"{YELLOW}{'='*60}{RESET}")
    
    results = {
        'Environment': check_environment(),
        'Dependencies': check_dependencies(),
        'Files': check_files(),
        'Imports': check_imports(),
        'Database': check_database(),
        'OpenAI': check_openai_connection(),
        'Canvas': check_canvas_connection()
    }
    
    print_section("Verification Summary")
    
    all_passed = True
    for check, passed in results.items():
        print_status(f"{check} Check", passed)
        if not passed:
            all_passed = False
    
    print(f"\n{YELLOW}{'='*60}{RESET}")
    if all_passed:
        print(f"{GREEN}✓ All checks passed! System is ready.{RESET}")
        print(f"\nTo start the application:")
        print(f"  cd lms_chatbot")
        print(f"  python main.py")
        print(f"\nThen open: http://localhost:8001")
    else:
        print(f"{RED}✗ Some checks failed. Please fix the issues above.{RESET}")
        print(f"\nCommon fixes:")
        print(f"  - Install dependencies: pip install -r requirements.txt")
        print(f"  - Configure .env file with your credentials")
        print(f"  - Ensure Canvas URL and token are valid")
        print(f"  - Verify OpenAI API key is active")
    print(f"{YELLOW}{'='*60}{RESET}\n")
    
    return all_passed

if __name__ == '__main__':
    success = run_verification()
    sys.exit(0 if success else 1)
