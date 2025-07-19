import logging

import requests
from urllib.parse import urlparse

from django.conf import settings
from django.shortcuts import redirect

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

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


@extend_schema(
    tags=['Users'],
    responses={302: None}
)
class LinkedInLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        origin = get_frontend_origin(request)
        request.session['oauth_frontend_origin'] = origin

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
        200: OpenApiResponse(
            description="Возвращает JSON с access и refresh токенами"
        ),
        400: OpenApiResponse(
            description="OAuth failed",
            examples=[
                OpenApiExample(
                    name='Missing code',
                    summary='User cancelled login',
                    value={},
                    response_only=True,
                )
            ],
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
            ],
        )
    }
)
class LinkedInCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Проверяем код/ошибку
        error = request.GET.get("error")
        code = request.GET.get("code")
        if error or not code:
            return Response({'detail': 'OAuth failed or cancelled'}, status=status.HTTP_400_BAD_REQUEST)

        # Меняем код на LinkedIn access token
        base = settings.BACKEND_BASE_URL.rstrip('/')
        redirect_uri = f"{base}/api/users/linkedin/callback/"
        linkedin_token = LinkedInOAuthService.exchange_code_for_token(code, redirect_uri)
        if not linkedin_token:
            logger.error("LinkedIn token exchange failed")
            return Response({'error': 'token_failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Получаем профиль LinkedIn
        resp = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {linkedin_token}"},
            timeout=10
        )
        if resp.status_code != 200:
            logger.error("LinkedIn userinfo error: %s", resp.text)
            return Response({'error': 'profile_failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        profile = resp.json()
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

        # Генерируем JWT
        tokens = AuthService.create_jwt_for_user(user)

@extend_schema(
    tags=["Users"],
    responses={200: UserSerializer}
)
class LinkedInProfileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user or request.user.is_anonymous:
            return Response({"detail": "Unauthorized"}, status=401)

        return Response(UserSerializer(request.user).data)
