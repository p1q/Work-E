import requests
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from users.infrastructure.models import User


class LinkedInAuthSerializer(serializers.Serializer):
    access_token = serializers.CharField(write_only=True)

    def validate_access_token(self, value):
        try:
            url = f"https://api.linkedin.com/v2/me"
            headers = {
                "Authorization": f"Bearer {value}",
            }
            response = requests.get(url, headers=headers)

            if response.status_code != 200:
                raise serializers.ValidationError(f"Invalid LinkedIn access token: {response.text}")

            linkedin_data = response.json()

            if not linkedin_data.get('emailAddress'):
                raise serializers.ValidationError("LinkedIn access token missing 'emailAddress' field.")
            if not linkedin_data.get('id'):
                raise serializers.ValidationError("LinkedIn access token missing 'id' field.")
            if 'localizedFirstName' not in linkedin_data or 'localizedLastName' not in linkedin_data:
                raise serializers.ValidationError("LinkedIn access token missing 'firstName' or 'lastName' fields.")

        except requests.exceptions.RequestException as e:
            raise serializers.ValidationError(f"Network error during LinkedIn token validation: {e}")
        except ValueError as e:
            raise serializers.ValidationError(f"Error decoding LinkedIn response: {e}")

        return linkedin_data

    def create(self, validated_data):
        linkedin_info = validated_data['access_token']
        email = linkedin_info.get('emailAddress', '')
        linkedin_id = linkedin_info.get('id')
        first_name = linkedin_info.get('localizedFirstName', '')
        last_name = linkedin_info.get('localizedLastName', '')
        avatar_url = \
            linkedin_info.get('profilePicture', {}).get('displayImage~', {}).get('elements', [{}])[0].get('identifiers',
                                                                                                          [{}])[0].get(
                'identifier', '')

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
