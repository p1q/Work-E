import requests
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from users.infrastructure.models import User


class LinkedInAuthSerializer(serializers.Serializer):
    access_token = serializers.CharField(write_only=True)

    def validate_access_token(self, value):
        try:
            url = "https://api.linkedin.com/v2/userinfo"
            headers = {
                "Authorization": f"Bearer {value}",
            }
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                raise serializers.ValidationError(f"Invalid LinkedIn access token: {response.text}")

            linkedin_data = response.json()

            if not linkedin_data.get('sub'):
                raise serializers.ValidationError("LinkedIn response missing 'sub' field.")
            if not linkedin_data.get('email'):
                raise serializers.ValidationError("LinkedIn response missing 'email' field.")
            if 'given_name' not in linkedin_data or 'family_name' not in linkedin_data:
                raise serializers.ValidationError(
                    "LinkedIn response missing 'given_name' or 'family_name' fields."
                )

        except requests.exceptions.RequestException as e:
            raise serializers.ValidationError(f"Network error during LinkedIn token validation: {e}")
        except ValueError as e:
            raise serializers.ValidationError(f"Error decoding LinkedIn response: {e}")

        return linkedin_data

    def create(self, validated_data):
        linkedin_info = validated_data['access_token']
        linkedin_id = linkedin_info['sub']
        email = linkedin_info['email']
        first_name = linkedin_info.get('given_name', '')
        last_name = linkedin_info.get('family_name', '')
        avatar_url = linkedin_info.get('picture', '')

        # 1) Поиск по linkedin_id
        user = User.objects.filter(linkedin_id=linkedin_id).first()
        if user:
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            user.avatar_url = avatar_url
            user.save(update_fields=['email', 'first_name', 'last_name', 'avatar_url'])
        else:
            # 2) Поиск по email (существующий пользователь, привязать LinkedIn)
            user = User.objects.filter(email__iexact=email).first()
            if user:
                user.linkedin_id = linkedin_id
                user.first_name = first_name
                user.last_name = last_name
                user.avatar_url = avatar_url
                user.save(update_fields=['linkedin_id', 'first_name', 'last_name', 'avatar_url'])
            else:
                # 3) Создание нового пользователя
                base = email.split('@')[0]
                username = base
                suffix = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base}{suffix}"
                    suffix += 1

                user = User.objects.create(
                    email=email,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    avatar_url=avatar_url,
                    linkedin_id=linkedin_id
                )

        # 4) Получаем или создаём токен
        token, _ = Token.objects.get_or_create(user=user)
        return {'user': user, 'token': token.key}
