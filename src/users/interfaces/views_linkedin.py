from django.shortcuts import redirect
from django.views import View
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import logging
from .linkedin_oauth import LinkedInOAuthService
from shared.auth.service import AuthService

logger = logging.getLogger(__name__)


class LinkedInLoginView(View):
    def get(self, request):
        state, challenge = LinkedInOAuthService.generate_pkce_and_state(request)
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if not origin:
            scheme = "https" if request.is_secure() else "http"
            origin = f"{scheme}://{request.get_host()}"
        origin = origin.rstrip("/").split("/api")[0]
        redirect_uri = f"{origin}/api/users/linkedin/callback/"
        authorization_url = LinkedInOAuthService.build_authorization_url(state, challenge, redirect_uri)
        return redirect(authorization_url)


class LinkedInCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        error = request.GET.get("error")
        code = request.GET.get("code")
        if error or not code:
            return redirect(self._fixed_callback_url() + "?error=auth_failed")
        verifier = LinkedInOAuthService.validate_state_and_get_verifier(request)
        if not verifier:
            logger.warning("LinkedIn OAuth failed: invalid state")
            return redirect(self._fixed_callback_url() + "?error=invalid_state")
        dynamic_redirect_uri = self._dynamic_callback_url(request)
        token = LinkedInOAuthService.exchange_code_for_token(code, verifier, dynamic_redirect_uri)
        if not token:
            logger.error("LinkedIn OAuth failed: token exchange error")
            return redirect(self._fixed_callback_url() + "?error=token_failed")
        try:
            user_info = LinkedInOAuthService.fetch_userinfo_via_oidc(token)
        except ValueError as e:
            msg = str(e)
            err = "email_not_verified" if "verified" in msg else "no_email_returned"
            return redirect(self._fixed_callback_url() + f"?error={err}")
        user = LinkedInOAuthService.get_or_create_user(user_info)
        tokens = AuthService.create_jwt_for_user(user)
        resp = redirect(self._fixed_callback_url())
        AuthService.attach_jwt_cookies(resp, tokens)
        return resp

    @staticmethod
    def _dynamic_callback_url(request) -> str:
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if not origin:
            scheme = "https" if request.is_secure() else "http"
            origin = f"{scheme}://{request.get_host()}"
        origin = origin.rstrip("/").split("/api")[0]
        return f"{origin}/api/users/linkedin/callback/"
