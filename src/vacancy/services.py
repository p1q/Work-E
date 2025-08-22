import logging

from cvs.models import CV
from django.db.models import Q
from vacancy.models import Vacancy

logger = logging.getLogger(__name__)


def get_filtered_vacancies(user_cv: CV):
    try:
        cv_data_for_filtering = {
            "skills": user_cv.skills or [],
            "languages": user_cv.languages or [],
            "level": user_cv.level,
            "categories": user_cv.categories or [],
            "countries": user_cv.countries or [],
            "cities": user_cv.cities or [],
            "is_office": user_cv.is_office,
            "is_remote": user_cv.is_remote,
            "is_hybrid": user_cv.is_hybrid,
            "willing_to_relocate": user_cv.willing_to_relocate,
            "salary_min": user_cv.salary_min,
            "salary_max": user_cv.salary_max,
            "salary_currency": user_cv.salary_currency,
        }

        # --- ФІЛЬТР 1: Категорії ---
        filters = Q()
        if cv_data_for_filtering.get("categories"):
            filters &= Q(categories__overlap=cv_data_for_filtering["categories"])
        else:
            logger.info("У резюме не вказано категорій. Повернено порожній список.")
            return Vacancy.objects.none()

        # --- ФІЛЬТР 2: Мови ---
        if cv_data_for_filtering.get("languages"):
            languages_filter = Q()
            for lang_data in cv_data_for_filtering["languages"]:
                lang = lang_data.get("language")
                level = lang_data.get("level")
                if lang:
                    if level:
                        languages_filter |= Q(languages__contains=[{"language": lang, "level": level}])
                    else:
                        languages_filter |= Q(languages__contains=[{"language": lang}])
            if languages_filter:
                filters &= languages_filter

        # --- ФІЛЬТР 3: Рівень досвіду ---
        if cv_data_for_filtering.get("level"):
            filters &= Q(level=cv_data_for_filtering["level"])

        # --- ФІЛЬТР 4: Локація ---
        location_filter = Q()
        is_remote_needed = cv_data_for_filtering.get("is_remote")
        willing_to_relocate = cv_data_for_filtering.get("willing_to_relocate")
        cities = cv_data_for_filtering.get("cities")
        countries = cv_data_for_filtering.get("countries")

        if is_remote_needed:
            location_filter |= Q(is_remote=True)
        if willing_to_relocate is not False:
            if cities:
                location_filter |= Q(cities__overlap=cities)
            if countries:
                location_filter |= Q(countries__overlap=countries)

        if location_filter:
            filters &= location_filter

        vacancies = Vacancy.objects.filter(filters)

        # --- ФІЛЬТР 5: Зарплата ---
        salary_min = cv_data_for_filtering.get("salary_min")
        salary_max = cv_data_for_filtering.get("salary_max")
        salary_currency = cv_data_for_filtering.get("salary_currency")

        salary_filter = Q()
        if salary_min is not None:
            salary_filter &= Q(salary_max__gte=salary_min)
        if salary_max is not None:
            salary_filter &= Q(salary_min__lte=salary_max)
        if salary_currency:
            salary_filter &= (Q(salary_currency=salary_currency) | Q(salary_currency__isnull=True))

        if salary_filter:
            vacancies = vacancies.filter(salary_filter)

        logger.info(f"Знайдено {vacancies.count()} вакансій для резюме {user_cv.id} після фільтрації.")

        return vacancies

    except Exception as e:
        logger.error(f"Помилка фільтрації вакансій для резюме {user_cv.id}: {e}", exc_info=True)
        return Vacancy.objects.none()
