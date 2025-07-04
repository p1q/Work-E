import logging
from django.shortcuts import redirect
from django.views import View
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

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

        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if not origin:
            scheme = "https" if request.is_secure() else "http"
            origin = f"{scheme}://{request.get_host()}"
        origin = origin.rstrip("/").split("/api")[0]

        redirect_uri = f"{origin}/api/users/linkedin/callback/"
        front = origin

        if error or not code:
            return redirect(f"{front}/sign-up?error=auth_failed")

        verifier = LinkedInOAuthService.validate_state_and_get_verifier(request)
        if not verifier:
            logger.warning("LinkedIn OAuth failed: invalid state")
            return redirect(f"{front}/sign-up?error=invalid_state")

        token = LinkedInOAuthService.exchange_code_for_token(code, verifier, redirect_uri)
        if not token:
            logger.error("LinkedIn OAuth failed: token exchange error")
            return redirect(f"{front}/sign-up?error=token_failed")

        try:
            user_info = LinkedInOAuthService.fetch_userinfo_via_oidc(token)
        except ValueError as e:
            logger.error("LinkedIn OAuth failed fetching userinfo: %s", e)
            msg = str(e)
            if "verified" in msg:
                return redirect(f"{front}/sign-up?error=email_not_verified")
            return redirect(f"{front}/sign-up?error=no_email_returned")

        user = LinkedInOAuthService.get_or_create_user(user_info)
        tokens = AuthService.create_jwt_for_user(user)

        resp = redirect(f"{front}/")
        AuthService.attach_jwt_cookies(resp, tokens)
        return resp
