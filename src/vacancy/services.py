from cvs.models import CV
from django.db.models import Q

from .models import Vacancy

LANGUAGE_LEVELS = {
    'A1': 1,
    'A2': 2,
    'B1': 3,
    'B2': 4,
    'C1': 5,
    'C2': 6
}


def get_filtered_vacancies(user_cv: CV):
    vacancies = Vacancy.objects.all()

    # 1. Фільтрація за мовами
    cv_languages = user_cv.languages  # Мови з CV
    vacancy_languages = []

    if cv_languages:
        for lang in cv_languages:
            lang_level = lang.get("level")
            # Якщо в CV є рівень мови і в вакансії є вимоги, перевіряємо умови
            if vacancy_languages:
                for vacancy_lang in vacancy_languages:
                    vacancy_level = vacancy_lang.get("level")
                    if vacancy_level and lang_level:
                        cv_level_numeric = LANGUAGE_LEVELS.get(lang_level, 0)
                        vacancy_level_numeric = LANGUAGE_LEVELS.get(vacancy_level, 0)
                        if vacancy_level_numeric - cv_level_numeric <= 1:  # Менше або рівно на 1 рівень
                            vacancies = vacancies.filter(
                                languages__contains=[vacancy_lang["language"]]
                            )

    # 2. Фільтрація за рівнем
    if user_cv.level and user_cv.level != "":
        vacancies = vacancies.filter(level=user_cv.level)

    # 3. Фільтрація за категоріями
    if user_cv.categories:
        vacancies = vacancies.filter(categories__contains=[user_cv.categories[0]])

    # 4. Локація та релокація
    user_location = user_cv.countries + user_cv.cities
    if user_cv.willing_to_relocate:
        vacancies = vacancies.filter(Q(is_remote=True) | Q(is_hybrid=True) | Q(countries__in=user_location))
    else:
        if user_cv.is_remote is not None:
            if user_cv.is_remote:
                vacancies = vacancies.filter(is_remote=True)
            elif user_cv.is_office is not None:
                if user_cv.is_office:
                    vacancies = vacancies.filter(cities__in=user_cv.cities)
                elif user_cv.is_hybrid:
                    vacancies = vacancies.filter(is_hybrid=True)

    # 5. Фільтрація за зарплатою
    if user_cv.salary_min and user_cv.salary_max:
        min_salary = user_cv.salary_min
        max_salary = user_cv.salary_max
        vacancies = vacancies.filter(
            Q(salary_min__gte=min_salary * 0.8) & Q(salary_max__lte=max_salary * 1.2)
        )
    return vacancies
