import logging

from cvs.models import CV
from cvs.service import analyze_cv_with_ai, extract_text_from_cv
from django.core.exceptions import ValidationError
from django.db.models import Q
from vacancy.models import Vacancy

logger = logging.getLogger(__name__)


def get_filtered_vacancies(user_cv: CV):
    try:
        if not hasattr(user_cv, 'skills') or not user_cv.skills:
            logger.info(f"CV {user_cv.id} требует анализа ИИ.")

            try:
                extracted_text, method_used, extracted_cv_id, filename = extract_text_from_cv(user_cv)
                if not extracted_text:
                     logger.error(f"Не удалось извлечь текст из CV {user_cv.id}.")
                     return Vacancy.objects.none()
                logger.debug(f"Текст извлечен методом '{method_used}' из CV {extracted_cv_id} ({filename}).")
            except ValidationError as e:
                 logger.error(f"Ошибка извлечения текста из CV {user_cv.id}: {e}")
                 return Vacancy.objects.none()
            except Exception as e:
                 logger.error(f"Неожиданная ошибка при извлечении текста из CV {user_cv.id}: {e}", exc_info=True)
                 return Vacancy.objects.none()

            try:
                ai_extracted_data = analyze_cv_with_ai(user_cv.id, user_cv.user.id if user_cv.user else None, cv_text_override=extracted_text)
                if not ai_extracted_data:
                    logger.error(f"ИИ не вернул данные для CV {user_cv.id}.")
                    return Vacancy.objects.none()
                logger.debug(f"Данные от ИИ получены для CV {user_cv.id}.")
            except Exception as e:
                 logger.error(f"Ошибка анализа ИИ CV {user_cv.id}: {e}", exc_info=True)
                 return Vacancy.objects.none()

            cv_data_for_filtering = ai_extracted_data

        else:
            logger.info(f"CV {user_cv.id} уже содержит данные ИИ или не требует анализа.")
            cv_data_for_filtering = {
                "skills": getattr(user_cv, 'skills', []),
                "tools": getattr(user_cv, 'tools', []),
                "responsibilities": getattr(user_cv, 'responsibilities', []),
                "languages": getattr(user_cv, 'languages', []),
                 "level": getattr(user_cv, 'level', None),
                 "cities": getattr(user_cv, 'cities', []),
                 "countries": getattr(user_cv, 'countries', []),
                 "is_remote": getattr(user_cv, 'is_remote', None),
                 "willing_to_relocate": getattr(user_cv, 'willing_to_relocate', False),
                 "salary_min": getattr(user_cv, 'salary_min', None),
                 "salary_max": getattr(user_cv, 'salary_max', None),
                 "salary_currency": getattr(user_cv, 'salary_currency', None),
            }

    except Exception as e:
        logger.error(f"Ошибка подготовки данных CV {user_cv.id} для фильтрации: {e}", exc_info=True)
        return Vacancy.objects.none()


    try:
        filters = Q()

        language_filter = Q()
        cv_languages = cv_data_for_filtering.get("languages", [])
        for lang_info in cv_languages:
             cv_lang_name = lang_info.get('language')
             cv_level_value = lang_info.get('level')
             if cv_lang_name and cv_level_value:
                 language_filter |= Q(languages__contains=[{"language": cv_lang_name, "level": cv_level_value}])

        if language_filter:
            filters &= language_filter

        cv_level = cv_data_for_filtering.get("level")
        if cv_level:
            filters &= Q(level=cv_level)

        location_filter = Q()
        is_remote_preference = cv_data_for_filtering.get("is_remote")
        willing_to_relocate = cv_data_for_filtering.get("willing_to_relocate", False)
        cities = cv_data_for_filtering.get("cities", [])
        countries = cv_data_for_filtering.get("countries", [])

        if is_remote_preference is True:
            location_filter |= Q(is_remote=True)

        if willing_to_relocate:
            pass
        else:
            if cities:
                location_filter |= Q(cities__overlap=cities)
            if countries:
                location_filter |= Q(countries__overlap=countries)
            if is_remote_preference is False:
                 location_filter &= ~Q(is_remote=True)

        if location_filter:
            filters &= location_filter

        salary_min = cv_data_for_filtering.get("salary_min")
        salary_max = cv_data_for_filtering.get("salary_max")
        salary_currency = cv_data_for_filtering.get("salary_currency")

        if salary_min is not None and salary_max is not None and salary_currency:
             def convert_to_usd(amount, currency):
                 return amount
             cv_min_usd = convert_to_usd(salary_min, salary_currency)
             cv_max_usd = convert_to_usd(salary_max, salary_currency)
             if cv_min_usd is not None and cv_max_usd is not None:
                 tolerance = 0.20
                 lower_bound = cv_min_usd * (1 - tolerance)
                 upper_bound = cv_max_usd * (1 + tolerance)
                 filters &= Q(salary_min__lte=upper_bound, salary_max__gte=lower_bound)

        vacancies = Vacancy.objects.filter(filters)
        logger.info(f"Найдено {vacancies.count()} вакансий для CV {user_cv.id} после фильтрации.")
        return vacancies

    except Exception as e:
         logger.error(f"Ошибка фильтрации вакансий для CV {user_cv.id}: {e}", exc_info=True)
         return Vacancy.objects.none()
