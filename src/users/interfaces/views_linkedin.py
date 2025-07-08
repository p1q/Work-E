import logging
from urllib.parse import urlparse

from django.conf import settings
from django.shortcuts import redirect
from django.views import View
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .linkedin_oauth import LinkedInOAuthService

logger = logging.getLogger(__name__)

class LinkedInLoginView(View):
    permission_classes = [AllowAny]

    def get(self, request):
        # 1) вычисляем базовый фронтенд-URL
        frontend_base_url = self._get_frontend_base_url(request)

        # 2) генерируем state (PKCE больше не нужен)
        state, _ = LinkedInOAuthService.generate_pkce_and_state(request)

        # 3) собираем точный redirect_uri
        redirect_uri = f"{frontend_base_url}/api/users/linkedin/callback/"

        # Сохраняем его в сессии, чтобы потом использовать именно тот же при обмене
        request.session["linkedin_redirect_uri"] = redirect_uri

        # 4) строим URL авторизации LinkedIn и редиректим
        authorization_url = LinkedInOAuthService.build_authorization_url(
            state, None, redirect_uri  # PKCE не передается
        )
        return redirect(authorization_url)

    def _get_frontend_base_url(self, request):
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if not origin:
            scheme = "https" if request.is_secure() else "http"
            origin = f"{scheme}://{request.get_host()}"
        parsed = urlparse(origin)
        return f"{parsed.scheme}://{parsed.netloc}"

class LinkedInCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        frontend_base_url = self._get_frontend_base_url(request)

        code = request.GET.get("code")
        error = request.GET.get("error")
        if error or not code:
            return redirect(f"{frontend_base_url}/linkedin/callback/?error=auth_failed")

        # убираем проверку state и code_verifier
        redirect_uri = request.session.pop("linkedin_redirect_uri", None)
        if not redirect_uri:
            logger.error("Missing redirect_uri in session")
            return redirect(f"{frontend_base_url}/linkedin/callback/?error=server_error")

        # обмениваем код на токен
        token = LinkedInOAuthService.exchange_code_for_token(code, redirect_uri)
        if not token:
            logger.error("LinkedIn OAuth failed: token exchange error")
            return redirect(f"{frontend_base_url}/linkedin/callback/?error=token_failed")

        # перенаправляем пользователя (токен может быть использован в дальнейшем для аутентификации)
        return redirect(f"{frontend_base_url}/linkedin/callback/?logged_in=true")

    def _get_frontend_base_url(self, request):
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if not origin:
            scheme = "https" if request.is_secure() else "http"
            origin = f"{scheme}://{request.get_host()}"
        parsed = urlparse(origin)
        return f"{parsed.scheme}://{parsed.netloc}"
