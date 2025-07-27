from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (TokenObtainPairView, TokenRefreshView, )
from shared.auth.service import AuthService
from src.schemas.token import (TOKEN_OBTAIN_REQUEST, TOKEN_OBTAIN_RESPONSE, TOKEN_OBTAIN_RESPONSE_UNAUTHORIZED,
                               TOKEN_REFRESH_REQUEST, TOKEN_REFRESH_RESPONSE, TOKEN_REFRESH_RESPONSE_INVALID,
                               LOGOUT_RESPONSE, )
from drf_spectacular.utils import extend_schema, OpenApiRequest


class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=OpenApiRequest(TOKEN_OBTAIN_REQUEST),
        responses={
            200: TOKEN_OBTAIN_RESPONSE,
            401: TOKEN_OBTAIN_RESPONSE_UNAUTHORIZED,
        },
        description='Отримати пару JWT токенів (access та refresh).',
        summary='Отримати JWT токени'
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=OpenApiRequest(TOKEN_REFRESH_REQUEST),
        responses={
            200: TOKEN_REFRESH_RESPONSE,
            401: TOKEN_REFRESH_RESPONSE_INVALID,
        },
        description='Оновити JWT access токен за допомогою refresh токена.',
        summary='Оновити JWT access токен'
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: LOGOUT_RESPONSE},
        description='Вихід користувача - refresh токен у чорний список.',
        summary='Вихід користувача'
    )
    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass

        resp = Response({"detail": "Вихід успішний"}, status=status.HTTP_200_OK)
        AuthService.clear_jwt_cookies(resp)
        return resp
