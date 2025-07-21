from rest_framework import serializers
from django.conf import settings
from google.oauth2 import id_token
from google.auth.transport import requests
from users.infrastructure.models import User
from rest_framework.authtoken.models import Token


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField(write_only=True)

    def validate_id_token(self, value):
        try:
            idinfo = id_token.verify_oauth2_token(
                value,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID,
                clock_skew_in_seconds=15
            )
        except ValueError as e:
            raise serializers.ValidationError(f"Invalid Google ID token: {e}")
        except requests.exceptions.RequestException as e:
            raise serializers.ValidationError(f"Network error during Google token validation: {e}")

        aud = idinfo.get('aud')
        valid_aud = settings.GOOGLE_CLIENT_ID
        if isinstance(aud, list):
            if valid_aud not in aud:
                raise serializers.ValidationError("Token audience mismatch")
        else:
            if aud != valid_aud:
                raise serializers.ValidationError("Token audience mismatch")

        return idinfo

    def create(self, validated_data):
        info = validated_data['id_token']
        email = info.get('email')
        google_id = info.get('sub')
        first_name = info.get('given_name', '')
        last_name = info.get('family_name', '')
        avatar_url = info.get('picture', '')

        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'first_name': first_name,
                'last_name': last_name,
                'google_id': google_id,
                'avatar_url': avatar_url,
            }
        )

        token, _ = Token.objects.get_or_create(user=user)
        return {'user': user, 'token': token.key}
