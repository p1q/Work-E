import logging

from cvs.models import CV
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from vacancy.models import Vacancy

from src.matching.service import calculate_vacancy_matches_for_cv
from src.vacancy.services import get_filtered_vacancies

User = get_user_model()
logger = logging.getLogger(__name__)


class MatchesForUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        try:
            logger.info(f"Початок підбору вакансій для користувача {user_id}")
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                logger.warning(f"Користувач з ID {user_id} не знайдений.")
                return Response({'error': f'Користувач з ID {user_id} не знайдений.'}, status=404)

            user_cv = CV.objects.filter(user=user).order_by('-uploaded_at').first()
            if not user_cv:
                logger.info(f"Резюме для користувача {user_id} не знайдено")
                return Response({'error': f'Резюме для користувача з ID {user_id} не знайдено.'}, status=404)

            if not user_cv.analyzed:
                logger.info(f"Резюме {user_cv.id} користувача {user_id} ще не проаналізовано ШІ.")
                return Response({
                    'error': f'Резюме користувача з ID {user_id} ще не проаналізовано. Будь ласка, зачекайте завершення аналізу.'},
                    status=400)

            filtered_vacancies_queryset = get_filtered_vacancies(user_cv)
            logger.info(
                f"Отримано {filtered_vacancies_queryset.count()} вакансій після фільтрації для користувача {user_id}")

            matches = calculate_vacancy_matches_for_cv(user_cv, filtered_vacancies_queryset)
            logger.info(f"Розраховано {len(matches)} збігів для користувача {user_id}")
            return Response(matches)

        except Exception as e:
            logger.error(f"Несподівана помилка при підборі вакансій для користувача {user_id}: {e}", exc_info=True)
            return Response({'error': 'Внутрішня помилка сервера'}, status=500)
