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
    """
    Новый эндпоинт:
    POST /api/users/linkedin/profile/
    Тело запроса: { "access_token": "<LinkedIn access token>" }
    Возвращает основные данные профиля и email.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        access_token = request.data.get('access_token')
        if not access_token:
            return Response(
                {'error': 'Access token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Restli-Protocol-Version': '2.0.0',
        }

        # 1) Получаем базовый профиль (минимальная проекция)
        profile_url = (
            'https://api.linkedin.com/v2/me'
            '?projection=(id,localizedFirstName,localizedLastName)'
        )
        try:
            profile_resp = requests.get(profile_url, headers=headers, timeout=10)
            profile_data = profile_resp.json()
            profile_resp.raise_for_status()
        except requests.RequestException as e:
            logger.error(
                'LinkedIn profile fetch failed: status=%s, body=%s, error=%s',
                getattr(profile_resp, 'status_code', None),
                getattr(profile_resp, 'text', None),
                e
            )
            return Response(
                {'error': 'Failed to fetch LinkedIn profile.', 'details': getattr(profile_resp, 'text', str(e))},
                status=status.HTTP_502_BAD_GATEWAY
            )

        # 2) Получаем email
        email_url = (
            'https://api.linkedin.com/v2/emailAddress'
            '?q=members&projection=(elements*(handle~))'
        )
        email_address = None
        try:
            email_resp = requests.get(email_url, headers=headers, timeout=10)
            email_data = email_resp.json()
            email_resp.raise_for_status()
            elements = email_data.get('elements', [])
            if elements:
                handle = elements[0].get('handle~', {})
                email_address = handle.get('emailAddress')
        except requests.RequestException as e:
            logger.warning(
                'LinkedIn email fetch failed: status=%s, body=%s, error=%s',
                getattr(email_resp, 'status_code', None),
                getattr(email_resp, 'text', None),
                e
            )

        # 3) Формируем ответ
        response_data = {
            'id': profile_data.get('id'),
            'first_name': profile_data.get('localizedFirstName'),
            'last_name': profile_data.get('localizedLastName'),
            'email': email_address,
            'profile_raw': profile_data,
        }
        return Response(response_data, status=status.HTTP_200_OK)
