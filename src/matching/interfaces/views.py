import logging
from decimal import Decimal

from cvs.models import CV
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from vacancy.models import Vacancy
from vacancy.services import get_filtered_vacancies

User = get_user_model()
logger = logging.getLogger(__name__)

# --- Валюты и курсы обмена (можно вынести в settings или отдельный сервис) ---
# Примерные курсы, используйте актуальные
EXCHANGE_RATES = {
    'USD': 1.0,
    'EUR': 0.92,  # Пример
    'UAH': 41.0,  # Пример
    # Добавьте другие валюты по необходимости
}


def get_exchange_rate(currency_code):
    """Получает курс валюты относительно USD."""
    if not currency_code:
        return None
    return EXCHANGE_RATES.get(currency_code.upper())


def normalize_salary(salary_min, salary_max, currency):
    """Нормализует диапазон зарплат в USD."""
    if salary_min is None and salary_max is None:
        return None, None
    rate = get_exchange_rate(currency)
    if rate is None or rate == 0:
        return None, None  # Невозможно нормализовать
    norm_min = Decimal(salary_min) / Decimal(rate) if salary_min is not None else None
    norm_max = Decimal(salary_max) / Decimal(rate) if salary_max is not None else None
    return norm_min, norm_max


def check_salary_overlap(cv_min, cv_max, v_min, v_max):
    """Проверяет пересечение двух диапазонов зарплат (уже нормализованных)."""
    if cv_min is None and cv_max is None:
        return True  # Кандидат не указал ожидания
    if v_min is None and v_max is None:
        return True  # Вакансия не указала вилку

    # Пересечение интервалов [a,b] и [c,d]: max(a,c) <= min(b,d)
    # Обрабатываем None как бесконечность
    left = max(cv_min or Decimal('-Infinity'), v_min or Decimal('-Infinity'))
    right = min(cv_max or Decimal('Infinity'), v_max or Decimal('Infinity'))
    return left <= right


class MatchesForUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id):
        try:
            logger.info(f"Начало подбора вакансий для пользователя {user_id}")
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                logger.warning(f"Пользователь с ID {user_id} не найден.")
                return Response({'error': f'Пользователь с ID {user_id} не найден.'}, status=404)

            # --- 1. Получение CV пользователя ---
            # Предполагаем, что у пользователя одно активное CV или берем последнее загруженное
            user_cv = CV.objects.filter(user=user).order_by('-uploaded_at').first()
            if not user_cv:
                logger.info(f"Резюме для пользователя {user_id} не найдено")
                return Response({'error': f'Резюме для пользователя с ID {user_id} не найдено.'}, status=404)

            if not user_cv.analyzed:
                logger.info(f"Резюме {user_cv.id} пользователя {user_id} еще не проанализировано ИИ.")
                # Можно вернуть ошибку или инициировать анализ
                return Response({
                    'error': f'Резюме пользователя с ID {user_id} еще не проанализировано. Пожалуйста, дождитесь завершения анализа.'},
                    status=400)

            # --- 2. Получение отфильтрованных вакансий ---
            # Эта функция должна быть реализована в vacancy/services.py
            # и возвращать QuerySet объектов Vacancy
            filtered_vacancies_queryset = get_filtered_vacancies(user_cv)
            logger.info(
                f"Получено {filtered_vacancies_queryset.count()} вакансий после фильтрации для пользователя {user_id}")

            # --- 3. Извлечение данных из CV для сравнения ---
            # Предполагается, что analyze_cv_with_ai заполнило эти поля
            cv_skills_set = set(s.lower().strip() for s in (getattr(user_cv, 'skills', []) or []) if s)
            cv_cities_set = set(c.lower().strip() for c in (getattr(user_cv, 'cities', []) or []) if c)
            cv_countries_set = set(co.lower().strip() for co in (getattr(user_cv, 'countries', []) or []) if co)
            cv_is_remote = getattr(user_cv, 'is_remote', None)  # True, False, None
            cv_salary_min_raw = getattr(user_cv, 'salary_min', None)
            cv_salary_max_raw = getattr(user_cv, 'salary_max', None)
            cv_salary_currency = getattr(user_cv, 'salary_currency', None)
            cv_level = getattr(user_cv, 'level', None)  # 'Junior', 'Middle', 'Senior', None

            # Нормализация зарплаты кандидата
            cv_salary_min_norm, cv_salary_max_norm = normalize_salary(
                cv_salary_min_raw, cv_salary_max_raw, cv_salary_currency
            )

            # --- 4. Расчет совпадений для каждой вакансии ---
            matches = []
            for vacancy in filtered_vacancies_queryset:
                # --- Skills Match ---
                vacancy_skills_set = set(s.lower().strip() for s in (getattr(vacancy, 'skills', []) or []) if s)
                skills_match_score = 0
                if vacancy_skills_set:
                    intersection_skills = cv_skills_set.intersection(vacancy_skills_set)
                    union_skills = cv_skills_set.union(vacancy_skills_set)
                    if union_skills:
                        # Jaccard similarity
                        skills_match_score = round((len(intersection_skills) / len(union_skills)) * 100)
                # Если у вакансии нет навыков, score остается 0

                # --- Location Match ---
                location_match_score = 0
                v_is_remote = getattr(vacancy, 'is_remote', False)
                v_is_hybrid = getattr(vacancy, 'is_hybrid', None)  # True, False, None

                # Если кандидат открыт к удаленной работе и вакансия удаленная/гибридная
                if cv_is_remote and (v_is_remote or v_is_hybrid):
                    location_match_score = 100
                # Если кандидат указал города
                elif cv_cities_set:
                    vacancy_cities_set = set(c.lower().strip() for c in (getattr(vacancy, 'cities', []) or []) if c)
                    if cv_cities_set.intersection(vacancy_cities_set):
                        location_match_score = 100
                    # Если города не совпали, проверяем страны
                    elif cv_countries_set:
                        vacancy_countries_set = set(
                            co.lower().strip() for co in (getattr(vacancy, 'countries', []) or []) if co)
                        if cv_countries_set.intersection(vacancy_countries_set):
                            location_match_score = 70  # Частичное совпадение по стране
                # Если кандидат не указал конкретную локацию, но вакансия удаленная
                elif cv_is_remote is None and v_is_remote:
                    location_match_score = 50  # Может подойти
                # Если кандидат не указал локацию и вакансия не удаленная
                elif cv_is_remote is None and not v_is_remote:
                    # Можно считать 50 (нейтрально) или 0
                    location_match_score = 50
                # Если кандидат НЕ открыт к удаленной работе, а вакансия только удаленная
                elif cv_is_remote == False and v_is_remote and not v_is_hybrid:
                    location_match_score = 0
                # Если кандидат открыт к удаленной работе, а вакансия только офисная
                elif cv_is_remote == True and not v_is_remote and not v_is_hybrid:
                    location_match_score = 0
                else:
                    # Остальные случаи - нет совпадения
                    location_match_score = 0

                # --- Salary Match ---
                salary_match_score = 0
                v_salary_min_raw = getattr(vacancy, 'salary_min', None)
                v_salary_max_raw = getattr(vacancy, 'salary_max', None)
                v_salary_currency = getattr(vacancy, 'salary_currency', None)

                # Нормализация зарплаты вакансии
                v_salary_min_norm, v_salary_max_norm = normalize_salary(
                    v_salary_min_raw, v_salary_max_raw, v_salary_currency
                )

                # Проверка пересечения нормализованных диапазонов
                if check_salary_overlap(cv_salary_min_norm, cv_salary_max_norm, v_salary_min_norm, v_salary_max_norm):
                    salary_match_score = 100
                else:
                    salary_match_score = 0

                # Если у кандидата или вакансии не указана зарплата, можно считать совпадение 100%
                if (cv_salary_min_raw is None and cv_salary_max_raw is None) or \
                        (v_salary_min_raw is None and v_salary_max_raw is None):
                    salary_match_score = 100

                # --- Level Match ---
                level_match_score = 100  # По умолчанию
                if cv_level and getattr(vacancy, 'level', None):
                    cv_lvl_clean = cv_level.lower().strip()
                    v_lvl_clean = getattr(vacancy, 'level', '').lower().strip()
                    if cv_lvl_clean == v_lvl_clean:
                        level_match_score = 100
                    else:
                        # Логика уровней: Junior -> Middle -> Senior -> Lead (пример)
                        level_hierarchy = ['intern', 'junior', 'middle', 'senior', 'lead', 'director']
                        try:
                            cv_lvl_index = level_hierarchy.index(cv_lvl_clean)
                            v_lvl_index = level_hierarchy.index(v_lvl_clean)
                            diff = v_lvl_index - cv_lvl_index
                            if diff == 0:
                                level_match_score = 100
                            elif diff == 1:
                                # Кандидат на уровень ниже - частичное совпадение
                                level_match_score = 70
                            elif diff > 1:
                                # Кандидат слишком низкого уровня
                                level_match_score = 30
                            elif diff == -1:
                                # Кандидат выше уровня - может подойти
                                level_match_score = 90
                            else:  # diff < -1
                                # Кандидат намного выше - возможно подходит
                                level_match_score = 70
                        except ValueError:
                            # Неизвестный уровень
                            level_match_score = 50
                # Если уровень не указан у кого-то, оставляем 100

                # --- Расчет общего Score ---
                # Веса факторов
                weights = {
                    'skills': 0.5,  # 50%
                    'location': 0.2,  # 20%
                    'salary': 0.2,  # 20%
                    'level': 0.1  # 10%
                }

                # Расчет взвешенного среднего
                total_score = (
                                      (skills_match_score / 100.0) * weights['skills'] +
                                      (location_match_score / 100.0) * weights['location'] +
                                      (salary_match_score / 100.0) * weights['salary'] +
                                      (level_match_score / 100.0) * weights['level']
                              ) * 100

                final_score = round(total_score)

                # --- Определение качества совпадения ---
                if final_score >= 80:
                    match_quality = "High"
                elif final_score >= 50:
                    match_quality = "Medium"
                else:
                    match_quality = "Low"

                matches.append({
                    'vacancy_id': vacancy.id,
                    'title': vacancy.title,
                    'score': final_score,
                    'match_quality': match_quality,
                    'skills_match': skills_match_score,
                    'location_match': location_match_score,
                    'salary_match': salary_match_score,
                    # 'level_match': level_match_score, # Можно добавить для отладки
                })

            logger.info(f"Рассчитано {len(matches)} совпадений для пользователя {user_id}")
            return Response(matches)

        except Exception as e:
            logger.error(f"Неожиданная ошибка при подборе вакансий для пользователя {user_id}: {e}", exc_info=True)
            return Response({'error': 'Внутренняя ошибка сервера'}, status=500)
