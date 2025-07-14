from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from shared.auth.service import AuthService


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except Exception:
                pass

        response = Response(
            {"detail": "Logout successful"},
            status=status.HTTP_200_OK
        )
        AuthService.clear_jwt_cookies(response)
        return response
