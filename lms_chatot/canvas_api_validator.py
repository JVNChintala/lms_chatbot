import requests
from typing import Dict, Any, Optional

class CanvasAPIValidator:
    """Validate Canvas API responses and handle errors consistently"""
    
    @staticmethod
    def validate_response(response: requests.Response, operation: str) -> Dict[str, Any]:
        """Validate Canvas API response and return standardized result"""
        try:
            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "data": data,
                    "operation": operation
                }
            elif response.status_code == 401:
                return {
                    "success": False,
                    "error": "Canvas API authentication failed. Check your token.",
                    "operation": operation
                }
            elif response.status_code == 403:
                return {
                    "success": False,
                    "error": "Canvas API access denied. Check permissions.",
                    "operation": operation
                }
            elif response.status_code == 404:
                return {
                    "success": False,
                    "error": f"Canvas resource not found for {operation}.",
                    "operation": operation
                }
            else:
                return {
                    "success": False,
                    "error": f"Canvas API error {response.status_code}: {response.text}",
                    "operation": operation
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Canvas API validation error: {str(e)}",
                "operation": operation
            }
    
    @staticmethod
    def format_tool_response(result: Dict[str, Any], tool_name: str) -> Dict[str, Any]:
        """Format Canvas API result for tool response"""
        if result["success"]:
            return result["data"]
        else:
            return {
                "error": result["error"],
                "tool": tool_name,
                "suggestion": CanvasAPIValidator._get_error_suggestion(result["error"])
            }
    
    @staticmethod
    def _get_error_suggestion(error: str) -> str:
        """Get helpful suggestion based on error type"""
        if "authentication" in error.lower():
            return "Verify your Canvas API token is correct and active."
        elif "permission" in error.lower() or "access denied" in error.lower():
            return "Check if your Canvas user has the required permissions for this operation."
        elif "not found" in error.lower():
            return "Verify the course ID or resource exists in Canvas."
        else:
            return "Check Canvas API documentation or contact your Canvas administrator."