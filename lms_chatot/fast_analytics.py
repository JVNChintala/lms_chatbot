import os
from fastapi import APIRouter
from analytics_cache import analytics_cache
from canvas_integration import CanvasLMS

router = APIRouter()

@router.get("/fast-analytics")
async def get_fast_analytics(user_role: str, canvas_user_id: int = None):
    """Lightweight analytics endpoint for chat integration"""
    try:
        canvas_url = os.getenv("CANVAS_URL", "")
        canvas_token = os.getenv("CANVAS_TOKEN", "")
        
        if not canvas_url or not canvas_token:
            return {"analytics": {"error": "Canvas not configured"}}
        
        # Check cache first
        cached = analytics_cache.get_cached_analytics(user_role, canvas_user_id)
        if cached:
            return {"analytics": cached, "cached": True}
        
        # Generate fresh analytics
        canvas = CanvasLMS(canvas_url, canvas_token, as_user_id=canvas_user_id if user_role != "admin" else None)
        analytics = analytics_cache.get_quick_analytics(canvas, user_role)
        
        # Cache the result
        analytics_cache.cache_analytics(user_role, analytics, canvas_user_id)
        
        return {"analytics": analytics, "cached": False}
        
    except Exception as e:
        return {"analytics": {"error": str(e)}}

@router.post("/clear-analytics-cache")
async def clear_analytics_cache():
    """Clear analytics cache for fresh data"""
    analytics_cache.cache = {}
    return {"success": True, "message": "Analytics cache cleared"}