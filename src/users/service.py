import requests


def fetch_google_userinfo(access_token):
    url = "https://www.googleapis.com/oauth2/v3/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}
    resp = requests.get(url, headers=headers, timeout=5)

    if resp.status_code != 200:
        raise ValueError(f"Google userinfo error: {resp.status_code} {resp.text}")

    return resp.json()

def calculate_profile_completion(user):
    fields = ["first_name", "last_name", "email", "linkedin_id", "google_id", "avatar_url"]
    filled = sum(1 for field in fields if getattr(user, field))
    return int(filled / len(fields) * 100)
