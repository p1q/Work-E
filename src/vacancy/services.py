import logging
from django.db.models import Q
from vacancy.models import Vacancy
from cvs.models import CV
from cvs.service import analyze_cv_with_ai, extract_text_from_cv

logger = logging.getLogger(__name__)


def get_filtered_vacancies(user_cv: CV):
    try:
        if not user_cv.analyzed:
            logger.info(f"Резюме {user_cv.id} ще не аналізувалося. Ініціюється аналіз ШІ.")
            try:
                extracted_text, method_used, extracted_cv_id, filename = extract_text_from_cv(user_cv)
                if not extracted_text:
                    logger.error(f"Не вдалося видобути текст із резюме {user_cv.id}.")
                    return Vacancy.objects.none()

                ai_extracted_data = analyze_cv_with_ai(
                    user_cv.id,
                    user_cv.user.id if user_cv.user else None,
                    cv_text_override=extracted_text
                )
                logger.debug(f"Дані від ШІ отримано для резюме {user_cv.id}.")

                updatable_fields = [
                    'skills', 'languages', 'level', 'categories',
                    'countries', 'cities', 'is_office', 'is_remote',
                    'is_hybrid', 'willing_to_relocate',
                    'salary_min', 'salary_max', 'salary_currency'
                ]
                updated_fields_list = []
                for field_name in updatable_fields:
                    if field_name in ai_extracted_data:
                        setattr(user_cv, field_name, ai_extracted_data[field_name])
                        updated_fields_list.append(field_name)

                user_cv.analyzed = True
                updated_fields_list.append('analyzed')

                user_cv.save(update_fields=updated_fields_list)
                logger.info(f"Резюме {user_cv.id} успішно проаналізовано та оновлено в БД.")

                cv_data_for_filtering = ai_extracted_data

            except Exception as e:
                logger.error(f"Помилка аналізу ШІ резюме {user_cv.id}: {e}", exc_info=True)
                return Vacancy.objects.none()
        else:
            logger.info(f"Резюме {user_cv.id} вже проаналізовано. Використовуються дані з БД.")
            cv_data_for_filtering = {
                "skills": getattr(user_cv, 'skills', []),
                "languages": getattr(user_cv, 'languages', []),
                "level": getattr(user_cv, 'level', None),
                "categories": getattr(user_cv, 'categories', []),
                "countries": getattr(user_cv, 'countries', []),
                "cities": getattr(user_cv, 'cities', []),
                "is_office": getattr(user_cv, 'is_office', None),
                "is_remote": getattr(user_cv, 'is_remote', None),
                "is_hybrid": getattr(user_cv, 'is_hybrid', None),
                "willing_to_relocate": getattr(user_cv, 'willing_to_relocate', None),
                "salary_min": getattr(user_cv, 'salary_min', None),
                "salary_max": getattr(user_cv, 'salary_max', None),
                "salary_currency": getattr(user_cv, 'salary_currency', None),
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
