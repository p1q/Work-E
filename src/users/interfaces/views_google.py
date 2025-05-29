from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers_google import GoogleAuthSerializer
from rest_framework.permissions import AllowAny


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            result = serializer.save()
            user = result['user']
            return Response({
                'token': result['token'],
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'username': user.username,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'avatar': user.avatar,
                    'date_joined': user.date_joined,
                }
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
