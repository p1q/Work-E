import logging
from urllib.parse import urlparse

from django.conf import settings
from django.shortcuts import redirect
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from .serializers_google import GoogleAuthSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Users'],
    request=GoogleAuthSerializer,
    responses={
        200: OpenApiResponse(
            description='Successful login via Google',
            examples=[
                OpenApiExample(
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
                    },
                    response_only=True
                )
            ]
        ),
        302: OpenApiResponse(
            description='Redirect to frontend sign-up on cancel or missing token'
        ),
        400: OpenApiResponse(
            description='Invalid or malformed Google ID token',
            examples=[
                OpenApiExample(
                    name='Malformed token',
                    summary='Token is not a valid JWT',
                    value={'detail': 'Invalid Google ID token: Unable to parse'},
                    response_only=True
                ),
                OpenApiExample(
                    name='Audience mismatch',
                    summary='Token audience does not match',
                    value={'detail': 'Token audience mismatch'},
                    response_only=True
                ),
            ]
        )
    },
)
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        error = request.data.get('error')
        id_token_value = request.data.get('id_token')
        if error or not id_token_value:
            # будуємо origin (scheme + netloc) із FRONTEND_URL
            parsed = urlparse(settings.FRONTEND_URL)
            origin = f"{parsed.scheme}://{parsed.netloc}"
            return redirect(f"{origin}/sign-up")

        # 1) Валідація id_token
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2) Логіка створення/отримання користувача
        result = serializer.save()
        user = result['user']
        token = result['token']

        # 3) Повертаємо токен і дані профілю
        return Response({
            'token': token,
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
