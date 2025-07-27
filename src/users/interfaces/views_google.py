import logging

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from users.infrastructure.models import User
from users.service import fetch_google_userinfo

from src.schemas.users import (GOOGLE_LOGIN_REQUEST, GOOGLE_LOGIN_RESPONSE_SUCCESS, GOOGLE_LOGIN_RESPONSE_ERROR, )

logger = logging.getLogger(__name__)


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=GOOGLE_LOGIN_REQUEST,
        responses={
            200: GOOGLE_LOGIN_RESPONSE_SUCCESS,
            400: GOOGLE_LOGIN_RESPONSE_ERROR,
        },
        description='Аутентифікація користувача через Google OAuth2 токен.',
        summary='Вхід через Google'
    )
    def post(self, request):
        # 1) Отримуємо access_token з тіла запиту
        access_token = request.data.get('access_token')
        if not access_token:
            return Response(
                {"detail": "Access token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        # 2) Отримуємо дані користувача через Google UserInfo API
        try:
            user_info = fetch_google_userinfo(access_token)
        except ValueError as e:
            logger.warning("Google userinfo failed: %s", e)
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        # 3) Створюємо або оновлюємо користувача в базі
        user, _ = User.objects.update_or_create(
            email=user_info['email'],
            defaults={
                'username': user_info['email'].split('@')[0],
                'first_name': user_info.get('given_name', ''),
                'last_name': user_info.get('family_name', ''),
                'google_id': user_info.get('sub', ''),
                'avatar_url': user_info.get('picture', ''),
            }
        )
        # 4) Отримуємо токен для нашої системи
        token, _ = Token.objects.get_or_create(user=user)
        # 5) Повертаємо токен і дані користувача
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'avatar_url': user.avatar_url,
                'date_joined': user.date_joined,
            }
        }, status=status.HTTP_200_OK)
