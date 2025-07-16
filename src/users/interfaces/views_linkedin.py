import logging
import requests
from urllib.parse import urlparse
from django.conf import settings
from django.shortcuts import redirect
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from shared.auth.service import AuthService
from users.infrastructure.models import User
from users.interfaces.serializers import UserSerializer
from .linkedin_oauth import LinkedInOAuthService

logger = logging.getLogger(__name__)


def get_frontend_origin(request):
    origin = request.headers.get("Origin")
    if origin:
        return origin.rstrip("/")
    referer = request.headers.get("Referer")
    if referer:
        parsed = urlparse(referer)
        return f"{parsed.scheme}://{parsed.netloc}"
    return request.build_absolute_uri("/").rstrip("/")


@extend_schema(tags=['Users'], responses={302: None})
class LinkedInLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logger.debug("LinkedInLoginView GET request received")

        origin = get_frontend_origin(request)
        request.session['oauth_frontend_origin'] = origin

        state, _ = LinkedInOAuthService.generate_pkce_and_state(request)
        logger.debug(f"Generated state for OAuth: {state}")

        base = settings.BACKEND_BASE_URL.rstrip('/')
        redirect_uri = f"{base}/api/users/linkedin/callback/"
        authorization_url = LinkedInOAuthService.build_authorization_url(state=state, redirect_uri=redirect_uri)

        logger.debug(f"Redirecting to LinkedIn OAuth URL: {authorization_url}")

        response = redirect(authorization_url)
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.items())}")
        return response


@extend_schema(
    tags=['Users'],
    responses={
        302: OpenApiResponse(description="Redirect after successful LinkedIn OAuth"),
        400: OpenApiResponse(description="OAuth failed", examples=[
            OpenApiExample(name='Missing code', summary='User cancelled', value={}, response_only=True)]),
        500: OpenApiResponse(description='Token exchange failed', examples=[
            OpenApiExample(name='Exchange error', summary='Token endpoint error', value={'error': 'token_failed'},
                           response_only=True)])
    }
)
class LinkedInCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logger.debug("LinkedInCallbackView GET request received")

        frontend = request.session.pop('oauth_frontend_origin', None) or get_frontend_origin(request)
        params = request.GET.dict()

        logger.debug(f"Frontend origin: {frontend}")
        logger.debug(f"Query parameters: {params}")

        if params.get("logged_in") == "true":
            logger.debug("User already logged in, redirecting to frontend root")
            response = redirect(f"{frontend}/")
            return response

        code = params.get("code")
        error = params.get("error")
        if error or not code:
            logger.warning(f"OAuth failed or missing code: error={error}")
            response = redirect(f"{frontend}/sign-up")
            return response

        base = settings.BACKEND_BASE_URL.rstrip('/')
        redirect_uri = f"{base}/api/users/linkedin/callback/"

        logger.debug(f"Exchanging code at {redirect_uri}")

        access_token = LinkedInOAuthService.exchange_code_for_token(code, redirect_uri)
        if not access_token:
            logger.error("Failed to exchange code for access token")
            response = redirect(f"{frontend}/login?error=token_failed")
            return response

        logger.debug("Access token obtained, making API request to LinkedIn")

        linkedin_resp = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10
        )

        try:
            profile = linkedin_resp.json()
        except ValueError:
            logger.error("Failed to parse LinkedIn user info response: invalid JSON")
            response = redirect(f"{frontend}/login?error=invalid_profile")
            return response

        logger.debug(f"LinkedIn profile data received: {profile}")

        if linkedin_resp.status_code != 200:
            logger.error(
                f"Error fetching user profile from LinkedIn: status={linkedin_resp.status_code}, message={linkedin_resp.text}")
            response = redirect(f"{frontend}/login?error=profile_failed")
            return response

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
            logger.debug(f"User {'created' if created else 'updated'}: {user.email}")
        except Exception as e:
            logger.warning(f"Failed to create or update user: {e}, merging with existing user")
            user = User.objects.get(email__iexact=email)
            user.linkedin_id = linkedin_id
            user.first_name = first_name
            user.last_name = last_name
            user.avatar_url = avatar
            user.save(update_fields=['linkedin_id', 'first_name', 'last_name', 'avatar_url'])

        tokens = AuthService.create_jwt_for_user(user)
        response = redirect(f"{frontend}/linkedin/callback")
        AuthService.attach_jwt_cookies(response, tokens)

        logger.debug("JWT cookies set on response")
        logger.debug(f"Response status: {response.status_code}")
        logger.debug(f"Response headers: {dict(response.items())}")
        logger.debug(f"Response cookies: {dict(response.cookies)}")
        return response


@extend_schema(tags=["Users"], responses={200: UserSerializer})
class LinkedInProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user or request.user.is_anonymous:
            return Response({"detail": "Unauthorized"}, status=401)
        return Response(UserSerializer(request.user).data)
