import os
import base64
import hashlib
import secrets
from urllib.parse import urlencode

import requests
from django.conf import settings
from users.infrastructure.models import User
from .views_auth import AuthService


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
    def build_authorization_url(cls, state, code_challenge):
        params = {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
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
        return verifier

    @classmethod
    def exchange_code_for_token(cls, code, verifier):
        resp = requests.post(
            cls.TOKEN_URL,
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET,
                "code_verifier": verifier,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if not resp.ok:
            return None
        return resp.json().get("access_token")

    @classmethod
    def fetch_userinfo_via_oidc(cls, access_token):
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get(cls.USERINFO_URL, headers=headers)
        resp.raise_for_status()
        info = resp.json()

        email = (
                info.get("email")
                or info.get("email_verified")
                or (info.get("emails") and info["emails"][0])
        )
        if not email:
            raise ValueError("Email not returned by LinkedIn OIDC")

        return {
            "email": email,
            "first_name": info.get("localizedFirstName", ""),
            "last_name": info.get("localizedLastName", ""),
            "linkedin_id": info.get("id", ""),
            "avatar_url": info.get("picture", ""),
        }

    @staticmethod
    def get_or_create_user(user_data):
        return User.objects.update_or_create(
            email=user_data["email"],
            defaults={
                "username": user_data["email"].split("@")[0],
                "first_name": user_data["first_name"],
                "last_name": user_data["last_name"],
                "avatar_url": user_data["avatar_url"],
                "linkedin_id": user_data["linkedin_id"],
            },
        )[0]

    @staticmethod
    def cleanup_session(request):
        request.session.pop("linkedin_oauth_state", None)
        request.session.pop("linkedin_code_verifier", None)
