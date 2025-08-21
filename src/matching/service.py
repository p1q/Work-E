import json
import logging

from cvs.models import CV
from django.contrib.auth import get_user_model
from vacancy.models import Vacancy

from src.openapi.service import call_openapi_ai

logger = logging.getLogger(__name__)

User = get_user_model()

WEIGHTS = {
    'skills': 0.25,
    'tools': 0.15,
    'responsibilities': 0.20,
    'languages': 0.15,
    'location': 0.15,
    'salary': 0.10,
}


def calculate_match_percentage(cv_data: dict, vacancy_data: dict, vacancy: Vacancy, user_cv: CV) -> dict:
    """Розраховує відсоток співпадіння між CV та вакансією"""

    def calculate_skills_match(cv_skills, vacancy_skills):
        if not vacancy_skills:
            return 100.0
        matched = sum(1 for skill in vacancy_skills if any(
            v_skill.lower() in skill.lower() or skill.lower() in v_skill.lower() for v_skill in cv_skills))
        return (matched / len(vacancy_skills)) * 100 if vacancy_skills else 0

    def calculate_tools_match(cv_tools, vacancy_tools):
        if not vacancy_tools:
            return 100.0
        matched = sum(1 for tool in vacancy_tools if
                      any(v_tool.lower() in tool.lower() or tool.lower() in v_tool.lower() for v_tool in cv_tools))
        return (matched / len(vacancy_tools)) * 100 if vacancy_tools else 0

    def calculate_responsibilities_match(cv_responsibilities, vacancy_responsibilities):
        if not vacancy_responsibilities:
            return 100.0
        matched = sum(1 for resp in vacancy_responsibilities if any(
            v_resp.lower() in resp.lower() or resp.lower() in v_resp.lower() for v_resp in cv_responsibilities))
        return (matched / len(vacancy_responsibilities)) * 100 if vacancy_responsibilities else 0

    def calculate_languages_match(cv_languages, vacancy_languages):
        if not vacancy_languages:
            return 100.0

        matched = 0
        total_weight = 0

        for v_lang in vacancy_languages:
            v_lang_name = v_lang.get("language", "").lower()
            v_lang_level = v_lang.get("level", "")

            # Знайти мову в CV
            cv_lang_item = next((item for item in cv_languages if item.get("language", "").lower() == v_lang_name),
                                None)

            if cv_lang_item:
                cv_lang_level = cv_lang_item.get("level", "")
                # Якщо рівень вказаний в обох, перевіряємо відповідність
                if v_lang_level and cv_lang_level:
                    # Створимо просте відображення рівнів
                    level_mapping = {"A1": 1, "A2": 2, "B1": 3, "B2": 4, "C1": 5, "C2": 6}
                    v_level_num = level_mapping.get(v_lang_level, 0)
                    cv_level_num = level_mapping.get(cv_lang_level, 0)

                    # Якщо рівень CV >= рівня вакансії, повне співпадіння
                    if cv_level_num >= v_level_num:
                        matched += 1
                    # Якщо різниця в 1 рівень, часткове співпадіння
                    elif cv_level_num >= v_level_num - 1:
                        matched += 0.5

                else:
                    # Якщо рівень не вказаний в одному з них, вважаємо співпадінням
                    matched += 1

            total_weight += 1

        return (matched / total_weight) * 100 if total_weight > 0 else 0

    def calculate_location_match(user_cv, vacancy):
        # Якщо вакансія віддалена, співпадіння 100%
        if vacancy.is_remote:
            return 100.0

        # Якщо в користувача не вказано локацію, повертаємо 50%
        if not (getattr(user_cv, 'cities', None) or getattr(user_cv, 'countries', None)):
            return 50.0

        # Перевіряємо співпадіння міст
        if getattr(user_cv, 'cities', None) and getattr(vacancy, 'cities', None):
            if any(city in vacancy.cities for city in user_cv.cities):
                return 100.0

        # Перевіряємо співпадіння країн
        if getattr(user_cv, 'countries', None) and getattr(vacancy, 'countries', None):
            if any(country in vacancy.countries for country in user_cv.countries):
                return 100.0

        # Якщо часткове співпадіння (наприклад, країна співпадає, але місто ні)
        if getattr(user_cv, 'countries', None) and getattr(vacancy, 'countries', None):
            if any(country in vacancy.countries for country in user_cv.countries):
                return 70.0

        return 0.0

    def calculate_salary_match(user_cv, vacancy):
        # Якщо зарплата не вказана в одному з них, повертаємо 100%
        if not (getattr(user_cv, 'salary_min', None) is not None and
                getattr(user_cv, 'salary_max', None) is not None and
                getattr(vacancy, 'salary_min', None) is not None and
                getattr(vacancy, 'salary_max', None) is not None):
            return 100.0

        # Перевірка валюти
        if getattr(user_cv, 'salary_currency', None) != getattr(vacancy, 'salary_currency', None):
            # Тут можна додати конвертацію валют, але для простоти повернемо 50%
            return 50.0

        # Перевірка діапазонів
        cv_min, cv_max = user_cv.salary_min, user_cv.salary_max
        vac_min, vac_max = vacancy.salary_min, vacancy.salary_max

        # Якщо діапазони перетинаються
        if cv_max >= vac_min and cv_min <= vac_max:
            # Обчислюємо ступінь перетину
            overlap_min = max(cv_min, vac_min)
            overlap_max = min(cv_max, vac_max)
            overlap = overlap_max - overlap_min

            # Максимальний можливий перетин
            range_max = max(cv_max, vac_max) - min(cv_min, vac_min)

            if range_max > 0:
                return (overlap / range_max) * 100
            else:
                return 100.0
        else:
            # Якщо не перетинаються, розраховуємо відстань
            if cv_min > vac_max:
                gap = cv_min - vac_max
                # Чим більша пропастина, тим менший відсоток
                return max(0, 100 - (gap / ((cv_max + vac_min) / 2)) * 100)
            elif vac_min > cv_max:
                gap = vac_min - cv_max
                return max(0, 100 - (gap / ((vac_max + cv_min) / 2)) * 100)
            return 0.0

    # Отримуємо дані з CV та вакансії
    cv_skills = cv_data.get("skills", [])
    cv_tools = cv_data.get("tools", [])
    cv_responsibilities = cv_data.get("responsibilities", [])
    cv_languages = cv_data.get("languages", [])

    vacancy_skills = vacancy_data.get("skills", [])
    vacancy_tools = vacancy_data.get("tools", [])
    vacancy_responsibilities = vacancy_data.get("responsibilities", [])
    vacancy_languages = vacancy_data.get("languages", [])

    # Розраховуємо відсотки співпадіння для кожної категорії
    skills_match = calculate_skills_match(cv_skills, vacancy_skills)
    tools_match = calculate_tools_match(cv_tools, vacancy_tools)
    responsibilities_match = calculate_responsibilities_match(cv_responsibilities, vacancy_responsibilities)
    languages_match = calculate_languages_match(cv_languages, vacancy_languages)
    location_match = calculate_location_match(user_cv, vacancy)
    salary_match = calculate_salary_match(user_cv, vacancy)

    # Розраховуємо загальний відсоток з використанням вагових коефіцієнтів
    weighted_score = (
            skills_match * WEIGHTS['skills'] +
            tools_match * WEIGHTS['tools'] +
            responsibilities_match * WEIGHTS['responsibilities'] +
            languages_match * WEIGHTS['languages'] +
            location_match * WEIGHTS['location'] +
            salary_match * WEIGHTS['salary']
    )

    return {
        'skills_match': round(skills_match, 2),
        'tools_match': round(tools_match, 2),
        'responsibilities_match': round(responsibilities_match, 2),
        'languages_match': round(languages_match, 2),
        'location_match': round(location_match, 2),
        'salary_match': round(salary_match, 2),
        'score': round(weighted_score, 2)
    }
