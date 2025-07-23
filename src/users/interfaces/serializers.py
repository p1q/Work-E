import re
from rest_framework import serializers
from django.core.validators import RegexValidator
from users.infrastructure.models import User

sql_injection_validator = RegexValidator(
    regex=r'^(?!.*(;|--|\b(drop|insert|delete|update|select)\b)).*$',
    flags=re.IGNORECASE,
    message="Field contains invalid or potentially dangerous characters."
)


class UserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=30,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z0-9._-]+$',
                message="Username may contain only letters, numbers, dots, underscores and hyphens."
            )
        ]
    )
    first_name = serializers.CharField(
        max_length=30,
        allow_blank=True,
        validators=[sql_injection_validator]
    )
    last_name = serializers.CharField(
        max_length=30,
        allow_blank=True,
        validators=[sql_injection_validator]
    )
    email = serializers.EmailField(max_length=254)
    avatar_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)
    linkedin_id = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'avatar_url', 'linkedin_id', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined', 'linkedin_id']


class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        max_length=30,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-z0-9._-]+$',
                message="Username may contain only letters, numbers, dots, underscores and hyphens."
            )
        ]
    )
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password']
        read_only_fields = ['id']

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        from django.contrib.auth import authenticate
        try:
            User.objects.get(email__iexact=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist.")

        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials.")
        data['user'] = user
        return data


class PatchUserSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(
        max_length=30,
        allow_blank=True,
        validators=[sql_injection_validator]
    )
    last_name = serializers.CharField(
        max_length=30,
        allow_blank=True,
        validators=[sql_injection_validator]
    )
    avatar_url = serializers.URLField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'avatar_url']
