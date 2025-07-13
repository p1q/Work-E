import logging

import requests
from django.conf import settings
from django.shortcuts import redirect
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from shared.auth.service import AuthService
from users.infrastructure.models import User

from .linkedin_oauth import LinkedInOAuthService

logger = logging.getLogger(__name__)


def get_frontend_origin(request):
    origin = request.headers.get("Origin")
    if origin:
        return origin.rstrip("/")

    referer = request.headers.get("Referer")
    if referer:
        from urllib.parse import urlparse
        parsed = urlparse(referer)
        return f"{parsed.scheme}://{parsed.netloc}"
    return request.build_absolute_uri("/").rstrip("/")


@extend_schema(
    tags=['Users'],
    responses={302: None}
)
class LinkedInLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        state, _ = LinkedInOAuthService.generate_pkce_and_state(request)
        base = settings.BACKEND_BASE_URL.rstrip('/')
        redirect_uri = f"{base}/api/users/linkedin/callback/"
        authorization_url = LinkedInOAuthService.build_authorization_url(
            state=state,
            redirect_uri=redirect_uri
        )
        return redirect(authorization_url)


@extend_schema(
    tags=['Users'],
    responses={
        302: OpenApiResponse(
            description="Redirects to frontend on successful LinkedIn OAuth authentication"
        ),
        400: OpenApiResponse(
            description='Authentication failed due to missing/invalid code or error from provider',
            examples=[
                OpenApiExample(
                    name='Missing code',
                    summary='User cancelled login',
                    value={},
                    response_only=True,
                ),
            ]
        ),
        500: OpenApiResponse(
            description='LinkedIn token exchange failed on server side',
            examples=[
                OpenApiExample(
                    name='Exchange error',
                    summary='Token endpoint returned error',
                    value={'error': 'token_failed'},
                    response_only=True
                )
            ]
        )
    }
)
class LinkedInCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        frontend = get_frontend_origin(request)

        if request.GET.get("logged_in") == "true":
            return redirect(f"{frontend}/")

        code = request.GET.get("code")
        error = request.GET.get("error")
        if error or not code:
            return redirect(f"{frontend}/sign-up")

        base = settings.BACKEND_BASE_URL.rstrip('/')
        redirect_uri = f"{base}/api/users/linkedin/callback/"
        access_token = LinkedInOAuthService.exchange_code_for_token(code, redirect_uri)
        if not access_token:
            logger.error("LinkedIn token exchange failed")
            return redirect(f"{frontend}/login?error=token_failed")

        headers = {"Authorization": f"Bearer {access_token}"}
        linkedin_resp = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers=headers,
            timeout=10
        )
        try:
            profile = linkedin_resp.json()
        except ValueError:
            logger.error("Invalid JSON from LinkedIn userinfo")
            return redirect(f"{frontend}/login?error=invalid_profile")
        if linkedin_resp.status_code != 200:
            logger.error("LinkedIn userinfo error: %s", profile)
            return redirect(f"{frontend}/login?error=profile_failed")

        linkedin_id = profile.get("sub")
        email = profile.get("email")
        first_name = profile.get("given_name", "")
        last_name = profile.get("family_name", "")
        avatar = profile.get("picture", "")

        defaults = {
            'email': email,
            'username': email.split('@')[0],
            'first_name': first_name,
            'last_name': last_name,
            'avatar_url': avatar,
        }
        try:
            user, created = User.objects.update_or_create(
                linkedin_id=linkedin_id,
                defaults=defaults
            )
        except Exception as e:
            logger.warning("LinkedIn create failed, merging existing user: %s", e)
            user = User.objects.get(email__iexact=email)
            user.linkedin_id = linkedin_id
            user.first_name = first_name
            user.last_name = last_name
            user.avatar_url = avatar
            user.save(update_fields=['linkedin_id', 'first_name', 'last_name', 'avatar_url'])

        tokens = AuthService.create_jwt_for_user(user)
        response = redirect(f"{frontend}/")
        AuthService.attach_jwt_cookies(response, tokens)
        return response
