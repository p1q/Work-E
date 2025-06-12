import requests
from rest_framework import serializers
from rest_framework.authtoken.models import Token
from users.infrastructure.models import User


class LinkedInAuthSerializer(serializers.Serializer):
    access_token = serializers.CharField(write_only=True)

    def validate_access_token(self, token):
        headers = {'Authorization': f'Bearer {token}'}

        profile_resp = requests.get(
            'https://api.linkedin.com/v2/me?projection=(id,localizedFirstName,localizedLastName,profilePicture(displayImage~:playableStreams))',
            headers=headers
        )
        email_resp = requests.get(
            'https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))',
            headers=headers
        )

        if not profile_resp.ok or not email_resp.ok:
            raise serializers.ValidationError("Invalid LinkedIn access token or API error.")

        profile = profile_resp.json()
        email_info = email_resp.json()

        email = email_info['elements'][0]['handle~']['emailAddress']
        first_name = profile.get('localizedFirstName', '')
        last_name = profile.get('localizedLastName', '')
        linkedin_id = profile.get('id')
        avatar_url = ''

        try:
            images = profile['profilePicture']['displayImage~']['elements']
            avatar_url = images[-1]['identifiers'][0]['identifier']
        except Exception:
            pass

        self._user_data = {
            'email': email,
            'username': email.split('@')[0],
            'first_name': first_name,
            'last_name': last_name,
            'avatar_url': avatar_url,
            'linkedin_id': linkedin_id
        }

        return token

    def create(self, validated_data):
        data = self._user_data
        user, _ = User.objects.update_or_create(
            email=data['email'],
            defaults={
                'username': data['username'],
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'avatar_url': data['avatar_url'],
            }
        )

        token, _ = Token.objects.get_or_create(user=user)
        return {'user': user, 'token': token.key}
