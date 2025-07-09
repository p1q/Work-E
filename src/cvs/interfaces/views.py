from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from drf_spectacular.utils import extend_schema

from cvs.models import CV
from .serializers import CVSerializer


@extend_schema(
    tags=['CV'],
    request=CVSerializer,
    responses={201: CVSerializer, 400: None}
)
class CVListCreateView(generics.ListCreateAPIView):
    queryset = CV.objects.all()
    serializer_class = CVSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]


@extend_schema(
    tags=['CV'],
    responses={200: CVSerializer, 404: None}
)
class CVRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    queryset = CV.objects.all()
    serializer_class = CVSerializer
    permission_classes = [AllowAny]


@extend_schema(
    tags=['CV'],
    request={'application/json': {'email': 'user@example.com'}},
    responses={200: CVSerializer(many=True), 400: None, 404: None}
)
class CVByEmailPostView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        cvs = CV.objects.filter(user__email__iexact=email)
        if not cvs.exists():
            return Response({'detail': f'No CVs found for email \"{email}\".'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CVSerializer(cvs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    tags=['CV'],
    request={'application/json': {'email': 'user@example.com'}},
    responses={200: CVSerializer, 400: None, 404: None}
)
class LastCVByEmailPostView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        cv = CV.objects.filter(user__email__iexact=email).order_by('-uploaded_at').first()
        if not cv:
            return Response({'detail': f'No CV found for email \"{email}\".'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CVSerializer(cv)
        return Response(serializer.data, status=status.HTTP_200_OK)
