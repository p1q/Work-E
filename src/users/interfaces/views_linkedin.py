import logging
from urllib.parse import urlparse

from django.conf import settings
from django.shortcuts import redirect
from django.views import View
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from shared.auth.service import AuthService

from .linkedin_oauth import LinkedInOAuthService

logger = logging.getLogger(__name__)

class LinkedInLoginView(View):
    def get(self, request):
        # --- Step 1: Compute base frontend URL ---
        frontend_base_url = self._get_frontend_base_url(request)

        # --- Step 2: Frontend -> Backend: GET /api/users/linkedin/login/ ---
        # Generate PKCE code verifier and state for security
        state, challenge = LinkedInOAuthService.generate_pkce_and_state(request)
        # Build callback URI that LinkedIn will redirect to
        redirect_uri = f"{frontend_base_url}/api/users/linkedin/callback/"
        print(f"Redirect URI: {redirect_uri}")  # For debugging

        # --- Step 4: Backend -> Frontend: 302 redirect to LinkedIn Authorization URL ---
        authorization_url = LinkedInOAuthService.build_authorization_url(
            state, challenge, redirect_uri
        )
        return redirect(authorization_url)

    def _get_frontend_base_url(self, request):
        """
        Computes and returns the base URL for the frontend (origin URL), without any paths.
        This URL is used throughout the OAuth process.
        """
        # Get the origin from headers or build it using scheme and host
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if not origin:
            scheme = "https" if request.is_secure() else "http"
            origin = f"{scheme}://{request.get_host()}"

        # Разбираем URL и получаем только схему и хост
        parsed_url = urlparse(origin)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        return base_url


class LinkedInCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        # --- Step 1: Compute base frontend URL ---
        frontend_base_url = self._get_frontend_base_url(request)

        # Get BACKEND_BASE_URL from environment
        backend_base_url = settings.BACKEND_BASE_URL

        # --- Step 5: LinkedIn -> Backend: GET /api/users/linkedin/callback?code=...&state=... ---
        error = request.GET.get("error")
        code = request.GET.get("code")
        if error or not code:
            # Authorization failed
            return redirect(self._fixed_callback_url(frontend_base_url) + "?error=auth_failed")

        # --- Step 6: Validate state and retrieve PKCE verifier ---
        verifier = LinkedInOAuthService.validate_state_and_get_verifier(request)
        if not verifier:
            logger.warning("LinkedIn OAuth failed: invalid state")
            return redirect(self._fixed_callback_url(frontend_base_url) + "?error=invalid_state")

        # Reconstruct the exact redirect URI used in the authorization step
        dynamic_redirect_uri = self._dynamic_callback_url(request, frontend_base_url)
        print(f"Dynamic Redirect URI: {dynamic_redirect_uri}")  # For debugging

        # --- Step 8: Backend -> LinkedIn: POST /oauth/v2/accessToken to exchange code for access token ---
        token = LinkedInOAuthService.exchange_code_for_token(
            code, verifier, dynamic_redirect_uri
        )
        if not token:
            logger.error("LinkedIn OAuth failed: token exchange error")
            return redirect(self._fixed_callback_url(frontend_base_url) + "?error=token_failed")

        # --- Step 9: Backend -> LinkedIn: GET /oauth/v2/userinfo with Bearer token ---
        try:
            user_info = LinkedInOAuthService.fetch_userinfo_via_oidc(token)
        except ValueError as e:
            msg = str(e)
            err = "email_not_verified" if "verified" in msg else "no_email_returned"
            return redirect(self._fixed_callback_url(frontend_base_url) + f"?error={err}")

        # Create or update the User in our database
        user = LinkedInOAuthService.get_or_create_user(user_info)

        # --- Step 10: Create JWT tokens for the user ---
        tokens = AuthService.create_jwt_for_user(user)

        # --- Step 11: Backend -> Frontend: 302 redirect with JWT cookies set ---
        resp = redirect(self._fixed_callback_url(frontend_base_url))
        AuthService.attach_jwt_cookies(resp, tokens)
        return resp

    def _get_frontend_base_url(self, request):
        """
        Computes and returns the base URL for the frontend (origin URL), without any paths.
        This URL is used throughout the OAuth process.
        """
        # Get the origin from headers or build it using scheme and host
        origin = request.headers.get("Origin") or request.headers.get("Referer")
        if not origin:
            scheme = "https" if request.is_secure() else "http"
            origin = f"{scheme}://{request.get_host()}"

        #
