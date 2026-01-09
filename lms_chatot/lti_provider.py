import base64
import hmac
import hashlib
import logging
import time
import os
from typing import Dict, Optional
from urllib.parse import quote
from fastapi import Request, HTTPException
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


class LTIProvider:
    """
    Canvas-compatible LTI 1.1 Tool Provider
    """

    def __init__(self, consumer_key: str = None, consumer_secret: str = None):
        self.consumer_key = consumer_key or os.getenv("LTI_CONSUMER_KEY")
        self.consumer_secret = consumer_secret or os.getenv("LTI_CONSUMER_SECRET")

        if not self.consumer_key or not self.consumer_secret:
            raise RuntimeError("LTI_CONSUMER_KEY and LTI_CONSUMER_SECRET are required")

        self.nonce_cache = {}
        self.nonce_ttl = 300

    # ---------- PUBLIC API ----------

    def verify_launch(self, request: Request, form_data: Dict) -> Dict:
        self._validate_required_params(form_data)
        self._verify_oauth(request, form_data)
        
        # Debug: Log all LTI payload keys
        logger.info("[LTI_PROVIDER] === LTI PAYLOAD DEBUG ===")
        logger.info(f"[LTI_PROVIDER] All keys received: {sorted(form_data.keys())}")
        
        # Log role-related fields
        role_fields = {k: v for k, v in form_data.items() if 'role' in k.lower()}
        logger.info(f"[LTI_PROVIDER] Role fields: {role_fields}")
        
        # Log user-related fields
        user_fields = {k: v for k, v in form_data.items() if 'user' in k.lower() or 'person' in k.lower()}
        logger.info(f"[LTI_PROVIDER] User fields: {user_fields}")
        
        # Log custom fields
        custom_fields = {k: v for k, v in form_data.items() if k.startswith('custom_')}
        logger.info(f"[LTI_PROVIDER] Custom fields: {custom_fields}")
        
        # Log context fields
        context_fields = {k: v for k, v in form_data.items() if 'context' in k.lower()}
        logger.info(f"[LTI_PROVIDER] Context fields: {context_fields}")
        logger.info("[LTI_PROVIDER] === END PAYLOAD DEBUG ===")

        return {
            "canvas_user_id": form_data.get("custom_canvas_user_id"),
            "user_id": form_data.get("user_id"),
            "login_id": form_data.get("custom_canvas_user_login_id"),
            "name": form_data.get("lis_person_name_full"),
            "first_name": form_data.get("lis_person_name_given"),
            "last_name": form_data.get("lis_person_name_family"),
            "email": form_data.get("lis_person_contact_email_primary"),
            "avatar": form_data.get("user_image"),
            "roles": form_data.get("roles", "").lower(),
            "context_roles": form_data.get("custom_canvas_course_role", form_data.get("ext_roles", "")).lower(),
            "ext_roles": form_data.get("ext_roles", "").lower(),
        }

    # ---------- OAUTH ----------

    def _verify_oauth(self, request: Request, params: Dict):
        if params.get("oauth_consumer_key") != self.consumer_key:
            raise HTTPException(401, "Invalid consumer key")

        self._check_nonce(params.get("oauth_nonce"), params.get("oauth_timestamp"))

        base_string = self._build_base_string(request, params)
        expected = self._sign(base_string)
        received = params.get("oauth_signature")

        if not hmac.compare_digest(received, expected):
            raise HTTPException(401, "OAuth signature mismatch")

    def _build_base_string(self, request: Request, params: Dict) -> str:
        method = request.method.upper()

        scheme = request.headers.get("x-forwarded-proto", request.url.scheme)
        host = request.headers.get("host")
        base_url = f"{scheme}://{host}{request.url.path}"

        normalized = [
            (k, str(v))
            for k, v in params.items()
            if k != "oauth_signature"
        ]

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

        if data["oauth_signature_method"] != "HMAC-SHA1":
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
        self.nonce_cache = {
            k: v for k, v in self.nonce_cache.items()
            if now - v < self.nonce_ttl
        }

    # ---------- HELPERS ----------

    def _enc(self, s: str) -> str:
        return quote(str(s), safe="-._~")

    def map_to_user_role(self, roles: str) -> str:
        r = roles.lower()
        logger.info(f"[LTI_PROVIDER] Mapping roles: '{roles}' (lowercase: '{r}')")
        
        if "instructor" in r or "teacher" in r or "teachingenrollment" in r:
            logger.info(f"[LTI_PROVIDER] Detected teacher role")
            return "teacher"
        if "administrator" in r or "admin" in r or "accountadmin" in r:
            logger.info(f"[LTI_PROVIDER] Detected admin role")
            return "admin"
        
        print(f"[LTI_PROVIDER] Defaulting to student role")
        return "student"
