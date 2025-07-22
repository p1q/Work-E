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
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                raise serializers.ValidationError(f"Invalid LinkedIn access token: {response.text}")

            linkedin_data = response.json()

            # Перевіряємо, що LinkedIn повернув внутрішній ідентифікатор 'sub'
            if not linkedin_data.get('sub'):
                raise serializers.ValidationError("LinkedIn response missing 'sub' field.")

            # Перевіряємо наявність email
            if not linkedin_data.get('email'):
                raise serializers.ValidationError("LinkedIn response missing 'email' field.")

            # Перевіряємо наявність імені та прізвища
            if 'given_name' not in linkedin_data or 'family_name' not in linkedin_data:
                raise serializers.ValidationError("LinkedIn response missing 'given_name' or 'family_name' fields.")

        except requests.exceptions.RequestException as e:
            raise serializers.ValidationError(f"Network error during LinkedIn token validation: {e}")
        except ValueError as e:
            raise serializers.ValidationError(f"Error decoding LinkedIn response: {e}")

        return linkedin_data

    def create(self, validated_data):
        linkedin_info = validated_data['access_token']
        email = linkedin_info.get('email', '')
        linkedin_id = linkedin_info.get('sub')
        first_name = linkedin_info.get('given_name', '')
        last_name = linkedin_info.get('family_name', '')
        avatar_url = linkedin_info.get('picture', '')

        user, _ = User.objects.update_or_create(
            linkedin_id=linkedin_id,
            defaults={
                'email': email,
                'username': email.split('@')[0],
                'first_name': first_name,
                'last_name': last_name,
                'avatar_url': avatar_url,
            }
        )

        token, _ = Token.objects.get_or_create(user=user)
        return {'user': user, 'token': token.key}
