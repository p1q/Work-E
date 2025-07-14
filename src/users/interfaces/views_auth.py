from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.utils import extend_schema, OpenApiExample
from shared.auth.service import AuthService


@extend_schema(
    tags=["Auth"],
    summary="Отримання access/refresh токенів (логін)",
    request={
        "type": "object",
        "properties": {
            "email": {"type": "string", "example": "user@example.com"},
            "password": {"type": "string", "example": "userpassword"},
        },
        "required": ["email", "password"],
    },
    responses={
        200: {
            "type": "object",
            "properties": {
                "access": {"type": "string"},
                "refresh": {"type": "string"},
            },
            "example": {
                "access": "eyJ0eXAiOiJKV1QiLCJh...",
                "refresh": "eyJhbGciOiJIUzI1NiIsInR...",
            },
        },
        401: OpenApiExample(
            name="Unauthorized",
            value={"detail": "No active account found with the given credentials"},
        ),
    },
)
class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]


@extend_schema(
    tags=["Auth"],
    summary="Оновлення access-токена по refresh-токену",
    request={
        "type": "object",
        "properties": {
            "refresh": {"type": "string", "example": "eyJhbGciOiJIUzI1NiIsInR..."}
        },
        "required": ["refresh"],
    },
    responses={
        200: {
            "type": "object",
            "properties": {
                "access": {"type": "string"},
                "refresh": {"type": "string"},
            },
            "example": {
                "access": "eyJ0eXAiOiJKV1QiLCJh...",
                "refresh": "eyJhbGciOiJIUzI1NiIsInR...",
            },
        },
        401: OpenApiExample(
            name="Invalid token",
            value={"detail": "Token is invalid or expired"},
        ),
    },
)
class CustomTokenRefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


@extend_schema(
    tags=["Auth"],
    summary="Вихід користувача (видаляє токени та куки)",
    responses={
        200: {
            "type": "object",
            "properties": {"detail": {"type": "string"}},
            "example": {"detail": "Logout successful"},
        }
    },
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass

        resp = Response({"detail": "Logout successful"}, status=status.HTTP_200_OK)
        AuthService.clear_jwt_cookies(resp)
        return resp
