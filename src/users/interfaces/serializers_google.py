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
                settings.GOOGLE_CLIENT_ID
            )
        except ValueError:
            raise serializers.ValidationError("Invalid Google ID token")

        if idinfo.get('aud') != settings.GOOGLE_CLIENT_ID:
            raise serializers.ValidationError("Token audience mismatch")

        return idinfo

    def create(self, validated_data):
        info = validated_data['id_token']
        email = info.get('email')
        google_id = info.get('sub')
        first_name = info.get('given_name', '')
        last_name = info.get('family_name', '')
        avatar = info.get('picture', '')

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'first_name': first_name,
                'last_name': last_name,
                'google_id': google_id,
                'avatar_url': avatar,
            }
        )

        if not created and not user.google_id:
            user.google_id = google_id
            user.avatar_url = avatar
            user.save()

        token, _ = Token.objects.get_or_create(user=user)
        return {'user': user, 'token': token.key}
