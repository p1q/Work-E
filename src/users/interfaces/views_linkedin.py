from django.conf import settings
from django.shortcuts import redirect
from django.views import View
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from .linkedin_oauth import LinkedInOAuthService
from shared.auth.service import AuthService


class LinkedInLoginView(View):
    def get(self, request):
        state, challenge = LinkedInOAuthService.generate_pkce_and_state(request)
        url = LinkedInOAuthService.build_authorization_url(state, challenge)
        return redirect(url)


class LinkedInCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        error = request.GET.get("error")
        code = request.GET.get("code")
        front = settings.FRONTEND_URL

        if error or not code:
            return redirect(f"{front}/sign-up?error=auth_failed")

        verifier = LinkedInOAuthService.validate_state_and_get_verifier(request)
        if not verifier:
            return redirect(f"{front}/sign-up?error=auth_failed")

        token = LinkedInOAuthService.exchange_code_for_token(code, verifier)
        if not token:
            return redirect(f"{front}/sign-up?error=token_failed")

        try:
            user_info = LinkedInOAuthService.fetch_userinfo_via_oidc(token)
        except ValueError:
            return redirect(f"{front}/sign-up?error=no_email")

        user = LinkedInOAuthService.get_or_create_user(user_info)

        tokens = AuthService.create_jwt_for_user(user)

        resp = redirect(f"{front}/")
        AuthService.attach_jwt_cookies(resp, tokens)

        LinkedInOAuthService.cleanup_session(request)
        return resp
