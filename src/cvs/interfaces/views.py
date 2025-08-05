import io
import json
import logging
import os

import google.generativeai as genai
import pdfplumber
import requests
from django.conf import settings
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from dotenv import load_dotenv
from drf_spectacular.utils import extend_schema, OpenApiResponse
from rest_framework import generics
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from src.schemas.cvs import (CV_LIST_RESPONSE, CV_CREATE, CV_DETAIL_RESPONSE, CV_DELETE_RESPONSE, CV_BY_EMAIL,
                             CV_LAST_BY_EMAIL, CV_LIST_PARAMETERS)
from .serializers import AnalyzeCVRequestSerializer, AnalyzeCVResponseSerializer
from .serializers import CVSerializer, CoverLetterSerializer, CVGenerationSerializer, User
from .serializers import ExtractTextFromCVRequestSerializer, ExtractTextFromCVResponseSerializer
from ..models import CV

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


@extend_schema(
    tags=["CVs"],
    summary="Видобути текст із останнього CV користувача",
    description="Отримує останнє завантажене CV користувача за його ID і видобуває текст за допомогою pdfplumber.",
    request=ExtractTextFromCVRequestSerializer,
    responses={
        200: ExtractTextFromCVResponseSerializer,
        400: OpenApiResponse(description='Помилка в запиті, даних користувача/CV або файлі PDF'),
        404: OpenApiResponse(description='Користувач або CV не знайдено'),
        500: OpenApiResponse(description='Помилка сервера при обробці PDF'),
    }
)
class ExtractTextFromCVView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    def post(self, request):
        logger = logging.getLogger(__name__)
        serializer = ExtractTextFromCVRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Недійсні дані для видобування тексту: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data.get('user_id')

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.warning(f"Користувач із id {user_id} не знайдений для видобування тексту")
            return Response({'error': f'Користувача з ID {user_id} не знайдено.'}, status=status.HTTP_404_NOT_FOUND)

        cv = CV.objects.filter(user=user).order_by('-uploaded_at').first()
        if not cv:
            logger.info(f"CV для користувача {user_id} не знайдено")
            return Response({'error': f'Резюме для користувача з ID {user_id} не знайдено.'},
                            status=status.HTTP_404_NOT_FOUND)

        if not cv.cv_file:
            logger.warning(f"До CV {cv.id} для користувача {user_id} не прикріплений файл")
            return Response({'error': f'До файлу резюме {cv.id} не прикріплений PDF.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            cv_file = cv.cv_file.open('rb')
            pdf_content = cv_file.read()
            cv_file.close()

            pdf_stream = io.BytesIO(pdf_content)

            extracted_text = ""
            method_used = "pdf_text"

            try:
                with pdfplumber.open(pdf_stream) as pdf:
                    text_parts = []
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            cleaned_page_text = '\n'.join(line for line in page_text.splitlines() if line.strip())
                            text_parts.append(cleaned_page_text)
                    extracted_text = "\n\n".join(text_parts).strip()
                    logger.debug(f"Текст видобуто за допомогою pdfplumber з CV {cv.id}")
            except pdfplumber.pdf.PSException as e:
                logger.error(f"PSException під час використання pdfplumber для CV {cv.id}: {e}", exc_info=True)
                return Response(
                    {'error': f'Помилка обробки PDF файлу (можливо, пошкоджений або нестандартний формат): {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                logger.error(f"Неочікувана помилка під час використання pdfplumber для CV {cv.id}: {e}", exc_info=True)
                extracted_text = ""

            if extracted_text.strip():
                response_data = {
                    'text': extracted_text,
                    'method': method_used,
                    'cv_id': cv.id,
                    'filename': cv.filename
                }
                response_serializer = ExtractTextFromCVResponseSerializer(response_data)
                logger.info(f"Успішно видобуто текст (метод: {method_used}) з CV {cv.id} для користувача {user_id}")
                return Response(response_serializer.data, status=status.HTTP_200_OK)
            else:
                logger.warning(f"Не вдалося видобути текст із CV {cv.id} для користувача {user_id}")
                return Response(
                    {
                        'error': 'Не вдалося видобути текст із PDF файлу. '
                                 'Файл може бути сканованим (без текстового шару), порожнім або пошкодженим.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

        except FileNotFoundError:
            file_path = cv.cv_file.path if cv.cv_file else "Шлях невідомий"
            logger.error(f"Файл CV для CV {cv.id} не знайдено на диску за шляхом: {file_path}")
            return Response({'error': f'Файл резюме не знайдено на сервері за шляхом: {file_path}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            logger.error(f"Неочікувана помилка під час видобування тексту для CV {cv.id}, користувач {user_id}: {e}",
                         exc_info=True)
            return Response(
                {'error': f'Сталася неочікувана помилка під час обробки файлу резюме: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@extend_schema(
    tags=["CVs"],
    summary="Проаналізувати резюме користувача за допомогою ШІ",
    description="Отримує останнє резюме користувача, видобуває з нього текст, потім надсилає текст до ШІ для аналізу та видобування структурованих даних.",
    request=AnalyzeCVRequestSerializer,
    responses={
        200: AnalyzeCVResponseSerializer,
        400: OpenApiResponse(description='Помилка в запиті, даних користувача/CV або файлі PDF'),
        404: OpenApiResponse(description='Користувач або CV не знайдено'),
        500: OpenApiResponse(description='Помилка сервера при обробці PDF або взаємодії з ШІ'),
        503: OpenApiResponse(description='Сервіс ШІ недоступний'),
    }
)
class AnalyzeCVView(APIView):
    permission_classes = [AllowAny]  # Або IsAuthenticated
    parser_classes = [JSONParser]

    def post(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)
        serializer = AnalyzeCVRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Недійсні дані для аналізу резюме: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_id = serializer.validated_data.get('user_id')

        # --- 1. Видобути текст резюме ---
        temp_request = type('TempRequest', (), {
            'data': {'user_id': user_id},
            'user': request.user
        })()

        extract_view = ExtractTextFromCVView()
        extract_response = extract_view.post(temp_request)

        if extract_response.status_code != status.HTTP_200_OK:
            logger.warning(
                f"Не вдалося видобути текст для аналізу CV користувача {user_id}. Статус: {extract_response.status_code}")
            return Response(extract_response.data, status=extract_response.status_code)

        # Отримуємо текст резюме
        cv_text = extract_response.data.get('text')
        cv_id = extract_response.data.get('cv_id')
        filename = extract_response.data.get('filename')

        if not cv_text:
            logger.error(f"Видобуток тексту успішний, але текст порожній для CV {cv_id} користувача {user_id}")
            return Response({'error': 'Видобутий текст резюме порожній.'}, status=status.HTTP_400_BAD_REQUEST)

        logger.debug(f"Успішно видобуто текст з CV {cv_id} користувача {user_id} для подальшого аналізу.")

        # --- 2. Підготувати запит до ШІ ---
        prompt = f"""
        Analyze the following candidate resume/CV and extract the specified parameters.
        Provide the result as a JSON object with the exact keys listed below.
        If a parameter cannot be determined or is not mentioned, leave its value as null or an empty list/object.

        Parameters to extract:
        1. skills: Array of strings. Key technical skills,  technologies, specific tools, and competencies mentioned (e.g., ["Python", "Django", "Git", "Docker", "AWS", "REST API"]).
        2. languages: Array of objects. Languages mentioned, including proficiency level if mentioned. Format: [{{"language": "English", "level": "B2"}}, ...]. If no level, use null for level.
        3. location: String. The candidate's location or preferred work arrangement mentioned (e.g., "Kyiv", "Lviv", "Odesa"). Only city, nothing else!
        4. salary_range: String. The candidate's expected salary range mentioned, in the format "min-max currency" (e.g., "50000-70000 UAH", "60000 EUR", "Negotiable"). If not specified, null.
        5. level: String. The candidate's experience level implied (e.g., "Junior", "Middle", "Senior", "Lead"). If not specified, null.
        6. english_level_required: String. The candidate's stated or implied English proficiency level (e.g., "A1", "A2", "B1", "B2", "C1", "C2"). If not specified, null.
        7. is_remote: Boolean. Is the candidate open to remote work? (true/false). If not specified or unclear, null.
        8. is_hybrid: Boolean. Is the candidate open to hybrid work? (true/false). If not specified or unclear, null.
        9. willing_to_relocate: Boolean. Is the candidate willing to relocate? (true/false). If not specified or unclear, null.
        10. responsibilities: Array of strings. Key responsibilities or achievements listed in previous roles (e.g., ["Developed web applications", "Led a team of 5 developers"]).

        Candidate Resume/CV Text:
        {cv_text}

        JSON Output:
        """

        ai_url = getattr(settings, 'OPENAPI_AI_URL')

        ai_request_data = {
            "model": "qwen-max-latest",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }

        # --- 3. Надіслати запит до ШІ ---
        try:
            logger.info(f"Надсилання запиту до ШІ для аналізу CV {cv_id} користувача {user_id}...")
            ai_response = requests.post(ai_url, json=ai_request_data, timeout=60)
            ai_response.raise_for_status()

            ai_response_data = ai_response.json()
            logger.debug(f"Отримано відповідь від ШІ для CV {cv_id}")

            # --- 4. Обробити відповідь ШІ ---
            ai_content = ""
            if 'choices' in ai_response_data and len(ai_response_data['choices']) > 0:
                ai_content = ai_response_data['choices'][0]['message'].get('content', '')
            elif 'message' in ai_response_data:
                ai_content = ai_response_data['message'].get('content', '')
            else:
                ai_content = ai_response.text

            if not ai_content:
                logger.error(f"Відповідь ШІ для CV {cv_id} порожня.")
                return Response({'error': 'Отримано порожню відповідь від ШІ.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            ai_content_clean = ai_content.strip()
            if ai_content_clean.startswith("```json"):
                ai_content_clean = ai_content_clean[7:]
            if ai_content_clean.endswith("```"):
                ai_content_clean = ai_content_clean[:-3]

            ai_parsed_data = json.loads(ai_content_clean)

            output_serializer = AnalyzeCVResponseSerializer(data=ai_parsed_data)
            if not output_serializer.is_valid():
                logger.warning(f"ШІ повернув недійсні дані для CV {cv_id}: {output_serializer.errors}")
                return Response(
                    {
                        'error': 'ШІ повернув дані, які не відповідають очікуваному формату.',
                        'details': output_serializer.errors,
                        'raw_ai_response': ai_parsed_data
                    },
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            logger.info(f"Успішно проаналізовано CV {cv_id} користувача {user_id} за допомогою ШІ.")
            return Response(output_serializer.validated_data, status=status.HTTP_200_OK)

        except json.JSONDecodeError as e:
            logger.error(f"Помилка парсингу JSON від ШІ для CV {cv_id}: {e}. Відповідь: {ai_content}", exc_info=True)
            return Response(
                {
                    'error': 'Помилка обробки відповіді від ШІ (недійсний JSON).',
                    'raw_ai_response': ai_content
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except requests.exceptions.Timeout:
            logger.error(f"Таймаут при з'єднанні з ШІ для CV {cv_id}.")
            return Response({'error': 'Сервіс ШІ не відповідає (таймаут).'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except requests.exceptions.ConnectionError:
            logger.error(f"Помилка з'єднання з ШІ для CV {cv_id}.")
            return Response(
                {'error': 'Неможливо з\'єднатися з сервісом ШІ.'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except requests.exceptions.RequestException as e:
            logger.error(f"Помилка HTTP-запиту до ШІ для CV {cv_id}: {e}", exc_info=True)
            return Response({'error': f'Помилка взаємодії з сервісом ШІ: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.error(f"Несподівана помилка під час аналізу CV {cv_id} користувача {user_id} ШІ: {e}", exc_info=True)
            return Response({'error': f'Сталася несподівана помилка: {str(e)}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
