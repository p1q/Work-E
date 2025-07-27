import logging

from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from src.schemas.users import (LINKEDIN_LOGIN_REQUEST, LINKEDIN_LOGIN_RESPONSE_SUCCESS, LINKEDIN_LOGIN_RESPONSE_ERROR, )
from .serializers_linkedin import LinkedInAuthSerializer

logger = logging.getLogger(__name__)


class LinkedInLoginView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=LINKEDIN_LOGIN_REQUEST,
        responses={
            200: LINKEDIN_LOGIN_RESPONSE_SUCCESS,
            400: LINKEDIN_LOGIN_RESPONSE_ERROR,
            500: LINKEDIN_LOGIN_RESPONSE_ERROR,
        },
        description='Аутентифікація користувача через LinkedIn OAuth2 токен.',
        summary='Вхід через LinkedIn'
    )
    def post(self, request):
        serializer = LinkedInAuthSerializer(data=request.data)
        if serializer.is_valid():
            try:
                result = serializer.save()
            except serializers.ValidationError as e:
                return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                logger.error(f"Unexpected error during LinkedIn authentication: {e}")
                return Response({"detail": "An unexpected error occurred during LinkedIn authentication."},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            user = result['user']
            token = result['token']
            return Response({
                'token': token,
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'avatar_url': user.avatar_url,
                    'date_joined': user.date_joined,
                }
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LinkedInCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        code = request.GET.get('code')
        request.GET.get('state')
        if not code:
            return Response({'error': 'Missing code'}, status=400)
        return redirect(settings.FRONTEND_URL)
