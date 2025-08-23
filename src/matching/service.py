import logging
from decimal import Decimal
from cvs.models import CV
from vacancy.models import Vacancy

logger = logging.getLogger(__name__)

EXCHANGE_RATES = {
    'USD': 1.0,
    'EUR': 0.92,
    'UAH': 41.0,
}


def get_exchange_rate(currency_code):
    if not currency_code:
        return None
    return EXCHANGE_RATES.get(currency_code.upper())


def normalize_salary(salary_min, salary_max, currency):
    if salary_min is None and salary_max is None:
        return None, None
    rate = get_exchange_rate(currency)
    if rate is None or rate == 0:
        return None, None
    norm_min = Decimal(salary_min) / Decimal(rate) if salary_min is not None else None
    norm_max = Decimal(salary_max) / Decimal(rate) if salary_max is not None else None
    return norm_min, norm_max


def check_salary_overlap(cv_min, cv_max, v_min, v_max):
    if cv_min is None and cv_max is None:
        return True
    if v_min is None and v_max is None:
        return True
    left = max(cv_min or Decimal('-Infinity'), v_min or Decimal('-Infinity'))
    right = min(cv_max or Decimal('Infinity'), v_max or Decimal('Infinity'))
    return left <= right


def calculate_vacancy_matches_for_cv(user_cv: CV, vacancies_queryset):
    matches = []
    cv_skills_set = set(s.lower().strip() for s in (getattr(user_cv, 'skills', []) or []) if s)
    cv_cities_set = set(c.lower().strip() for c in (getattr(user_cv, 'cities', []) or []) if c)
    cv_countries_set = set(co.lower().strip() for co in (getattr(user_cv, 'countries', []) or []) if co)
    cv_is_remote = getattr(user_cv, 'is_remote', None)
    cv_salary_min_raw = getattr(user_cv, 'salary_min', None)
    cv_salary_max_raw = getattr(user_cv, 'salary_max', None)
    cv_salary_currency = getattr(user_cv, 'salary_currency', None)
    cv_level = getattr(user_cv, 'level', None)

    cv_salary_min_norm, cv_salary_max_norm = normalize_salary(
        cv_salary_min_raw, cv_salary_max_raw, cv_salary_currency
    )

    for vacancy in vacancies_queryset:
        vacancy_skills_set = set(s.lower().strip() for s in (getattr(vacancy, 'skills', []) or []) if s)
        skills_match_score = 0
        if vacancy_skills_set:
            intersection_skills = cv_skills_set.intersection(vacancy_skills_set)
            union_skills = cv_skills_set.union(vacancy_skills_set)
            if union_skills:
                skills_match_score = round((len(intersection_skills) / len(union_skills)) * 100)

        location_match_score = 0
        v_is_remote = getattr(vacancy, 'is_remote', False)
        v_is_hybrid = getattr(vacancy, 'is_hybrid', None)

        if cv_is_remote and (v_is_remote or v_is_hybrid):
            location_match_score = 100
        elif cv_cities_set:
            vacancy_cities_set = set(c.lower().strip() for c in (getattr(vacancy, 'cities', []) or []) if c)
            if cv_cities_set.intersection(vacancy_cities_set):
                location_match_score = 100
            elif cv_countries_set:
                vacancy_countries_set = set(
                    co.lower().strip() for co in (getattr(vacancy, 'countries', []) or []) if co)
                if cv_countries_set.intersection(vacancy_countries_set):
                    location_match_score = 70
        elif cv_is_remote is None and v_is_remote:
            location_match_score = 50
        elif cv_is_remote is None and not v_is_remote:
            location_match_score = 50
        elif cv_is_remote == False and v_is_remote and not v_is_hybrid:
            location_match_score = 0
        elif cv_is_remote == True and not v_is_remote and not v_is_hybrid:
            location_match_score = 0
        else:
            location_match_score = 0

        salary_match_score = 0
        v_salary_min_raw = getattr(vacancy, 'salary_min', None)
        v_salary_max_raw = getattr(vacancy, 'salary_max', None)
        v_salary_currency = getattr(vacancy, 'salary_currency', None)

        v_salary_min_norm, v_salary_max_norm = normalize_salary(
            v_salary_min_raw, v_salary_max_raw, v_salary_currency
        )

        if check_salary_overlap(cv_salary_min_norm, cv_salary_max_norm, v_salary_min_norm, v_salary_max_norm):
            salary_match_score = 100
        else:
            salary_match_score = 0

        if (cv_salary_min_raw is None and cv_salary_max_raw is None) or \
                (v_salary_min_raw is None and v_salary_max_raw is None):
            salary_match_score = 100

        level_match_score = 100
        if cv_level and getattr(vacancy, 'level', None):
            cv_lvl_clean = cv_level.lower().strip()
            v_lvl_clean = getattr(vacancy, 'level', '').lower().strip()
            if cv_lvl_clean == v_lvl_clean:
                level_match_score = 100
            else:
                level_hierarchy = ['intern', 'junior', 'middle', 'senior', 'lead', 'director']
                try:
                    cv_lvl_index = level_hierarchy.index(cv_lvl_clean)
                    v_lvl_index = level_hierarchy.index(v_lvl_clean)
                    diff = v_lvl_index - cv_lvl_index
                    if diff == 0:
                        level_match_score = 100
                    elif diff == 1:
                        level_match_score = 70
                    elif diff > 1:
                        level_match_score = 30
                    elif diff == -1:
                        level_match_score = 90
                    else:
                        level_match_score = 70
                except ValueError:
                    level_match_score = 50

        weights = {
            'skills': 0.5,
            'location': 0.2,
            'salary': 0.2,
            'level': 0.1
        }

        total_score = (
                              (skills_match_score / 100.0) * weights['skills'] +
                              (location_match_score / 100.0) * weights['location'] +
                              (salary_match_score / 100.0) * weights['salary'] +
                              (level_match_score / 100.0) * weights['level']
                      ) * 100

        final_score = round(total_score)

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
        })

    return matches
