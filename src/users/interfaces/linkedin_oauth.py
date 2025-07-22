import logging
import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

class LinkedInOAuthService:
    AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"

    @staticmethod
    def generate_pkce_and_state(request):
        state = secrets.token_urlsafe(16)
        request.session["linkedin_oauth_state"] = state
        return state, None

    @classmethod
    def build_authorization_url(cls, state, redirect_uri):
        params = {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "openid email profile",
        }
        auth_url = f"{cls.AUTHORIZATION_URL}?{urlencode(params)}"
        return auth_url

    @staticmethod
    def validate_state_and_get_verifier(request):
        incoming = request.GET.get("state")
        stored = request.session.get("linkedin_oauth_state")

        if incoming != stored:
            return None

        request.session.pop("linkedin_oauth_state", None)
        return None

    @classmethod
    def exchange_code_for_token(cls, code, redirect_uri):
        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET
        }
        try:
            resp = requests.post(
                cls.TOKEN_URL,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
        except requests.RequestException as e:
            logger.error("LinkedIn token exchange failed (exception): %s", e)
            return None

        if not resp.ok:
            logger.error(
                "LinkedIn token exchange failed: status=%s, body=%s",
                resp.status_code,
                resp.text
            )
            return None

        data = resp.json()
        return data.get("access_token")
