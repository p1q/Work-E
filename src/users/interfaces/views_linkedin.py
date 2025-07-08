import logging
from urllib.parse import urlparse

import requests
from django.shortcuts import redirect
from django.views import View
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .linkedin_oauth import LinkedInOAuthService

logger = logging.getLogger(__name__)


class FrontendBaseURLMixin:
    def _get_frontend_base_url(self, request):
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if not origin:
            scheme = "https" if request.is_secure() else "http"
            origin = f"{scheme}://{request.get_host()}"
        parsed = urlparse(origin)
        return f"{parsed.scheme}://{parsed.netloc}"


class LinkedInLoginView(FrontendBaseURLMixin, View):
    permission_classes = [AllowAny]

    def get(self, request):
        frontend_base_url = self._get_frontend_base_url(request)

        state, _ = LinkedInOAuthService.generate_pkce_and_state(request)
        redirect_uri = f"{frontend_base_url}/api/users/linkedin/callback/"
        request.session["linkedin_redirect_uri"] = redirect_uri

        authorization_url = LinkedInOAuthService.build_authorization_url(
            state, None, redirect_uri
        )
        return redirect(authorization_url)


class LinkedInCallbackView(FrontendBaseURLMixin, APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # Проверка быстрого запроса от фронтенда
        if request.GET.get("logged_in") == "true":
            return Response({"logged_in": True}, status=status.HTTP_200_OK)

        code = request.GET.get("code")
        error = request.GET.get("error")
        if error or not code:
            return Response({"error": "auth_failed"}, status=status.HTTP_400_BAD_REQUEST)

        redirect_uri = request.session.pop("linkedin_redirect_uri", None)
        if not redirect_uri:
            logger.warning("redirect_uri missing in session, using default")
            redirect_uri = f"{self._get_frontend_base_url(request)}/api/users/linkedin/callback/"

        token = LinkedInOAuthService.exchange_code_for_token(code, redirect_uri)
        if not token:
            logger.error("LinkedIn token exchange failed")
            return Response({"error": "token_failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"logged_in": True, "access_token": token}, status=status.HTTP_200_OK)


class LinkedInProfileView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get("access_token")
        if not access_token:
            return Response(
                {"error": "Access token is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        headers = {
            "Authorization": f"Bearer {access_token}",
        }
        userinfo_url = "https://api.linkedin.com/v2/userinfo"

        resp = requests.get(userinfo_url, headers=headers, timeout=10)
        try:
            data = resp.json()
        except ValueError:
            return Response(
                {"error": "Invalid JSON from LinkedIn", "details": resp.text},
                status=status.HTTP_502_BAD_GATEWAY
            )

        if resp.status_code != 200:
            return Response(data, status=resp.status_code)

        result = {
            "id": data.get("sub"),
            "email": data.get("email"),
            "email_verified": data.get("email_verified"),
            "first_name": data.get("given_name"),
            "last_name": data.get("family_name"),
            "full_name": data.get("name"),
            "locale": data.get("locale"),
            "picture": data.get("picture"),
        }
        return Response(result, status=status.HTTP_200_OK)
