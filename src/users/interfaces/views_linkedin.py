import logging
import requests
from django.conf import settings
from django.shortcuts import redirect
from django.db import IntegrityError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from .linkedin_oauth import LinkedInOAuthService
from users.infrastructure.models import User

logger = logging.getLogger(__name__)


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
        200: None,
        400: OpenApiResponse(
            description='Authentication failed due to missing/invalid code or error from provider',
            examples=[
                OpenApiExample(
                    name='Missing code',
                    summary='No code or error query param',
                    value={'error': 'auth_failed'},
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
        if request.GET.get("logged_in") == "true":
            return Response({"logged_in": True}, status=status.HTTP_200_OK)

        code = request.GET.get("code")
        error = request.GET.get("error")
        if error or not code:
            return Response({"error": "auth_failed"}, status=status.HTTP_400_BAD_REQUEST)

        base = settings.BACKEND_BASE_URL.rstrip('/')
        redirect_uri = f"{base}/api/users/linkedin/callback/"

        token = LinkedInOAuthService.exchange_code_for_token(code, redirect_uri)
        if not token:
            logger.error("LinkedIn token exchange failed")
            return Response({"error": "token_failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"logged_in": True, "access_token": token}, status=status.HTTP_200_OK)


@extend_schema(
    tags=['Users'],
    request={'application/json': {'access_token': 'string'}},
    responses={
        200: None,
        400: OpenApiResponse(
            description='Access token missing or invalid request format',
            examples=[
                OpenApiExample(
                    name='No token provided',
                    summary='Missing access_token in body',
                    value={'error': 'Access token is required.'},
                    response_only=True
                )
            ]
        ),
        502: OpenApiResponse(
            description='Bad gateway — invalid JSON from LinkedIn',
            examples=[
                OpenApiExample(
                    name='Invalid JSON',
                    summary='LinkedIn returned non‑JSON body',
                    value={'error': 'Invalid JSON from LinkedIn', 'details': '<raw body>'},
                    response_only=True
                )
            ]
        )
    }
)
class LinkedInProfileView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get("access_token")
        if not access_token:
            return Response({"error": "Access token is required."},
                            status=status.HTTP_400_BAD_REQUEST)

        # 1. Запрашиваем профиль у LinkedIn
        headers = {"Authorization": f"Bearer {access_token}"}
        resp = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers, timeout=10)
        try:
            data = resp.json()
        except ValueError:
            return Response(
                {"error": "Invalid JSON from LinkedIn", "details": resp.text},
                status=status.HTTP_502_BAD_GATEWAY
            )
        if resp.status_code != 200:
            return Response(data, status=resp.status_code)

        linkedin_id = data.get("sub")
        email = data.get("email")
        first_name = data.get("given_name", "")
        last_name = data.get("family_name", "")
        avatar = data.get("picture", "")

        # 2. Пытаемся update_or_create только по linkedin_id
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
        except IntegrityError as e:
            # если при создании нового пользователя возник конфликт по username/email,
            # находим существующего по email и дополняем ему linkedin_id
            logger.warning("LinkedIn create failed, merging existing user: %s", e)
            user = User.objects.get(email__iexact=email)
            user.linkedin_id = linkedin_id
            user.first_name = first_name
            user.last_name = last_name
            user.avatar_url = avatar
            user.save(update_fields=['linkedin_id', 'first_name', 'last_name', 'avatar_url'])

        # 3. Возвращаем токен и профиль
        token_obj, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token_obj.key,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'avatar_url': user.avatar_url,
                'linkedin_id': user.linkedin_id,
                'date_joined': user.date_joined,
            }
        }, status=status.HTTP_200_OK)
