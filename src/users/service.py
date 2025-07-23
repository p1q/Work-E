import requests
from django.conf import settings


def validate_access_token(access_token):
    # 1) Перевірка токена
    tokeninfo_url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}"
    resp = requests.get(tokeninfo_url, timeout=5)
    if resp.status_code != 200:
        raise ValueError("Invalid or expired access token")

    data = resp.json()
    aud = data.get('aud') or data.get('audience')
    if aud != settings.GOOGLE_CLIENT_ID:
        raise ValueError("Token audience mismatch")

    # 2) Запит повного профілю користувача
    userinfo_url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp2 = requests.get(userinfo_url, headers=headers, timeout=5)
    if resp2.status_code != 200:
        raise ValueError("Failed to fetch user info from Google")

    userinfo = resp2.json()
    return userinfo
