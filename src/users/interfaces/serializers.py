import re
from rest_framework import serializers
from django.contrib.auth import authenticate
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

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


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

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if user is None:
            raise serializers.ValidationError("Invalid credentials")
        data['user'] = user
        return data
