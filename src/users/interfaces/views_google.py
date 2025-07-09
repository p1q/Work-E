import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample

from .serializers_google import GoogleAuthSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Users'],
    request=GoogleAuthSerializer,
    responses={
        200: None,
        400: OpenApiResponse(
            description='Invalid or malformed Google ID token',
            examples=[
                OpenApiExample(
                    name='Malformed token',
                    summary='Token is not a valid JWT',
                    value={'detail': 'Invalid Google ID token: Unable to parse'},
                    response_only=True
                ),
                OpenApiExample(
                    name='Audience mismatch',
                    summary='Token audience does not match',
                    value={'detail': 'Token audience mismatch'},
                    response_only=True
                ),
            ]
        )
    }
)
class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        result = serializer.save()
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
        }, status=status.HTTP_200_OK)
