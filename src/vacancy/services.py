from django.db.models import Q
from .models import Vacancy
from decimal import Decimal

LANGUAGE_LEVELS = {
    'A1': 1,
    'A2': 2,
    'B1': 3,
    'B2': 4,
    'C1': 5,
    'C2': 6
}

def convert_to_usd(amount, currency):
    if not amount or not currency:
        return None

    if currency == 'USD':
        return Decimal(amount)
    elif currency == 'EUR':
        return Decimal(amount) * Decimal('1.07')
    elif currency == 'UAH':
        return Decimal(amount) / Decimal('36.9')
    return None


def get_filtered_vacancies(user_cv):
    filters = Q()

    # 1. Фильтрация по языкам
    if hasattr(user_cv, 'languages') and user_cv.languages:
        language_filter = Q()
        for cv_lang in user_cv.languages:
            cv_lang_name = cv_lang.get("language")
            cv_lang_level = cv_lang.get("level")

            if not cv_lang_name or not cv_lang_level:
                continue

            if cv_lang_level in LANGUAGE_LEVELS:
                cv_level_value = LANGUAGE_LEVELS[cv_lang_level]

                # Фильтрация вакансий по языкам и уровням
                language_filter |= Q(languages__language=cv_lang_name,
                                     languages__level__gte=cv_level_value - 1)
        if language_filter:
            filters &= language_filter

    # 2. Фильтрация по уровню
    if hasattr(user_cv, 'level') and user_cv.level:
        filters &= Q(level=user_cv.level)

    # 3. Фильтрация по категориям
    if hasattr(user_cv, 'categories') and user_cv.categories:
        primary_category = user_cv.categories[0] if len(user_cv.categories) > 0 else None
        if primary_category:
            filters &= Q(categories__contains=[primary_category])

    # 4. Фильтрация по локации
    location_filter = Q()

    # Учитываем отдалённую работу
    if getattr(user_cv, 'is_remote', True) != False:
        location_filter |= Q(is_remote=True)

    if getattr(user_cv, 'willing_to_relocate', False):
        # Нет дополнительных ограничений для релокации
        pass
    else:
        if getattr(user_cv, 'cities', None):
            location_filter |= Q(cities__overlap=user_cv.cities)
        if getattr(user_cv, 'countries', None):
            location_filter |= Q(countries__overlap=user_cv.countries)

    # Исключаем отдалённые вакансии, если пользователь явно не хочет работать удалённо
    if getattr(user_cv, 'is_remote', None) is False:
        location_filter &= ~Q(is_remote=True)

    # Добавляем гибридные вакансии, если пользователь готов работать в офисе
    if getattr(user_cv, 'is_office', None) is True and getattr(user_cv, 'cities', None):
        location_filter |= Q(is_hybrid=True, cities__overlap=user_cv.cities)

    if location_filter:
        filters &= location_filter

    # 5. Фильтрация по зарплате
    if (hasattr(user_cv, 'salary_min') and hasattr(user_cv, 'salary_max') and
            hasattr(user_cv, 'salary_currency') and
            user_cv.salary_min is not None and user_cv.salary_max is not None and user_cv.salary_currency):

        cv_min_usd = convert_to_usd(user_cv.salary_min, user_cv.salary_currency)
        cv_max_usd = convert_to_usd(user_cv.salary_max, user_cv.salary_currency)

        if cv_min_usd is not None and cv_max_usd is not None:
            tolerance = Decimal('0.20')
            lower_bound = cv_min_usd * (1 - tolerance)
            upper_bound = cv_max_usd * (1 + tolerance)

            filters &= Q(salary_min__lte=upper_bound, salary_max__gte=lower_bound)

    # Выполняем запрос с фильтрацией
    vacancies = Vacancy.objects.filter(filters)

    return vacancies
