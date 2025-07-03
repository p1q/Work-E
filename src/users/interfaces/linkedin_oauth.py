import os
import base64
import hashlib
import secrets
import logging
from urllib.parse import urlencode

import requests
from django.conf import settings
from users.infrastructure.models import User

logger = logging.getLogger(__name__)


class LinkedInOAuthService:
    AUTHORIZATION_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    USERINFO_URL = "https://api.linkedin.com/oauth/v2/userinfo"

    @staticmethod
    def generate_pkce_and_state(request):
        state = secrets.token_urlsafe(16)
        code_verifier = base64.urlsafe_b64encode(os.urandom(40)).rstrip(b"=").decode("ascii")
        code_challenge = base64.urlsafe_b64encode(
            hashlib.sha256(code_verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")

        request.session["linkedin_oauth_state"] = state
        request.session["linkedin_code_verifier"] = code_verifier
        return state, code_challenge

    @classmethod
    def build_authorization_url(cls, state, code_challenge, redirect_uri):
        params = {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "state": state,
            "scope": "openid profile email",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{cls.AUTHORIZATION_URL}?{urlencode(params)}"

    @staticmethod
    def validate_state_and_get_verifier(request):
        incoming = request.GET.get("state")
        stored = request.session.get("linkedin_oauth_state")
        verifier = request.session.get("linkedin_code_verifier")

        if incoming != stored or not verifier:
            return None

        request.session.pop("linkedin_oauth_state", None)
        request.session.pop("linkedin_code_verifier", None)
        return verifier

    @classmethod
    def exchange_code_for_token(cls, code, verifier, redirect_uri):
        try:
            resp = requests.post(
                cls.TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": settings.LINKEDIN_CLIENT_ID,
                    "client_secret": settings.LINKEDIN_CLIENT_SECRET,
                    "code_verifier": verifier,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10,
            )
        except requests.RequestException as e:
            logger.error("LinkedIn token exchange failed: %s", e)
            return None

        if not resp.ok:
            logger.warning(
                "LinkedIn token exchange error: status=%s, body=%s",
                resp.status_code,
                resp.text,
            )
            return None

        return resp.json().get("access_token")

    @classmethod
    def fetch_userinfo_via_oidc(cls, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(
            cls.USERINFO_URL,
            headers=headers,
            timeout=10,
        )
        resp.raise_for_status()
        info = resp.json()

        if not info.get("email_verified", False):
            raise ValueError("Email not verified by LinkedIn")

        email = info.get("email")
        if not email:
            raise ValueError("No email returned by LinkedIn OIDC")

        return {
            "email": email,
            "first_name": info.get("localizedFirstName", ""),
            "last_name": info.get("localizedLastName", ""),
            "linkedin_id": info.get("id", ""),
            "avatar_url": info.get("picture", ""),
        }

    @staticmethod
    def get_or_create_user(user_data):
        email = user_data["email"]
        base_username = email.split("@")[0]
        username = base_username

        existing = User.objects.filter(email__iexact=email).first()
        defaults = {
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "avatar_url": user_data["avatar_url"],
            "linkedin_id": user_data["linkedin_id"],
        }

        if User.objects.filter(username__iexact=username).exists():
            import uuid
            suffix = uuid.uuid4().hex[:8]
            username = f"{base_username}-{suffix}"

        if existing:
            existing.username = username
            for field, value in defaults.items():
                setattr(existing, field, value)
            existing.save(update_fields=["username"] + list(defaults.keys()))
            return existing
        else:
            return User.objects.create(
                email=email,
                username=username,
                **defaults
            )
