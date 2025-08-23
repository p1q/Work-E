import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

EXCHANGE_RATES = {
    'UAH': 0.027,
    'USD': 1.0,
    'EUR': 1.07,
}


def _normalize_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    return " ".join(text.strip().lower().split())


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (ValueError, TypeError):
        return 0


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def calculate_skills_match(cv_skills: List[str], vacancy_skills: List[str]) -> float:
    if not vacancy_skills:
        return 100.0

    cv_skills_normalized = {_normalize_text(skill) for skill in cv_skills}
    vacancy_skills_normalized = {_normalize_text(skill) for skill in vacancy_skills}

    matched_skills = cv_skills_normalized.intersection(vacancy_skills_normalized)

    matched_skills_partial = set()
    for cv_skill in cv_skills_normalized:
        for vacancy_skill in vacancy_skills_normalized:
            if cv_skill in vacancy_skill or vacancy_skill in cv_skill:
                matched_skills_partial.add(vacancy_skill)

    total_matched = len(matched_skills.union(matched_skills_partial))
    return (total_matched / len(vacancy_skills_normalized)) * 100 if vacancy_skills_normalized else 0.0


def calculate_tools_match(cv_tools: List[str], vacancy_tools: List[str]) -> float:
    if not vacancy_tools:
        return 100.0

    cv_tools_normalized = {_normalize_text(tool) for tool in cv_tools}
    vacancy_tools_normalized = {_normalize_text(tool) for tool in vacancy_tools}

    matched_tools = cv_tools_normalized.intersection(vacancy_tools_normalized)
    return (len(matched_tools) / len(vacancy_tools_normalized)) * 100 if vacancy_tools_normalized else 0.0


def calculate_responsibilities_match(cv_responsibilities: List[str], vacancy_responsibilities: List[str]) -> float:
    if not vacancy_responsibilities:
        return 100.0

    cv_responsibilities_normalized = [_normalize_text(resp) for resp in cv_responsibilities]
    vacancy_responsibilities_normalized = [_normalize_text(resp) for resp in vacancy_responsibilities]

    matched = 0
    for v_resp in vacancy_responsibilities_normalized:
        for cv_resp in cv_responsibilities_normalized:
            if v_resp in cv_resp or cv_resp in v_resp:
                matched += 1
                break

    return (matched / len(vacancy_responsibilities_normalized)) * 100 if vacancy_responsibilities_normalized else 0.0


def calculate_languages_match(cv_languages: List[Dict[str, str]], vacancy_languages: List[Dict[str, str]]) -> float:
    if not vacancy_languages:
        return 100.0

    cv_langs_dict = {
        _normalize_text(lang.get("language", "")): _normalize_text(lang.get("level", ""))
        for lang in cv_languages
    }

    matched = 0
    total_weight = 0

    for v_lang in vacancy_languages:
        v_lang_name = _normalize_text(v_lang.get("language", ""))
        v_lang_level = _normalize_text(v_lang.get("level", ""))

        if not v_lang_name:
            continue

        total_weight += 1
        cv_lang_level = cv_langs_dict.get(v_lang_name, "")

        if cv_lang_level:
            if not v_lang_level or cv_lang_level >= v_lang_level:
                matched += 1
            elif _compare_language_levels(cv_lang_level, v_lang_level) >= 0:
                matched += 1

    return (matched / total_weight) * 100 if total_weight > 0 else 0.0


def _compare_language_levels(cv_level: str, required_level: str) -> int:
    levels = {
        "a1": 1, "a2": 2, "b1": 3, "b2": 4,
        "c1": 5, "c2": 6, "elementary": 1, "intermediate": 3,
        "upper-intermediate": 4, "advanced": 5, "proficiency": 6
    }

    cv_num = levels.get(cv_level, 0)
    req_num = levels.get(required_level, 0)

    return cv_num - req_num


def calculate_location_match(cv_obj: Any, vacancy_obj: Any) -> float:
    if getattr(vacancy_obj, 'is_remote', False):
        return 100.0

    if getattr(cv_obj, 'is_office', False) is False and not getattr(cv_obj, 'is_remote', True):
        return 0.0

    if getattr(cv_obj, 'willing_to_relocate', False):
        return 70.0

    cv_countries = set()
    vacancy_countries = set()

    if hasattr(cv_obj, 'countries') and cv_obj.countries.exists():
        cv_countries = {_normalize_text(country.name) for country in cv_obj.countries.all()}
    elif hasattr(cv_obj, 'countries') and isinstance(cv_obj.countries, list):
        cv_countries = {_normalize_text(country) for country in cv_obj.countries}

    if hasattr(vacancy_obj, 'countries') and vacancy_obj.countries.exists():
        vacancy_countries = {_normalize_text(country.name) for country in vacancy_obj.countries.all()}
    elif hasattr(vacancy_obj, 'countries') and isinstance(vacancy_obj.countries, list):
        vacancy_countries = {_normalize_text(country) for country in vacancy_obj.countries}

    if vacancy_countries and cv_countries.intersection(vacancy_countries):
        cv_cities = set()
        vacancy_cities = set()

        if hasattr(cv_obj, 'cities') and cv_obj.cities.exists():
            cv_cities = {_normalize_text(city.name) for city in cv_obj.cities.all()}
        elif hasattr(cv_obj, 'cities') and isinstance(cv_obj.cities, list):
            cv_cities = {_normalize_text(city) for city in cv_obj.cities}

        if hasattr(vacancy_obj, 'cities') and vacancy_obj.cities.exists():
            vacancy_cities = {_normalize_text(city.name) for city in vacancy_obj.cities.all()}
        elif hasattr(vacancy_obj, 'cities') and isinstance(vacancy_obj.cities, list):
            vacancy_cities = {_normalize_text(city) for city in vacancy_obj.cities}

        if not vacancy_cities:
            return 80.0
        elif cv_cities.intersection(vacancy_cities):
            return 100.0
        else:
            return 60.0

    return 0.0


def convert_to_usd(amount, currency):
    if currency not in EXCHANGE_RATES:
        return None
    return amount * EXCHANGE_RATES[currency]


def calculate_salary_match(cv_obj: Any, vacancy_obj: Any) -> float:
    try:
        cv_min = _safe_int(getattr(cv_obj, 'salary_min', None))
        cv_max = _safe_int(getattr(cv_obj, 'salary_max', None))
        cv_currency = _normalize_text(getattr(cv_obj, 'salary_currency', None))

        vacancy_min = _safe_int(getattr(vacancy_obj, 'salary_min', None))
        vacancy_max = _safe_int(getattr(vacancy_obj, 'salary_max', None))
        vacancy_currency = _normalize_text(getattr(vacancy_obj, 'salary_currency', None))

        if (not cv_min and not cv_max) or (not vacancy_min and not vacancy_max):
            return 100.0

        cv_min_usd = convert_to_usd(cv_min, cv_currency) if cv_currency else None
        cv_max_usd = convert_to_usd(cv_max, cv_currency) if cv_currency else None
        vacancy_min_usd = convert_to_usd(vacancy_min, vacancy_currency) if vacancy_currency else None
        vacancy_max_usd = convert_to_usd(vacancy_max, vacancy_currency) if vacancy_currency else None

        if (cv_currency and (cv_min_usd is None or cv_max_usd is None)) or \
                (vacancy_currency and (vacancy_min_usd is None or vacancy_max_usd is None)):
            return 0.0

        if cv_min_usd is None:
            cv_min_usd = float(cv_min) if cv_min else None
        if cv_max_usd is None:
            cv_max_usd = float(cv_max) if cv_max else None
        if vacancy_min_usd is None:
            vacancy_min_usd = float(vacancy_min) if vacancy_min else None
        if vacancy_max_usd is None:
            vacancy_max_usd = float(vacancy_max) if vacancy_max else None

        if (cv_min_usd is None and cv_max_usd is None) or (vacancy_min_usd is None and vacancy_max_usd is None):
            return 100.0

        if cv_min_usd is not None and cv_max_usd is None:
            cv_max_usd = cv_min_usd * 2
        elif cv_max_usd is not None and cv_min_usd is None:
            cv_min_usd = cv_max_usd / 2
        elif cv_min_usd is None and cv_max_usd is None:
            return 100.0

        if vacancy_min_usd is not None and vacancy_max_usd is None:
            vacancy_max_usd = vacancy_min_usd * 2
        elif vacancy_max_usd is not None and vacancy_min_usd is None:
            vacancy_min_usd = vacancy_max_usd / 2
        elif vacancy_min_usd is None and vacancy_max_usd is None:
            return 100.0

        if cv_max_usd >= vacancy_min_usd and cv_min_usd <= vacancy_max_usd:
            intersection_min = max(cv_min_usd, vacancy_min_usd)
            intersection_max = min(cv_max_usd, vacancy_max_usd)
            intersection_length = intersection_max - intersection_min

            union_min = min(cv_min_usd, vacancy_min_usd)
            union_max = max(cv_max_usd, vacancy_max_usd)
            union_length = union_max - union_min

            if union_length > 0:
                match_percent = (intersection_length / union_length) * 100
                return min(match_percent, 100.0)
            else:
                return 100.0
        else:
            return 0.0

    except Exception as e:
        logger.error(f"Ошибка при расчете совпадения зарплаты: {e}")
        return 100.0


def calculate_weighted_match_score(
        skills_match: float,
        location_match: float,
        salary_match: float,
        tools_match: float,
        responsibilities_match: float,
        languages_match: float
) -> float:
    """
    Рассчитывает итоговый взвешенный процент совпадения.
    """
    weights = {
        'skills': 0.4,
        'location': 0.15,
        'salary': 0.15,
        'tools': 0.1,
        'responsibilities': 0.1,
        'languages': 0.1
    }

    total_score = (
            skills_match * weights['skills'] +
            location_match * weights['location'] +
            salary_match * weights['salary'] +
            tools_match * weights['tools'] +
            responsibilities_match * weights['responsibilities'] +
            languages_match * weights['languages']
    )

    return total_score
