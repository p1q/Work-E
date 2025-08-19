import logging
import random
from decimal import Decimal

from cvs.models import CV
from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from vacancy.models import Vacancy

User = get_user_model()
logger = logging.getLogger(__name__)

EXCHANGE_RATES = {
    'UAH': 0.027,
    'EUR': 1.07,
    'USD': 1.0
}


def convert_to_usd(amount, currency):
    if currency not in EXCHANGE_RATES:
        return None
    return amount * Decimal(str(EXCHANGE_RATES[currency]))


class MatchesForUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        user_id = kwargs.get('user_id')
        if user_id is None:
             return Response({'error': 'user_id is required'}, status=400)
        try:
             user_id = int(user_id)
        except (ValueError, TypeError):
             return Response({'error': 'Invalid user_id'}, status=400)

        logger.info(f"Отримання матчів для користувача {user_id}")

        # 1. Отримуємо користувача
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"Користувача з ID {user_id} не знайдено")
            return Response({'error': f'Користувача з ID {user_id} не знайдено.'}, status=404)

        # 2. Отримуємо останнє резюме користувача
        user_cv = CV.objects.filter(user=user).order_by('-uploaded_at').first()
        if not user_cv:
            logger.info(f"CV для користувача {user_id} не знайдено")
            return Response({'error': f'Резюме для користувача з ID {user_id} не знайдено.'}, status=404)

        # 3. Формуємо запит до вакансій
        vacancies = Vacancy.objects.all()

        # 4. Фільтрація за мовами
        if user_cv.languages and len(user_cv.languages) > 0:
            language_filter = Q()
            for lang_info in user_cv.languages:
                language = lang_info.get('language')
                level = lang_info.get('level')

                if language and level:
                    # Створюємо фільтр для кожної мови в резюме
                    lang_q = Q(languages__contains=[{'language': language}])

                    # Визначаємо мінімальний прийнятний рівень (на 1 менше)
                    level_order = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
                    try:
                        level_index = level_order.index(level)
                        min_acceptable_level_index = max(0, level_index - 1)
                        acceptable_levels = level_order[min_acceptable_level_index:]

                        # Додаємо умову на рівень мови
                        lang_q &= Q(languages__contains=[{'language': language, 'level': l} for l in acceptable_levels])
                    except ValueError:
                        # Якщо рівень не в стандартному списку, пропускаємо фільтрацію за рівнем для цієї мови
                        pass

                    language_filter |= lang_q

            if language_filter:
                vacancies = vacancies.filter(language_filter)

        # 5. Фільтрація за рівнем
        if getattr(user_cv, 'level', None):
            vacancies = vacancies.filter(level=user_cv.level)

        # 6. Фільтрація за категоріями
        if getattr(user_cv, 'categories', None) and len(user_cv.categories) > 0:
            primary_category = user_cv.categories[0]
            vacancies = vacancies.filter(categories__contains=[primary_category])

        # 7. Фільтрація за локацією та релокацією
        location_filter = Q()

        # Включаємо віддалені вакансії, якщо користувач не вказав небажання працювати віддалено
        if getattr(user_cv, 'is_remote', True) != False:  # Якщо не вказано False, включаємо віддалені
            location_filter |= Q(is_remote=True)

        # Якщо готовий до релокейту - включаємо все
        if getattr(user_cv, 'willing_to_relocate', False):
            location_filter |= Q()  # Не додаємо обмежень
        else:
            # Якщо не готовий до релокейту, перевіряємо точне співпадіння локації
            if getattr(user_cv, 'cities', None):
                location_filter |= Q(cities__overlap=user_cv.cities)
            if getattr(user_cv, 'countries', None):
                location_filter |= Q(countries__overlap=user_cv.countries)

            # Для гібридних вакансій також перевіряємо співпадіння локації
            if getattr(user_cv, 'is_hybrid', False):
                if getattr(user_cv, 'cities', None):
                    location_filter |= Q(is_hybrid=True, cities__overlap=user_cv.cities)
                if getattr(user_cv, 'countries', None):
                    location_filter |= Q(is_hybrid=True, countries__overlap=user_cv.countries)

        vacancies = vacancies.filter(location_filter)

        # 8. Фільтрація за зарплатою
        if (getattr(user_cv, 'salary_min', None) and getattr(user_cv, 'salary_max', None) and
                getattr(user_cv, 'salary_currency', None)):

            cv_min_usd = convert_to_usd(user_cv.salary_min, user_cv.salary_currency)
            cv_max_usd = convert_to_usd(user_cv.salary_max, user_cv.salary_currency)

            if cv_min_usd is not None and cv_max_usd is not None:
                # Розраховуємо діапазон з урахуванням 20% відхилення
                tolerance = Decimal('0.20')
                lower_bound = cv_min_usd * (1 - tolerance)
                upper_bound = cv_max_usd * (1 + tolerance)

                # Фільтруємо вакансії, де вказана зарплата
                salary_filter = (
                        Q(salary_min__isnull=False) &
                        Q(salary_max__isnull=False) &
                        Q(salary_currency__isnull=False)
                )

                # Отримуємо вакансії з вказаною зарплатою
                vacancies_with_salary = vacancies.filter(salary_filter)

                # Фільтруємо по відповідності діапазону з урахуванням валюти
                matching_vacancies_ids = []
                for vacancy in vacancies_with_salary:
                    vacancy_min_usd = convert_to_usd(vacancy.salary_min, vacancy.salary_currency)
                    vacancy_max_usd = convert_to_usd(vacancy.salary_max, vacancy.salary_currency)

                    if (vacancy_min_usd is not None and vacancy_max_usd is not None and
                            vacancy_max_usd >= lower_bound and vacancy_min_usd <= upper_bound):
                        matching_vacancies_ids.append(vacancy.id)

                # Отримуємо вакансії без вказаної зарплати
                vacancies_without_salary = vacancies.exclude(salary_filter)

                # Об'єднуємо результати
                vacancies = Vacancy.objects.filter(
                    Q(id__in=matching_vacancies_ids) |
                    Q(id__in=vacancies_without_salary.values_list('id', flat=True))
                )

        matches = []
        for vacancy in vacancies[:10]:
            match = {
                'vacancy_id': vacancy.id,
                'title': vacancy.title,
                'link': vacancy.link,
                'score': round(random.uniform(50, 100), 2),
                'match_quality': random.choice(['Low', 'Medium', 'High']),
                'skills_match': round(random.uniform(0, 100), 2),
                'tools_match': round(random.uniform(0, 100), 2),
                'responsibilities_match': round(random.uniform(0, 100), 2),
                'languages_match': round(random.uniform(0, 100), 2),
                'location_match': round(random.uniform(0, 100), 2),
                'salary_match': round(random.uniform(0, 100), 2),
            }
            matches.append(match)

        return Response(matches)
