import requests
from django.conf import settings
from django.shortcuts import redirect
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from users.infrastructure.models import User


class LinkedInCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        error = request.GET.get('error')
        code = request.GET.get('code')
        frontend_url = settings.FRONTEND_URL

        if error:
            return redirect(f"{frontend_url}/sign-up?error={error}")

        if not code:
            return redirect(f"{frontend_url}/sign-up?error=invalid_code")

        # 1. Exchange code for access token
        token_resp = requests.post(
            "https://www.linkedin.com/oauth/v2/accessToken",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
                "client_id": settings.LINKEDIN_CLIENT_ID,
                "client_secret": settings.LINKEDIN_CLIENT_SECRET,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        if not token_resp.ok:
            return redirect(f"{frontend_url}/sign-up?error=token_failed")

        access_token = token_resp.json().get("access_token")
        if not access_token:
            return redirect(f"{frontend_url}/sign-up?error=no_access_token")

        # 2. Use OIDC userinfo endpoint
        headers = {"Authorization": f"Bearer {access_token}"}
        userinfo_resp = requests.get("https://api.linkedin.com/v2/userinfo", headers=headers)

        if not userinfo_resp.ok:
            return redirect(f"{frontend_url}/sign-up?error=profile_failed")

        info = userinfo_resp.json()
        email = info.get("email")
        first_name = info.get("given_name", "")
        last_name = info.get("family_name", "")
        avatar_url = info.get("picture", "")
        info.get("sub")

        if not email:
            return redirect(f"{frontend_url}/sign-up?error=email_unavailable")

        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                "username": email.split("@")[0],
                "first_name": first_name,
                "last_name": last_name,
                "avatar_url": avatar_url,
            }
        )

        token, _ = Token.objects.get_or_create(user=user)

        return redirect(f"{frontend_url}/linkedin-success?token={token.key}")
