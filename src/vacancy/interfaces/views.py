import logging

from django.db.models import Q
from drf_spectacular.utils import extend_schema
from openapi.service import extract_vacancy_data
from rest_framework import serializers
from rest_framework import status, generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from vacancy.models import Vacancy

from src.schemas.vacancy import (VACANCY_LIST_RESPONSE, VACANCY_DETAIL_RESPONSE, VACANCY_DELETE_RESPONSE)
from src.vacancy.interfaces.serializers import VacancySerializer


class CreateVacancyRequestSerializer(serializers.Serializer):
    vacancy_text = serializers.CharField(required=True, help_text="Сирий текст вакансії для обробки ШІ.")


class VacancyListCreateView(generics.ListCreateAPIView):
    queryset = Vacancy.objects.all()
    serializer_class = VacancySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [AllowAny]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    @extend_schema(responses={200: VACANCY_LIST_RESPONSE}, )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Створити нову вакансію з необробленого тексту",
        description="Приймає сирий текст вакансії, обробляє його ШІ для видобування структурованих даних, нормалізує дані та зберігає вакансію.",
        request=CreateVacancyRequestSerializer,
        responses={
            201: VACANCY_DETAIL_RESPONSE,
            400: "Помилка в запиті або даних вакансії",
            500: "Помилка сервера під час обробки тексту або взаємодії з ШІ",
            503: "Сервіс ШІ недоступний"
        }
    )
    def create(self, request, *args, **kwargs):
        logger = logging.getLogger(__name__)

        serializer = CreateVacancyRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.warning(f"Неправильні дані у запиті на створення вакансії: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        vacancy_text = serializer.validated_data.get('vacancy_text')

        if not vacancy_text:
            logger.warning("Не надано тексту вакансії у запиті.")
            return Response({'error': 'Текст вакансії є обов\'язковим.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            logger.info("Відправка тексту вакансії до ШІ для обробки.")
            ai_extracted_data = extract_vacancy_data(description_text=vacancy_text)

            if not ai_extracted_data:
                logger.error("ШІ не повернув дані для вакансії.")
                return Response({'error': 'Не вдалося отримати структуровані дані від ШІ.'},
                                status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            logger.debug(f"Дані, отримані від ШІ: {ai_extracted_data}")

            vacancy_serializer = VacancySerializer(data=ai_extracted_data)

            if vacancy_serializer.is_valid():
                vacancy = vacancy_serializer.save()
                logger.info(f"Вакансія '{vacancy.title}' (ID: {vacancy.id}) успішно створена з обробленого тексту.")
                return Response(vacancy_serializer.data, status=status.HTTP_201_CREATED)
            else:
                logger.warning(f"Дані від ШІ не пройшли валідацію: {vacancy_serializer.errors}")
                return Response(
                    {
                        'error': 'Дані, отримані від ШІ, не відповідають формату вакансії. Можливо, текст був нерозпізнаний.',
                        'details': vacancy_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"Несподівана помилка під час створення вакансії: {e}", exc_info=True)
            return Response(
                {'error': 'Внутрішня помилка сервера під час обробки вакансії.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VacancyRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    queryset = Vacancy.objects.all()
    serializer_class = VacancySerializer

    def get_permissions(self):
        if self.request.method == 'GET':
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @extend_schema(responses={200: VACANCY_DETAIL_RESPONSE}, )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(responses={204: VACANCY_DELETE_RESPONSE}, )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class VacancyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user_cv = CV.objects.filter(user=request.user).first()
        if not user_cv:
            return Response({"error": "CV not found"}, status=400)

        languages_filter = Q()
        if user_cv.languages:
            for language in user_cv.languages:
                languages_filter &= Q(languages__contains=[language['language']])

        level_filter = Q()
        if user_cv.level:
            level_filter &= Q(level=user_cv.level)

        categories_filter = Q()
        if user_cv.categories:
            categories_filter &= Q(categories__contains=[user_cv.categories[0]])

        location_filter = Q()
        if user_cv.countries and user_cv.cities:
            location_filter &= Q(countries__in=user_cv.countries, cities__in=user_cv.cities)

        salary_filter = Q()
        if user_cv.salary_min and user_cv.salary_max:
            salary_filter &= Q(salary_min__gte=user_cv.salary_min, salary_max__lte=user_cv.salary_max)

        vacancies = Vacancy.objects.filter(
            languages_filter & level_filter & categories_filter & location_filter & salary_filter
        )

        serializer = VacancySerializer(vacancies, many=True)
        return Response(serializer.data)
