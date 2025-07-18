import os
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
        common = {
            "secure": True,
            "httponly": True,
            "samesite": "None",
        }

        cookie_domain = os.getenv("COOKIE_DOMAIN")
        if cookie_domain:
            common["domain"] = cookie_domain

        response.set_cookie(
            "access_token",
            tokens["access"],
            max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
            **common
        )

        response.set_cookie(
            "refresh_token",
            tokens["refresh"],
            max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
            **common
        )

    @staticmethod
    def clear_jwt_cookies(response):
        domain = os.getenv("COOKIE_DOMAIN")
        response.delete_cookie("access_token", domain=domain)
        response.delete_cookie("refresh_token", domain=domain)
