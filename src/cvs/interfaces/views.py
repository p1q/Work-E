from django.utils.decorators import method_decorator
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiResponse

from ..models import CV
from .serializers import CVSerializer, CoverLetterSerializer, CVGenerationSerializer
from src.schemas.cvs import (
    CV_LIST_RESPONSE,
    CV_CREATE,
    CV_DETAIL_RESPONSE,
    CV_DELETE_RESPONSE,
    CV_BY_EMAIL,
    CV_LAST_BY_EMAIL,
    CV_LIST_PARAMETERS
)
import logging
import os
from rest_framework import status
from rest_framework.response import Response
import google.generativeai as genai
from dotenv import load_dotenv
from django_ratelimit.decorators import ratelimit

logger = logging.getLogger(__name__)

# Load env and configure genai once (better in app config but okay here)
load_dotenv()
API_KEY = os.getenv("GENAI_API_KEY")
if not API_KEY:
    logger.error("GENAI_API_KEY is not set in environment")
    raise RuntimeError("GENAI_API_KEY is not set")
genai.configure(api_key=API_KEY)


@method_decorator(
    ratelimit(key='ip', rate='1/m', method='POST', block=True),
    name='post'
)
@extend_schema(
    tags=["AI"],
    request=CVGenerationSerializer,
    responses={
        200: OpenApiResponse(description="Generated CV", response=CVGenerationSerializer),
        400: OpenApiResponse(description="Validation Error"),
        500: OpenApiResponse(description="Server Error"),
    },
)
class GenerateCVView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request) -> Response:
        serializer = CVGenerationSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid CV input data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        profile_data = serializer.validated_data

        # Clear prompt to guide the model better with structure and output format
        prompt = (
            "You are a helpful assistant that generates a professional CV in Markdown format.\n"
            "Use the following structured user profile data:\n"
            f"{profile_data}\n\n"
            "Format the output as a clean Markdown CV with sections: Contact, Summary, Experience, Skills, Education.\n"
            "Use bullet points and headers as appropriate.\n"
            "Do not include any extra text or explanation."
        )

        try:
            model = genai.GenerativeModel('gemini-2.5-pro')
            response = model.generate_content(prompt)
            return Response({'cv': response.text}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"CV generation failed: {e}", exc_info=True)
            return Response({'error': 'Failed to generate CV.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(
    ratelimit(key='ip', rate='1/m', method='POST', block=True),
    name='post'
)
@extend_schema(
    tags=["AI"],
    request=CoverLetterSerializer,
    responses={
        200: OpenApiResponse(description="Adapted Cover Letter", response=CoverLetterSerializer),
        400: OpenApiResponse(description="Validation Error"),
        500: OpenApiResponse(description="Server Error"),
    },
)
class AdaptCoverLetterView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request) -> Response:
        serializer = CoverLetterSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Invalid Cover Letter input data: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        base_letter = serializer.validated_data.get('coverLetter')
        job_description = serializer.validated_data.get('job_description')

        prompt = (
            "You are a helpful assistant that adapts a cover letter to match a job description.\n"
            "Given the base cover letter and the job description below, produce a tailored cover letter.\n\n"
            f"Base Cover Letter:\n{base_letter}\n\n"
            f"Job Description:\n{job_description}\n\n"
            "Rewrite the cover letter emphasizing relevant skills and experience matching the job. "
            "Keep it professional and concise."
        )

        try:
            model = genai.GenerativeModel('gemini-2.5-pro')
            response = model.generate_content(prompt)
            return Response({'cover_letter': response.text}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Cover letter adaptation failed: {e}", exc_info=True)
            return Response({'error': 'Failed to adapt cover letter.'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    responses={200: CV_LIST_RESPONSE},
    parameters=CV_LIST_PARAMETERS
)
class CVListCreateView(generics.ListCreateAPIView):
    queryset = CV.objects.all()
    serializer_class = CVSerializer
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(**CV_CREATE)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        if email := self.request.query_params.get('email'):
            queryset = queryset.filter(user__email__iexact=email)
        return queryset


@extend_schema(
    responses={
        200: CV_DETAIL_RESPONSE,
        204: CV_DELETE_RESPONSE
    }
)
class CVRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    queryset = CV.objects.all()
    serializer_class = CVSerializer
    permission_classes = [AllowAny]

    def delete(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


@extend_schema(**CV_BY_EMAIL)
class CVByEmailPostView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Електронна пошта обов\'язкова.'}, status=status.HTTP_400_BAD_REQUEST)
        cvs = CV.objects.filter(user__email__iexact=email)
        if not cvs.exists():
            return Response({'detail': f'Резюме для "{email}" не знайдено.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CVSerializer(cvs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(**CV_LAST_BY_EMAIL)
class LastCVByEmailPostView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'Електронна пошта обов\'язкова.'}, status=status.HTTP_400_BAD_REQUEST)
        cv = CV.objects.filter(user__email__iexact=email).order_by('-uploaded_at').first()
        if not cv:
            return Response({'detail': f'Резюме для "{email}" не знайдено.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CVSerializer(cv)
        return Response(serializer.data, status=status.HTTP_200_OK)
