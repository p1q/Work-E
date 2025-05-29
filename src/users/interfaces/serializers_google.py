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
            # Проверяем токен у Google
            idinfo = id_token.verify_oauth2_token(
                value,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )
        except ValueError:
            raise serializers.ValidationError("Invalid Google ID token")

        # Проверяем, что токен был выдан для нашего client_id
        if idinfo['aud'] != settings.GOOGLE_CLIENT_ID:
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
            google_id=google_id,
            defaults={
                'email': email,
                'username': email.split('@')[0],
                'first_name': first_name,
                'last_name': last_name,
                'avatar_url': avatar,
            }
        )
        # если нашли по email, но google_id пустой — обновляем
        if not created and user.google_id is None:
            user.google_id = google_id
            user.avatar_url = avatar
            user.save()

        # выдаём токен DRF
        token, _ = Token.objects.get_or_create(user=user)
        return {'user': user, 'token': token.key}
