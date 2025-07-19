import logging
import requests
from urllib.parse import urlparse, urlencode

from django.conf import settings
from django.shortcuts import redirect

from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from shared.auth.service import AuthService
from users.infrastructure.models import User
from users.interfaces.serializers import UserSerializer

from .linkedin_oauth import LinkedInOAuthService

logger = logging.getLogger(__name__)


def get_frontend_origin(request):
    # берём сохранённый при login
    origin = request.session.get('oauth_frontend_origin')
    if origin:
        return origin.rstrip('/')
    # fallback на FRONTEND_URL
    parsed = urlparse(settings.FRONTEND_URL)
    return f"{parsed.scheme}://{parsed.netloc}"


class LinkedInLoginView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        origin = request.headers.get("Origin") or request.headers.get("Referer", "")
        if origin:
            origin = origin.rstrip('/')
            request.session['oauth_frontend_origin'] = origin

        state, _ = LinkedInOAuthService.generate_pkce_and_state(request)
        base = settings.BACKEND_BASE_URL.rstrip('/')
        redirect_uri = f"{base}/api/users/linkedin/callback/"
        auth_url = LinkedInOAuthService.build_authorization_url(state, redirect_uri)
        return redirect(auth_url)


class LinkedInCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        logger.debug("LinkedInCallbackView GET params: %s", request.GET.dict())
        error = request.GET.get("error")
        code = request.GET.get("code")
        if error or not code:
            return redirect(f"{get_frontend_origin(request)}/linkedin/callback?error=oauth_failed")

        # обмен кода на LinkedIn-токен
        base = settings.BACKEND_BASE_URL.rstrip('/')
        redirect_uri = f"{base}/api/users/linkedin/callback/"
        linkedin_token = LinkedInOAuthService.exchange_code_for_token(code, redirect_uri)
        if not linkedin_token:
            return redirect(f"{get_frontend_origin(request)}/linkedin/callback?error=token_failed")

        # fetch профиль
        resp = requests.get(
            "https://api.linkedin.com/v2/userinfo",
            headers={"Authorization": f"Bearer {linkedin_token}"},
            timeout=10
        )
        if resp.status_code != 200:
            return redirect(f"{get_frontend_origin(request)}/linkedin/callback?error=profile_failed")

        profile = resp.json()
        linkedin_id = profile.get("sub")
        email = profile.get("email", "")
        first_name = profile.get("given_name", "")
        last_name = profile.get("family_name", "")
        avatar = profile.get("picture", "")

        defaults = {
            'email': email,
            'username': email.split('@')[0],
            'first_name': first_name,
            'last_name': last_name,
            'avatar_url': avatar,
        }

        try:
            user, _ = User.objects.update_or_create(
                linkedin_id=linkedin_id,
                defaults=defaults
            )
        except Exception:
            user = User.objects.get(email__iexact=email)
            user.linkedin_id = linkedin_id
            user.first_name = first_name
            user.last_name = last_name
            user.avatar_url = avatar
            user.save(update_fields=['linkedin_id', 'first_name', 'last_name', 'avatar_url'])

        tokens = AuthService.create_jwt_for_user(user)
        user_data = UserSerializer(user).data

        # собираем параметры для передачи на фронт
        params = {
            'access': tokens['access'],
            'refresh': tokens['refresh'],

            'uid': user_data['id'],
            'email': user_data['email'],
            'first_name': user_data['first_name'],
            'last_name': user_data['last_name'],
            'username': user_data['username'],
        }
        qs = urlencode(params)
        return redirect(f"{get_frontend_origin(request)}/linkedin/callback?{qs}")
