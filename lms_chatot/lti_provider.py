import hmac
import hashlib
import base64
import time
import os
from typing import Dict, Optional
from urllib.parse import quote, urlparse
from fastapi import Request, HTTPException
import xml.etree.ElementTree as ET
from dotenv import load_dotenv

load_dotenv()

class LTIProvider:
    """
    Canvas-compatible LTI 1.1 Tool Provider
    """

    def __init__(self, consumer_key: str = None, consumer_secret: str = None):
        self.consumer_key = consumer_key or os.getenv("LTI_CONSUMER_KEY")
        self.consumer_secret = consumer_secret or os.getenv("LTI_CONSUMER_SECRET")

        if not self.consumer_key or not self.consumer_secret:
            raise RuntimeError("LTI_CONSUMER_KEY and LTI_CONSUMER_SECRET are required for Canvas LTI 1.1")

        self.nonce_cache = {}
        self.nonce_ttl = 300  # 5 minutes

    # ---------- PUBLIC API ----------

    def verify_launch(self, request: Request, form_data: Dict) -> Dict:
        print("LTI PAYLOAD:", sorted(form_data.keys()))
        self._validate_required_params(form_data)
        self._verify_oauth(request, form_data)

        return {
            "user_id": form_data.get("user_id"),
            "name": form_data.get("lis_person_name_full"),
            "email": form_data.get("lis_person_contact_email_primary"),
            "roles": form_data.get("roles", "").lower(),
            "context_id": form_data.get("context_id"),
            "context_title": form_data.get("context_title"),
            "resource_link_id": form_data.get("resource_link_id"),
            "outcome_service_url": form_data.get("lis_outcome_service_url"),
            "result_sourcedid": form_data.get("lis_result_sourcedid"),
        }

    # ---------- OAUTH ----------

    def _verify_oauth(self, request: Request, params: Dict):
        if params.get("oauth_consumer_key") != self.consumer_key:
            raise HTTPException(401, "Invalid consumer key")

        self._check_nonce(params.get("oauth_nonce"), params.get("oauth_timestamp"))

        base_string = self._build_base_string(request, params)
        expected = self._sign(base_string)

        received = params.get("oauth_signature")

        print("BASE STRING:", base_string)
        print("EXPECTED:", expected)
        print("RECEIVED:", received)

        if not hmac.compare_digest(received, expected):
            raise HTTPException(401, "OAuth signature mismatch")

    def _build_base_string(self, request: Request, params: Dict) -> str:
        method = request.method.upper()

        # IMPORTANT: use url_for-like reconstruction
        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.headers.get("host")

        base_url = f"{scheme}://{host}{request.url.path}"

        # Flatten params & remove signature
        normalized = []
        for k, v in params.items():
            if k == "oauth_signature":
                continue
            if isinstance(v, list):
                for item in v:
                    normalized.append((k, str(item)))
            else:
                normalized.append((k, str(v)))

        normalized.sort(key=lambda x: (x[0], x[1]))

        param_str = "&".join(
            f"{self._enc(k)}={self._enc(v)}" for k, v in normalized
        )

        return "&".join([
            method,
            self._enc(base_url),
            self._enc(param_str),
        ])


    def _sign(self, base_string: str) -> str:
        key = f"{self._enc(self.consumer_secret)}&"
        raw = hmac.new(key.encode(), base_string.encode(), hashlib.sha1).digest()
        return base64.b64encode(raw).decode()

    # ---------- VALIDATION ----------

    def _validate_required_params(self, data: Dict):
        required = [
            "lti_message_type",
            "lti_version",
            "resource_link_id",
            "oauth_consumer_key",
            "oauth_signature",
            "oauth_timestamp",
            "oauth_nonce",
            "oauth_signature_method",
        ]

        missing = [k for k in required if k not in data]
        if missing:
            raise HTTPException(400, f"Missing LTI parameters: {missing}")

        if data["lti_message_type"] != "basic-lti-launch-request":
            raise HTTPException(400, "Invalid LTI message type")
        
        if data.get("oauth_signature_method") != "HMAC-SHA1":
            raise HTTPException(401, "Unsupported OAuth signature method")

    def _check_nonce(self, nonce: Optional[str], timestamp: Optional[str]):
        if not nonce or not timestamp:
            raise HTTPException(401, "Missing OAuth nonce or timestamp")

        ts = int(timestamp)
        now = int(time.time())

        if abs(now - ts) > 300:
            raise HTTPException(401, "Expired OAuth timestamp")

        if nonce in self.nonce_cache:
            raise HTTPException(401, "Replay detected")

        self.nonce_cache[nonce] = now
        self.nonce_cache = {k: v for k, v in self.nonce_cache.items() if now - v < self.nonce_ttl}

    # ---------- HELPERS ----------

    def _enc(self, s: str) -> str:
        return quote(str(s), safe="-._~")
    
    def map_to_user_role(self, roles: str) -> str:
        """Map LTI roles to internal roles"""
        roles_lower = roles.lower()
        if 'instructor' in roles_lower or 'teacher' in roles_lower:
            return 'teacher'
        elif 'administrator' in roles_lower:
            return 'admin'
        else:
            return 'student'
