from rest_framework import serializers
from django.contrib.auth import get_user_model
from cvs.models import CV

User = get_user_model()


class CVSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    filename = serializers.CharField(read_only=True)
    email = serializers.EmailField(write_only=True)
    cv_file = serializers.FileField(write_only=True)

    class Meta:
        model = CV
        fields = ['id', 'user', 'email', 'filename', 'cv_file', 'uploaded_at']
        read_only_fields = ['id', 'user', 'filename', 'uploaded_at']

    def create(self, validated_data):
        email = validated_data.pop('email')
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'email': f'Пользователь с email "{email}" не найден.'
            })
        return CV.objects.create(user=user, **validated_data)
