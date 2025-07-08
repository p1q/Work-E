import logging
from urllib.parse import urlparse

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
        if request.GET.get("logged_in") == "true":
            return Response({"logged_in": True}, status=status.HTTP_200_OK)

        code = request.GET.get("code")
        error = request.GET.get("error")

        if error or not code:
            return Response({"error": "auth_failed"}, status=status.HTTP_400_BAD_REQUEST)

        redirect_uri = request.session.pop("linkedin_redirect_uri", None)
        if not redirect_uri:
            logger.error("Missing redirect_uri in session")
            return Response({"error": "server_error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        token = LinkedInOAuthService.exchange_code_for_token(code, redirect_uri)
        if not token:
            logger.error("LinkedIn token exchange failed")
            return Response({"error": "token_failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"logged_in": True, "access_token": token}, status=status.HTTP_200_OK)
