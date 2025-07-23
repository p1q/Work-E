import requests
from django.conf import settings


def validate_access_token(access_token):
    url = f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        if data.get('aud') != settings.GOOGLE_CLIENT_ID:
            raise ValueError("Token audience mismatch")

        return data
    else:
        raise ValueError("Invalid or expired access token")
