import hmac
import hashlib
import time
from typing import Dict, Optional
from urllib.parse import quote, urlencode
from fastapi import Request, HTTPException
import xml.etree.ElementTree as ET

class LTIProvider:
    """Minimal LTI 1.1 Tool Provider with OAuth1 signature verification"""
    
    def __init__(self, consumer_key: str, consumer_secret: str):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.nonce_cache = {}  # In production, use Redis
        self.nonce_ttl = 300  # 5 minutes
    
    def verify_launch(self, request: Request, form_data: Dict) -> Dict:
        """Verify OAuth1 signature and extract LTI params"""
        # 1. Check required LTI params
        required = ['lti_message_type', 'lti_version', 'resource_link_id']
        if not all(k in form_data for k in required):
            raise HTTPException(400, "Missing required LTI parameters")
        
        if form_data.get('lti_message_type') != 'basic-lti-launch-request':
            raise HTTPException(400, "Invalid LTI message type")
        
        # 2. Verify OAuth signature
        if not self._verify_oauth_signature(request, form_data):
            raise HTTPException(401, "Invalid OAuth signature")
        
        # 3. Check replay attack (nonce + timestamp)
        if not self._check_nonce(form_data.get('oauth_nonce'), form_data.get('oauth_timestamp')):
            raise HTTPException(401, "Replay attack detected or expired request")
        
        # 4. Extract user info
        return {
            'user_id': form_data.get('user_id'),
            'lis_person_name_full': form_data.get('lis_person_name_full'),
            'lis_person_contact_email_primary': form_data.get('lis_person_contact_email_primary'),
            'roles': form_data.get('roles', '').lower(),
            'context_id': form_data.get('context_id'),
            'context_title': form_data.get('context_title'),
            'resource_link_id': form_data.get('resource_link_id'),
            'lis_outcome_service_url': form_data.get('lis_outcome_service_url'),
            'lis_result_sourcedid': form_data.get('lis_result_sourcedid'),
        }
    
    def _verify_oauth_signature(self, request: Request, params: Dict) -> bool:
        """Verify OAuth 1.0 signature"""
        oauth_signature = params.get('oauth_signature')
        if not oauth_signature:
            return False
        
        # Build base string
        method = request.method.upper()
        
        # Normalize URL: remove query params, ensure lowercase scheme/host, remove default ports
        url = str(request.url)
        base_url = url.split('?')[0]
        
        # Ensure consistent scheme (Canvas expects exact match)
        if base_url.startswith('http://'):
            base_url = base_url.replace(':80/', '/', 1) if ':80/' in base_url else base_url
        elif base_url.startswith('https://'):
            base_url = base_url.replace(':443/', '/', 1) if ':443/' in base_url else base_url
        
        # Collect all params except signature (including query params if any)
        normalized_params = {k: v for k, v in params.items() if k != 'oauth_signature'}
        
        # Sort and encode per OAuth spec
        sorted_params = sorted(normalized_params.items())
        param_string = '&'.join(f"{self._percent_encode(str(k))}={self._percent_encode(str(v))}" 
                               for k, v in sorted_params)
        
        # Create signature base string
        base_string = f"{method}&{self._percent_encode(base_url)}&{self._percent_encode(param_string)}"
        
        # Sign with HMAC-SHA1 (key is consumer_secret&token_secret, token_secret is empty for LTI)
        key = f"{self._percent_encode(self.consumer_secret)}&"
        signature = hmac.new(key.encode('utf-8'), base_string.encode('utf-8'), hashlib.sha1).digest()
        import base64
        expected_signature = base64.b64encode(signature).decode()
        
        # Debug logging (remove in production)
        if oauth_signature != expected_signature:
            print(f"Signature mismatch:")
            print(f"  Base URL: {base_url}")
            print(f"  Params: {sorted_params[:3]}...")  # First 3 params
            print(f"  Expected: {expected_signature}")
            print(f"  Received: {oauth_signature}")
        
        return hmac.compare_digest(oauth_signature, expected_signature)
    
    def _percent_encode(self, s: str) -> str:
        """OAuth percent encoding: encode everything except unreserved chars"""
        return quote(s, safe='~')
    
    def _check_nonce(self, nonce: Optional[str], timestamp: Optional[str]) -> bool:
        """Prevent replay attacks using nonce and timestamp"""
        if not nonce or not timestamp:
            return False
        
        try:
            ts = int(timestamp)
            current_time = int(time.time())
            
            # Check timestamp is within acceptable window (Canvas uses 90 seconds)
            if abs(current_time - ts) > 90:
                print(f"Timestamp outside window: {abs(current_time - ts)}s difference")
                return False
            
            # Check nonce hasn't been used
            if nonce in self.nonce_cache:
                return False
            
            # Store nonce with expiry
            self.nonce_cache[nonce] = current_time
            
            # Cleanup old nonces
            self.nonce_cache = {k: v for k, v in self.nonce_cache.items() 
                               if current_time - v < self.nonce_ttl}
            
            return True
        except (ValueError, TypeError):
            return False
    
    def map_to_user_role(self, roles: str) -> str:
        """Map LTI roles to internal roles"""
        roles_lower = roles.lower()
        if 'instructor' in roles_lower or 'teacher' in roles_lower:
            return 'teacher'
        elif 'administrator' in roles_lower:
            return 'admin'
        else:
            return 'student'
    
    def send_grade(self, service_url: str, sourcedid: str, score: float) -> bool:
        """Send grade back to LMS via LTI Outcomes service"""
        if not service_url or not sourcedid:
            return False
        
        # Build XML request
        message_id = f"grade_{int(time.time())}"
        xml_body = f"""<?xml version="1.0" encoding="UTF-8"?>
<imsx_POXEnvelopeRequest xmlns="http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0">
  <imsx_POXHeader>
    <imsx_POXRequestHeaderInfo>
      <imsx_version>V1.0</imsx_version>
      <imsx_messageIdentifier>{message_id}</imsx_messageIdentifier>
    </imsx_POXRequestHeaderInfo>
  </imsx_POXHeader>
  <imsx_POXBody>
    <replaceResultRequest>
      <resultRecord>
        <sourcedGUID>
          <sourcedId>{sourcedid}</sourcedId>
        </sourcedGUID>
        <result>
          <resultScore>
            <language>en</language>
            <textString>{score:.2f}</textString>
          </resultScore>
        </result>
      </resultRecord>
    </replaceResultRequest>
  </imsx_POXBody>
</imsx_POXEnvelopeRequest>"""
        
        # Sign and send OAuth request
        import requests
        from requests_oauthlib import OAuth1
        
        auth = OAuth1(
            self.consumer_key,
            self.consumer_secret,
            signature_type='auth_header'
        )
        
        headers = {'Content-Type': 'application/xml'}
        
        try:
            response = requests.post(service_url, data=xml_body, auth=auth, headers=headers, timeout=10)
            
            # Parse response
            root = ET.fromstring(response.content)
            ns = {'ims': 'http://www.imsglobal.org/services/ltiv1p1/xsd/imsoms_v1p0'}
            status = root.find('.//ims:imsx_codeMajor', ns)
            
            return status is not None and status.text == 'success'
        except Exception as e:
            print(f"Grade passback failed: {e}")
            return False
