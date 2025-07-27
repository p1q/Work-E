from django.db import IntegrityError
from drf_spectacular.utils import extend_schema, OpenApiRequest
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

from src.schemas.users import (USER_LIST_RESPONSE, USER_CREATE_REQUEST, USER_DETAIL_RESPONSE, USER_UPDATE_REQUEST,
                               USER_UPDATE_RESPONSE, USER_DELETE_RESPONSE, REGISTER_REQUEST, REGISTER_RESPONSE_SUCCESS,
                               REGISTER_RESPONSE_ERROR,
                               LOGIN_REQUEST, LOGIN_RESPONSE_SUCCESS, LOGIN_RESPONSE_ERROR, CURRENT_USER_RESPONSE, )


class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    @extend_schema(
        responses={200: USER_LIST_RESPONSE},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        request=OpenApiRequest(USER_CREATE_REQUEST),
        responses={200: USER_LIST_RESPONSE},
    )
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

    @extend_schema(
        responses={200: USER_DETAIL_RESPONSE},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        request=USER_UPDATE_REQUEST,
        responses={200: USER_UPDATE_RESPONSE},
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        request=USER_UPDATE_REQUEST,
        responses={200: USER_UPDATE_RESPONSE},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        responses={204: USER_DELETE_RESPONSE},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=REGISTER_REQUEST,
        responses={
            201: REGISTER_RESPONSE_SUCCESS,
            400: REGISTER_RESPONSE_ERROR,
        },
        description='Створює нового користувача та повертає токен.',
        summary='Реєстрація нового користувача'
    )
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

    @extend_schema(
        request=LOGIN_REQUEST,
        responses={
            200: LOGIN_RESPONSE_SUCCESS,
            400: LOGIN_RESPONSE_ERROR,
        },
        description='Аутентифікує користувача та повертає токен.',
        summary='Вхід користувача'
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            token, _ = Token.objects.get_or_create(user=user)
            return Response({'token': token.key})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: CURRENT_USER_RESPONSE},
        description='Повертає інформацію про поточного аутентифікованого користувача.',
        summary='Отримати інформацію про поточного користувача'
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
