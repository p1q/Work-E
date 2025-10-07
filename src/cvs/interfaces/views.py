import io
import logging
import os
import time
import uuid
from os.path import basename

import google.generativeai as genai
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from dotenv import load_dotenv
from drf_spectacular.utils import extend_schema, OpenApiResponse
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from jsonschema import ValidationError
from rest_framework import generics
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from src.schemas.cvs import (CV_LIST_RESPONSE, CV_CREATE, CV_DETAIL_RESPONSE, CV_DELETE_RESPONSE, CV_BY_EMAIL,
                             CV_LAST_BY_EMAIL, CV_LIST_PARAMETERS)
from .serializers import AnalyzeCVRequestSerializer, AnalyzeCVResponseSerializer, CVSerializer, CoverLetterSerializer, \
    CVGenerationSerializer, DownloadCVRequestSerializer, ExtractTextFromCVRequestSerializer, \
    ExtractTextFromCVResponseSerializer, User, ExtractTextFromCVUploadRequestSerializer
from ..models import CV
from ..service import analyze_cv_with_ai, extract_text_from_cv, extract_text_from_pdf_bytes

logger = logging.getLogger(__name__)

# Load env and configure genai once (better in app config but okay here)
load_dotenv()
API_KEY = os.getenv("GENAI_API_KEY")
if not API_KEY:
    logger.error("GENAI_API_KEY is not set in environment")
    raise RuntimeError("GENAI_API_KEY is not set")
genai.configure(api_key=API_KEY)


def _get_latest_cv_for_user(user_id, logger):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        logger.warning(f"Користувач із id {user_id} не знайдений.")
        return None, Response({'error': f'Користувача з ID {user_id} не знайдено.'}, status=status.HTTP_404_NOT_FOUND)

    cv = CV.objects.filter(user=user).order_by('-created_at').first()
    if not cv:
        logger.info(f"CV для користувача {user_id} не знайдено")
        return None, Response({'error': f'Резюме для користувача з ID {user_id} не знайдено.'},
                              status=status.HTTP_404_NOT_FOUND)

    return cv, None


def handle_serializer_validation(serializer, logger, view_name):
    if not serializer.is_valid():
        logger.warning(f"Недійсні дані запиту для {view_name}: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return None


@method_decorator(
    ratelimit(key='ip', rate='6/m', method='POST', block=True),
    name='post'
)
@extend_schema(
    tags=["AI"],
    request=CVGenerationSerializer,
    responses={200: OpenApiResponse(description="Generated CV", response=CVGenerationSerializer),
               400: OpenApiResponse(description="Validation Error"),
               500: OpenApiResponse(description="Server Error")},
)
class GenerateCVView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request) -> Response:
        serializer = CVGenerationSerializer(data=request.data)
        validation_response = handle_serializer_validation(serializer, logger, "GenerateCVView")
        if validation_response:
            return validation_response

        profile_data = serializer.validated_data

        profile_str = f"Name: {profile_data.get('name')} {profile_data.get('lastname')}\n\n"

        profile_str += "Experience:\n"
        for exp in profile_data.get('experience', []):
            responsibilities = exp.get("responsibilities", [])
            resp_str = "\n  ".join([f"- {r}" for r in responsibilities])
            profile_str += f"- {exp.get('role')} at {exp.get('company')} ({exp.get('duration')}):\n  {resp_str}\n"

        profile_str += "\nSkills:\n"
        for skill in profile_data.get('skills', []):
            profile_str += f"- {skill}\n"

        profile_str += "\nEducation:\n"
        for edu in profile_data.get('education', []):
            profile_str += f"- {edu.get('degree')} at {edu.get('institution')} ({edu.get('year')})\n"

        prompt = f"""
        You are a professional CV writer.

        Using the structured profile data below, generate a complete CV in Markdown format.

        The CV must always include sections: Contact, Summary, Experience, Skills, and Education.
        If some information is missing, make reasonable assumptions.
        Do not leave the CV empty.

        Profile Data:
        {profile_str}
        """

        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=2000,
                ),
                safety_settings=[
                    {"category": HarmCategory.HARM_CATEGORY_HARASSMENT, "threshold": HarmBlockThreshold.BLOCK_NONE},
                    {"category": HarmCategory.HARM_CATEGORY_HATE_SPEECH, "threshold": HarmBlockThreshold.BLOCK_NONE},
                    {"category": HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                     "threshold": HarmBlockThreshold.BLOCK_NONE},
                    {"category": HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                     "threshold": HarmBlockThreshold.BLOCK_NONE},
                ]
            )

            # Log raw response for debugging
            logger.debug("Raw Gemini response: %s", response)

            generated_text = None

            # First try response.text (safe access)
            try:
                generated_text = response.text
            except Exception as e:
                logger.warning("response.text accessor failed: %s", e)

            # Fallback: candidates -> parts
            if not generated_text and response.candidates:
                for candidate in response.candidates:
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, "text") and part.text:
                                generated_text = part.text
                                break
                    if generated_text:
                        break

            if not generated_text:
                logger.error("No text in response. finish_reason=%s, full response=%s",
                             response.candidates[0].finish_reason if response.candidates else "unknown",
                             response)
                return Response({'error': 'No CV generated. Please try again.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({'cv': generated_text}, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"CV generation failed with unexpected error: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(
    ratelimit(key='ip', rate='6/m', method='POST', block=True),
    name='post'
)
@extend_schema(
    tags=["AI"],
    request=CoverLetterSerializer,
    responses={
        200: OpenApiResponse(description="Adapted Cover Letter", response=CoverLetterSerializer),
        400: OpenApiResponse(description="Validation Error"),
        500: OpenApiResponse(description="Server Error")
    },
)
class AdaptCoverLetterView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    MAX_RETRIES = 3

    def post(self, request) -> Response:
        serializer = CoverLetterSerializer(data=request.data)
        validation_response = handle_serializer_validation(serializer, logger, "AdaptCoverLetterView")
        if validation_response:
            return validation_response

        base_letter = serializer.validated_data.get('coverLetter', '').strip()
        job_description = serializer.validated_data.get('job_description', '').strip()

        if not base_letter or not job_description:
            return Response(
                {'error': 'Cover letter and job description are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        structured_input = (
            f"Base Cover Letter:\n{base_letter}\n\n"
            f"Job Description:\n{job_description}\n"
        )

        prompt = (
            "You are a helpful assistant that adapts a cover letter to match a job description.\n"
            "Use the structured input below to produce a tailored cover letter.\n"
            f"---\n{structured_input}---\n"
            "Rewrite the cover letter emphasizing relevant skills and experience matching the job. "
            "Keep it professional, concise, and do not include extra text."
        )

        try:
            model = genai.GenerativeModel('gemini-2.5-flash')

            for attempt in range(self.MAX_RETRIES):
                logger.debug("Sending prompt to AI (attempt %d): %s", attempt + 1, prompt)
                response = model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(max_output_tokens=2000)
                )

                if response.candidates and response.candidates[0].content.parts:
                    generated_text = response.candidates[0].content.parts[0].text
                    return Response({'cover_letter': generated_text}, status=status.HTTP_200_OK)

                logger.warning(
                    "No content returned from AI (attempt %d). finish_reason=%s",
                    attempt + 1,
                    response.candidates[0].finish_reason if response.candidates else "unknown"
                )
                time.sleep(1)  # small delay before retry

            return Response(
                {'error': 'No cover letter generated after multiple attempts. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        except Exception as e:
            logger.error("Cover letter adaptation failed: %s", e, exc_info=True)
            return Response({'error': 'Failed to adapt cover letter.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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
    responses={200: CV_DETAIL_RESPONSE, 204: CV_DELETE_RESPONSE}
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


@extend_schema(
    tags=["CVs"],
    summary="Извлечь текст из загруженного PDF резюме",
    description="Принимает PDF-файл резюме через multipart/form-data и извлекает из него текстовое содержимое.",
    #**EXTRACT_TEXT_FROM_CV_UPLOAD,
    responses={
        200: ExtractTextFromCVResponseSerializer,
        400: OpenApiResponse(description='Помилка в запиті або обробці PDF'),
        500: OpenApiResponse(description='Внутрішня помилка сервера'),
    },
)
class ExtractTextFromCVView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        serializer = ExtractTextFromCVUploadRequestSerializer(data=request.data)

        if not serializer.is_valid():
            logger.warning(f"Недійсні дані запиту для ExtractTextFromCVView: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_pdf_file = serializer.validated_data.get('cv_file')

        try:
            pdf_content_bytes = uploaded_pdf_file.read()
            pdf_stream = io.BytesIO(pdf_content_bytes)
            extracted_text, method_used = extract_text_from_pdf_bytes(pdf_stream)

            if not extracted_text:
                logger.warning(f"Не вдалося видобути текст з завантаженого PDF файлу: {uploaded_pdf_file.name}")
                return Response({'error': 'Не вдалося видобути текст з PDF файлу. Файл може бути сканованим (без текстового шару), порожнім або пошкодженим.'}, status=status.HTTP_400_BAD_REQUEST)

            response_data = {
                'text': extracted_text,
                'method': method_used,
                'cv_id': None,
                'filename': uploaded_pdf_file.name
            }
            response_serializer = ExtractTextFromCVResponseSerializer(response_data)

            logger.info(f"Успішно видобуто текст (метод: {method_used}) з завантаженого PDF файлу: {uploaded_pdf_file.name}")
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except ValidationError as e:
            logger.warning(f"Помилка валідації при обробці PDF файлу {uploaded_pdf_file.name}: {e.message}")
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Неочікувана помилка при видобуванні тексту з завантаженого PDF файлу {uploaded_pdf_file.name}: {e}", exc_info=True)
            return Response({'error': 'Внутрішня помилка сервера'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    tags=["CVs"],
    summary="Проаналізувати резюме користувача за допомогою ШІ",
    description="Отримує останнє завантажене резюме користувача за його ID, "
                "видобуває текст, потім надсилає текст до ШІ для аналізу та "
                "видобування структурованих даних.",
    request=AnalyzeCVRequestSerializer,
    responses={200: AnalyzeCVResponseSerializer,
               400: OpenApiResponse(description='Помилка в запиті або даних користувача/CV'),
               404: OpenApiResponse(description='Користувач або CV не знайдено'),
               500: OpenApiResponse(description='Помилка сервера під час обробки PDF або взаємодії з ШІ'),
               503: OpenApiResponse(description='Сервіс ШІ недоступний')},
)
class AnalyzeCVView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        logger = logging.getLogger(__name__)
        serializer = AnalyzeCVRequestSerializer(data=request.data)
        validation_response = handle_serializer_validation(serializer, logger, "AnalyzeCVView")
        if validation_response:
            return validation_response
        user_id = serializer.validated_data.get('user_id')

        cv, error_response = _get_latest_cv_for_user(user_id, logger)
        if error_response:
            return error_response
        try:
            cv_text, method_used, extracted_cv_id, filename = extract_text_from_cv(cv)
            if not cv_text:
                logger.warning(f"Не вдалося видобути текст з CV {cv.id} для користувача {user_id}")
                return Response({'error': 'Не вдалося видобути текст з резюме.'}, status=status.HTTP_400_BAD_REQUEST)

            ai_extracted_data = analyze_cv_with_ai(cv.id, user_id, cv_text_override=cv_text)
            response_serializer = AnalyzeCVResponseSerializer(data=ai_extracted_data)
            if response_serializer.is_valid():
                logger.info(f"Аналіз CV {cv.id} для користувача {user_id} успішно завершено.")
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:
                logger.warning(
                    f"ШІ повернув недійсні дані для CV {cv.id} користувача {user_id}: {response_serializer.errors}")
                return Response({"error": "ШІ повернув недійсні дані"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ValidationError as e:
            logger.warning(f"Помилка валідації при аналізі CV для користувача {user_id}: {e.message}")
            if "не знайдено" in str(e) or "видобути текст" in str(e):
                return Response({'error': e.message}, status=status.HTTP_404_NOT_FOUND)
            return Response({'error': e.message}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Неочікувана помилка при аналізі CV для користувача {user_id}: {e}", exc_info=True)
            return Response({'error': 'Внутрішня помилка сервера'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GetDownloadLinkView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        logger.info(f"Отримано POST запит на /api/cvs/get-download-link/ від {request.META.get('REMOTE_ADDR')}")
        logger.debug(f"Тіло запиту: {request.data}")

        serializer = DownloadCVRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Недійсні дані запиту для GetDownloadLinkView: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data.get('user_id')
        requested_filename = serializer.validated_data.get('filename')

        logger.info(f"Шукаємо CV для user_id={user_id}, за ім'ям файлу: '{requested_filename}'")

        user_cvs = CV.objects.filter(user_id=user_id)
        cv = None
        for c in user_cvs:
            if basename(c.cv_file.name) == requested_filename:
                cv = c
                break

        if cv is None:
            try:
                cv = CV.objects.get(user_id=user_id, cv_file=requested_filename)
                logger.info(f"Знайдено CV за повним шляхом: {cv.cv_file.name}")
            except CV.DoesNotExist:
                logger.warning(
                    f"CV для user_id={user_id} з ім'ям файлу або шляхом '{requested_filename}' не знайдено серед {user_cvs.count()} CV.")
                logger.debug(f"Доступні шляхи для user_id={user_id}: {[basename(c.cv_file.name) for c in user_cvs]}")
                return Response({'error': 'CV не знайдено або файл не належить користувачеві.'},
                                status=status.HTTP_404_NOT_FOUND)
        else:
            logger.info(f"Знайдено CV за ім'ям файлу: {cv.cv_file.name}")

        file_path = cv.cv_file.path
        logger.info(f"Перевіряємо файл за повним шляхом: {file_path}")
        if not os.path.exists(file_path):
            logger.error(f"Файл CV '{file_path}' не знайдено на диску.")
            return Response({'error': 'Файл CV не знайдено на сервері.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            logger.info(f"Файл існує на диску: {file_path}")

        token = str(uuid.uuid4())
        cache_key = f"cv_download_token:{token}"
        cache.set(cache_key, file_path, timeout=300)
        logger.info(f"Токен {token} збережено в кеші для файлу: {file_path}")

        download_url = request.build_absolute_uri(f'/api/cvs/download-cv-file/{token}/').replace("http://", "https://")
        logger.info(
            f"Згенеровано одноразове посилання для завантаження CV '{cv.cv_file.name}' для користувача {user_id}. Посилання: {download_url}")
        return Response({'download_url': download_url}, status=status.HTTP_200_OK)
