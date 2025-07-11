from django.shortcuts import redirect
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from shared.auth.service import AuthService


@extend_schema(
    tags=['Users'],
    responses={200: None}
)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            token = request.COOKIES.get("refresh_token")
            if token:
                RefreshToken(token).blacklist()
        except Exception:
            pass

        resp = redirect("/")
        AuthService.clear_jwt_cookies(resp)

        return resp
