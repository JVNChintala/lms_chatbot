import os
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
from dotenv import load_dotenv
from lti_provider import LTIProvider
from session_manager import session_manager
from auth import create_demo_token

load_dotenv()

router = APIRouter(prefix="/lti", tags=["LTI"])

# Initialize LTI provider
LTI_CONSUMER_KEY = os.getenv("LTI_CONSUMER_KEY", "canvas_lms_key")
LTI_CONSUMER_SECRET = os.getenv("LTI_CONSUMER_SECRET", "canvas_lms_secret")
lti_provider = LTIProvider(LTI_CONSUMER_KEY, LTI_CONSUMER_SECRET)

# Store LTI sessions for grade passback
lti_sessions = {}

@router.post("/launch")
async def lti_launch(
    request: Request,
    lti_message_type: str = Form(...),
    lti_version: str = Form(...),
    resource_link_id: str = Form(...),
    user_id: Optional[str] = Form(None),
    roles: Optional[str] = Form(None),
    lis_person_name_full: Optional[str] = Form(None),
    lis_person_contact_email_primary: Optional[str] = Form(None),
    context_id: Optional[str] = Form(None),
    context_title: Optional[str] = Form(None),
    lis_outcome_service_url: Optional[str] = Form(None),
    lis_result_sourcedid: Optional[str] = Form(None),
    oauth_consumer_key: Optional[str] = Form(None),
    oauth_signature_method: Optional[str] = Form(None),
    oauth_timestamp: Optional[str] = Form(None),
    oauth_nonce: Optional[str] = Form(None),
    oauth_version: Optional[str] = Form(None),
    oauth_signature: Optional[str] = Form(None),
):
    """LTI 1.1 Launch endpoint - receives LTI launch requests from LMS"""
    
    try:
        # Collect all form data
        form_data = await request.form()
        form_dict = dict(form_data)
        
        # Verify OAuth signature and extract params
        lti_params = lti_provider.verify_launch(request, form_dict)
        
        # Map LTI role to internal role - use context roles, ignore system roles
        context_roles = lti_params.get('context_roles', '')
        user_role = lti_provider.map_to_user_role(context_roles if context_roles else lti_params['roles'])
        
        # Get Canvas user ID - try custom param first, then lookup via Canvas API
        canvas_user_id = lti_params.get('canvas_user_id')
        
        if not canvas_user_id:
            # Lookup Canvas user by login_id (LTI user_id)
            from canvas_integration import CanvasLMS
            canvas_url = os.getenv('CANVAS_URL', '')
            canvas_token = os.getenv('CANVAS_TOKEN', '')
            
            if canvas_url and canvas_token:
                try:
                    canvas = CanvasLMS(canvas_url, canvas_token)
                    # Search for user by login_id
                    import requests
                    search_url = f"{canvas_url.rstrip('/').replace('/api/v1', '')}/api/v1/accounts/self/users"
                    params = {'search_term': lti_params.get('login_id') or lti_params['user_id']}
                    headers = {'Authorization': f'Bearer {canvas_token}'}
                    response = requests.get(search_url, params=params, headers=headers, timeout=5)
                    
                    if response.ok:
                        users = response.json()
                        if users:
                            canvas_user_id = users[0]['id']
                            print(f"[LTI_ROUTES] Found Canvas user_id={canvas_user_id} for LTI user={lti_params['user_id']}")
                except Exception as e:
                    print(f"[LTI_ROUTES] Failed to lookup Canvas user: {e}")
        
        # Fallback to LTI user_id if still not found (will have limited functionality)
        if not canvas_user_id:
            canvas_user_id = lti_params['user_id']
            print(f"[LTI_ROUTES] WARNING: Using LTI user_id as canvas_user_id. Canvas API calls may fail.")
        
        print(f"[LTI_ROUTES] Final: canvas_user_id={canvas_user_id}, role={user_role}")
        
        # Create session
        session_id = session_manager.create_session(
            user_role=user_role,
            canvas_user_id=canvas_user_id,
            username=lti_params['name'] or lti_params['user_id']
        )
        
        # Store LTI session for grade passback
        lti_sessions[session_id] = {
            'user_id': lti_params['user_id'],
            'resource_link_id': form_dict.get('resource_link_id'),
            'context_id': form_dict.get('context_id'),
            'outcome_service_url': form_dict.get('lis_outcome_service_url'),
            'result_sourcedid': form_dict.get('lis_result_sourcedid'),
            'user_name': lti_params['name'],
            'user_email': lti_params['email'],
        }
        
        # Create JWT token
        token = create_demo_token(lti_params['user_id'], user_role)
        
        # Store in session for dashboard
        session_manager.update_session(
            session_id,
            role=user_role,
            user_token=token,
            username=lti_params['name'] or lti_params['user_id']
        )
        
        # Escape username for JavaScript
        username = (lti_params.get('name') or lti_params['user_id']).replace("'", "&#39;")
        
        # Return HTML that sets localStorage and redirects to chat only
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LTI Launch</title>
        </head>
        <body>
            <script>
                localStorage.setItem('canvas_user_id', '{canvas_user_id}');
                localStorage.setItem('canvas_token', '{token}');
                localStorage.setItem('canvas_role', '{user_role}');
                localStorage.setItem('canvas_username', '{username}');
                localStorage.setItem('lti_session_id', '{session_id}');
                localStorage.setItem('lti_mode', 'true');
                window.location.href = '/canvas-embed?user_id={canvas_user_id}&role={user_role}&username=' + encodeURIComponent('{username}');
            </script>
            <p>Launching Canvas LMS Assistant...</p>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LTI launch failed: {str(e)}")


@router.post("/grade")
async def send_grade(
    session_id: str = Form(...),
    score: float = Form(...),
):
    """Send grade back to LMS via LTI Outcomes service"""
    
    if session_id not in lti_sessions:
        raise HTTPException(404, "LTI session not found")
    
    lti_session = lti_sessions[session_id]
    
    if not lti_session['outcome_service_url'] or not lti_session['result_sourcedid']:
        raise HTTPException(400, "Grade passback not supported for this launch")
    
    # Validate score (0.0 to 1.0)
    if not 0.0 <= score <= 1.0:
        raise HTTPException(400, "Score must be between 0.0 and 1.0")
    
    # Send grade
    success = lti_provider.send_grade(
        lti_session['outcome_service_url'],
        lti_session['result_sourcedid'],
        score
    )
    
    if success:
        return {"success": True, "message": "Grade sent successfully"}
    else:
        raise HTTPException(500, "Failed to send grade to LMS")


@router.get("/config.xml")
async def lti_config():
    """LTI Tool Configuration XML for easy installation in Canvas"""
    
    base_url = os.getenv("APP_BASE_URL", "http://localhost:8001")
    
    xml_config = f"""<?xml version="1.0" encoding="UTF-8"?>
<cartridge_basiclti_link xmlns="http://www.imsglobal.org/xsd/imslticc_v1p0"
    xmlns:blti="http://www.imsglobal.org/xsd/imsbasiclti_v1p0"
    xmlns:lticm="http://www.imsglobal.org/xsd/imslticm_v1p0"
    xmlns:lticp="http://www.imsglobal.org/xsd/imslticp_v1p0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xsi:schemaLocation="http://www.imsglobal.org/xsd/imslticc_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticc_v1p0.xsd
    http://www.imsglobal.org/xsd/imsbasiclti_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imsbasiclti_v1p0p1.xsd
    http://www.imsglobal.org/xsd/imslticm_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticm_v1p0.xsd
    http://www.imsglobal.org/xsd/imslticp_v1p0 http://www.imsglobal.org/xsd/lti/ltiv1p0/imslticp_v1p0.xsd">
    <blti:title>Canvas LMS AI Assistant</blti:title>
    <blti:description>AI-powered assistant for Canvas LMS with GPT-4</blti:description>
    <blti:launch_url>{base_url}/lti/launch</blti:launch_url>
    <blti:extensions platform="canvas.instructure.com">
        <lticm:property name="privacy_level">public</lticm:property>
        <lticm:property name="domain">{base_url.replace('http://', '').replace('https://', '')}</lticm:property>
    </blti:extensions>
</cartridge_basiclti_link>"""
    
    return HTMLResponse(content=xml_config, media_type="application/xml")
