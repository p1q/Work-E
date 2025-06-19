from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


class AuthService:
    @staticmethod
    def create_jwt_for_user(user):
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }

    @staticmethod
    def attach_jwt_cookies(response, tokens):
        response.set_cookie(
            "access_token",
            tokens["access"],
            secure=True,
            httponly=True,
            samesite="Strict",
            max_age=settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds(),
        )

        response.set_cookie(
            "refresh_token",
            tokens["refresh"],
            secure=True,
            httponly=True,
            samesite="Strict",
            max_age=settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds(),
        )

    @staticmethod
    def clear_jwt_cookies(response):
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
