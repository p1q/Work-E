from django.db import IntegrityError
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiExample

from users.infrastructure.models import User
from users.interfaces.serializers import UserSerializer, RegisterSerializer, LoginSerializer
import logging


@extend_schema(
    tags=['Users'],
    request=UserSerializer,
    responses={200: UserSerializer}
)
class UserListCreateView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')

        errors = {}
        if username and User.objects.filter(username__iexact=username).exists():
            errors['username'] = ['A user with that username already exists.']
        if email and User.objects.filter(email__iexact=email).exists():
            errors['email'] = ['A user with that email already exists.']

        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)


@extend_schema(
    tags=['Users'],
    request=UserSerializer,
    responses={200: UserSerializer}
)
class UserRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


@extend_schema(
    tags=['Users'],
    request=RegisterSerializer,
    responses={201: {'application/json': {'token': 'abc123'}}, 400: None},
    examples=[
        OpenApiExample('Реєстрація', summary='Створення нового користувача',
                       value={'email': 'a@b.c', 'username': 'user', 'password': 'pass'})
    ]
)
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
                    return Response({'username': ['A user with that username already exists.']},
                                    status=status.HTTP_400_BAD_REQUEST)
                if 'email' in err:
                    return Response({'email': ['A user with that email already exists.']},
                                    status=status.HTTP_400_BAD_REQUEST)
                return Response({'detail': 'Could not create user due to database error.'},
                                status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    tags=['Users'],
    request=LoginSerializer,
    responses={200: {'application/json': {'token': 'abc123'}}, 400: None},
    examples=[
        OpenApiExample('Логін', summary='Аутентифікація за email і паролем',
                       value={'email': 'a@b.c', 'password': 'pass'})
    ]
)
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
        logger = logging.getLogger('linkedin')
        logger.debug(f"Accessing /current for user: {request.user.email}")
        return Response(UserSerializer(request.user).data)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        logger = logging.getLogger('linkedin')
        logger.debug("========== /api/users/current/ ==========")
        logger.debug(f"Method: {request.method}")
        logger.debug(f"Path: {request.get_full_path()}")
        logger.debug(f"Headers: {dict(request.headers)}")
        logger.debug(f"Cookies present: {'YES' if request.COOKIES else 'NO'}")
        logger.debug(f"Cookies content: {dict(request.COOKIES)}")
        logger.debug(f"User: {request.user} (id={request.user.id})")

        return Response(UserSerializer(request.user).data)
