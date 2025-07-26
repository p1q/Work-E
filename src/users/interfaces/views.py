from django.db import IntegrityError
from rest_framework import status, generics
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from users.infrastructure.models import User
from users.interfaces.serializers import (
    UserSerializer,
    RegisterSerializer,
    LoginSerializer,
    PatchUserSerializer,
)


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')
        errors = {}
        if username and User.objects.filter(username__iexact=username).exists():
            errors['username'] = ['Користувач із таким ім\'ям вже існує.']
        if email and User.objects.filter(email__iexact=email).exists():
            errors['email'] = ['Користувач із такою електронною поштою вже існує.']
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)


class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                token, _ = Token.objects.get_or_create(user=user)
                return Response({'token': token.key}, status=status.HTTP_201_CREATED)
            except IntegrityError as e:
                err = str(e).lower()
                if 'username' in err:
                    return Response(
                        {'username': ['Користувач із таким ім\'ям вже існує.']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                if 'email' in err:
                    return Response(
                        {'email': ['Користувач із такою електронною поштою вже існує.']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                return Response(
                    {'detail': 'Не вдалося створити користувача через помилку бази даних.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
