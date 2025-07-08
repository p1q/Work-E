# Інтеграція LinkedIn OAuth

---

## 🔐 Ініціація логіна

**Запит:**
```
**GET** api/users/linkedin/login/
```

**Відповідь:**
```
HTTP/1.1 302 Found
Location: https://www.linkedin.com/oauth/v2/authorization?
  response_type=code&
  client_id=CLIENT_ID&
  redirect_uri=https://BACKEND/api/users/linkedin/callback/&
  state=GENERATED_STATE&
  scope=openid%20profile%20email
```

---

## 🔁 LinkedIn callback

**LinkedIn робить редирект на:**
```
GET api/users/linkedin/callback/?code=ABC123&state=GENERATED_STATE
Cookie: sessionid=…
```

**Backend робить запит к LinkedIn:**
```
POST https://www.linkedin.com/oauth/v2/accessToken
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=ABC123&
redirect_uri=https://BACKEND/api/users/linkedin/callback/&
client_id=CLIENT_ID&
client_secret=CLIENT_SECRET
```

**Відповідь LinkedIn:**
```json
{
    "logged_in": true,
    "access_token": "AQWZQiAI ... SvJsvcV8sQ"
}
```

---

## 👤 Отримання профілю

**Запит:**
```
**POST** api/users/linkedin/profile/

{
    "access_token": "AQX0Mn ... ao3Lg"
}

```

**Відповідь:**
```json
{
    "id": "E0P1Ndct",
    "email": "mail@gmail.com",
    "email_verified": true,
    "first_name": "Name",
    "last_name": "Surname",
    "full_name": "Full Name",
    "locale": {
        "country": "US",
        "language": "en"
    },
    "picture": "https://media.licdn.com/dms/image/v2/C4D ... ZE"
}
```