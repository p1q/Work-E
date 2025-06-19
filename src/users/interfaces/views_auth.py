from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import redirect
from shared.auth.service import AuthService


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = request.COOKIES.get("refresh_token")
            if token:
                from rest_framework_simplejwt.tokens import RefreshToken
                RefreshToken(token).blacklist()
        except Exception:
            pass

        resp = redirect("/")
        AuthService.clear_jwt_cookies(resp)
        return resp
