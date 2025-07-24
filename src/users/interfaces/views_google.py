import logging

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from .serializers_google import GoogleAuthSerializer
from users.service import fetch_google_userinfo
from users.infrastructure.models import User
from rest_framework.authtoken.models import Token

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Users'],
    request=GoogleAuthSerializer,
    responses={
        200: OpenApiResponse(
            response={
                'type': 'object',
                'properties': {
                    'token': {'type': 'string'},
                    'user': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'email': {'type': 'string', 'format': 'email'},
                            'username': {'type': 'string'},
                            'first_name': {'type': 'string'},
                            'last_name': {'type': 'string'},
                            'avatar_url': {'type': 'string', 'format': 'uri'},
                            'date_joined': {'type': 'string', 'format': 'date-time'}
                        }
                    }
                }
            },
            description='Successful login via Google',
            examples=[OpenApiExample(
                name='Приклад успішної відповіді',
                summary='Успішний вхід через Google',
                value={
                    "token": "abc123def456",
                    "user": {
                        "id": 42,
                        "email": "user@example.com",
                        "username": "user42",
                        "first_name": "John",
                        "last_name": "Doe",
                        "avatar_url": "https://lh3.googleusercontent.com/.../photo.jpg",
                        "date_joined": "2025-07-01T14:30:00Z"
                    }
                }
            )]
        ),
        400: OpenApiResponse(
            description='Missing or invalid Google access token',
            examples=[
                OpenApiExample(
                    name='No token',
                    summary='Access token не передано',
                    value={'detail': 'Access token is required.'},
                    response_only=True
                ),
                OpenApiExample(
                    name='Invalid token',
                    summary='Token is invalid or expired',
                    value={'detail': 'Google userinfo error: 401 ...'},
                    response_only=True
                ),
            ]
        )
    },
)
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

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
