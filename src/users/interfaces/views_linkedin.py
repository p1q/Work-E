import logging
from urllib.parse import urlparse
from django.shortcuts import redirect
from django.views import View
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from .linkedin_oauth import LinkedInOAuthService
from shared.auth.service import AuthService

logger = logging.getLogger(__name__)


def _get_frontend_base(request) -> str:
    """
    Берёт Origin или Referer, парсит через urlparse и возвращает scheme://netloc,
    например "https://localhost:3001" или "https://wq.work.gd".
    """
    raw = request.headers.get("Origin") or request.headers.get("Referer") or ""
    if raw:
        p = urlparse(raw)
        scheme = p.scheme or ("https" if request.is_secure() else "http")
        netloc = p.netloc
        return f"{scheme}://{netloc}"
    # fallback
    scheme = "https" if request.is_secure() else "http"
    return f"{scheme}://{request.get_host()}"


def _get_backend_base(request) -> str:
    """
    Базовый URL текущего бэкенда: scheme://{host:port},
    например "https://127.0.0.1:8000" или "https://wq.work.gd".
    """
    scheme = "https" if request.is_secure() else "http"
    return f"{scheme}://{request.get_host()}"


class LinkedInLoginView(View):
    def get(self, request):
        # 1) PKCE + state
        state, challenge = LinkedInOAuthService.generate_pkce_and_state(request)

        # 2) redirect_uri для LinkedIn — URL фронтенда
        frontend_callback = f"{_get_frontend_base(request)}/api/users/linkedin/callback/"

        # 3) редиректим на LinkedIn
        authorization_url = LinkedInOAuthService.build_authorization_url(
            state=state,
            code_challenge=challenge,
            redirect_uri=frontend_callback
        )
        return redirect(authorization_url)


class LinkedInCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        error = request.GET.get("error")
        code = request.GET.get("code")

        backend_base = _get_backend_base(request)
        frontend_base = _get_frontend_base(request)

        # 1) Если ошибка или нет кода — сразу редиректим на фронт с флагом
        if error or not code:
            return redirect(f"{frontend_base}/?error=auth_failed")

        # 2) Проверяем state
        verifier = LinkedInOAuthService.validate_state_and_get_verifier(request)
        if not verifier:
            logger.warning("LinkedIn OAuth failed: invalid state")
            return redirect(f"{frontend_base}/?error=invalid_state")

        # 3) Обмен code → access_token
        #    Передаём тот же redirect_uri, что и при логине
        frontend_callback = f"{frontend_base}/api/users/linkedin/callback/"
        token = LinkedInOAuthService.exchange_code_for_token(
            code=code,
            verifier=verifier,
            redirect_uri=frontend_callback
        )
        if not token:
            logger.error("LinkedIn OAuth failed: token exchange error")
            return redirect(f"{frontend_base}/?error=token_failed")

        # 4) Запрос профиля и User/Token
        try:
            user_info = LinkedInOAuthService.fetch_userinfo_via_oidc(token)
        except ValueError as e:
            msg = str(e)
            err = "email_not_verified" if "verified" in msg else "no_email_returned"
            return redirect(f"{frontend_base}/?error={err}")

        user = LinkedInOAuthService.get_or_create_user(user_info)
        tokens = AuthService.create_jwt_for_user(user)

        # 5) Финальный редирект — ставим куки и уходим на фронтенд
        resp = redirect(f"{frontend_base}/?logged_in=true")
        AuthService.attach_jwt_cookies(resp, tokens)
        return resp
