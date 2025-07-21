import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiExample
from .serializers_linkedin import LinkedInAuthSerializer

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Users'],
    request=LinkedInAuthSerializer,
    responses={
        200: OpenApiResponse(
            description='Successful login via LinkedIn',
            examples=[OpenApiExample(
                name='Successful login example',
                summary='Successful login through LinkedIn',
                value={
                    "token": "abc123def456",
                    "user": {
                        "id": 42,
                        "email": "user@example.com",
                        "username": "user42",
                        "first_name": "John",
                        "last_name": "Doe",
                        "avatar_url": "https://lh3.googleusercontent.com/.../photo.jpg",
                        "date_joined": "2025-07-01T14:30:00Z"
                    }
                }
            )]
        ),
        400: OpenApiResponse(
            description='Invalid LinkedIn token',
            examples=[OpenApiExample(
                name='Invalid token',
                summary='Token is invalid or malformed',
                value={'detail': 'Invalid LinkedIn ID token: ...'}
            )]
        )
    }
)
class LinkedInLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LinkedInAuthSerializer(data=request.data)
        if serializer.is_valid():
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
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LinkedInCallbackView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Users'],
        responses={200: OpenApiResponse(description='LinkedIn callback success')},
    )
    def get(self, request):
        code = request.GET.get('code')
        request.GET.get('state')

        if not code:
            return Response({'error': 'Missing code'}, status=400)
        return redirect(settings.FRONTEND_URL)
