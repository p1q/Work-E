from cvs.models import CV
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


def get_filtered_vacancies(user_cv: CV):
    vacancies = Vacancy.objects.all()

    # 1. Фільтрація за мовами
    if hasattr(user_cv, 'languages') and user_cv.languages:
        language_filter = Q()
        for cv_lang in user_cv.languages:
            cv_lang_name = cv_lang.get("language")
            cv_lang_level = cv_lang.get("level")

            if not cv_lang_name or not cv_lang_level:
                continue

            if cv_lang_level in LANGUAGE_LEVELS:
                cv_level_value = LANGUAGE_LEVELS[cv_lang_level]

                # Створюємо умову для кожної вакансії
                vacancy_ids = []
                for vacancy in vacancies:
                    if not hasattr(vacancy, 'languages') or not vacancy.languages:
                        continue

                    for vacancy_lang in vacancy.languages:
                        if vacancy_lang.get("language") == cv_lang_name:
                            vacancy_level = vacancy_lang.get("level")
                            if not vacancy_level:
                                vacancy_ids.append(vacancy.id)
                                break

                            if vacancy_level in LANGUAGE_LEVELS:
                                vacancy_level_value = LANGUAGE_LEVELS[vacancy_level]
                                # Перевірка: рівень користувача >= рівень вакансії - 1
                                if cv_level_value >= vacancy_level_value - 1:
                                    vacancy_ids.append(vacancy.id)
                            break

                if vacancy_ids:
                    language_filter |= Q(id__in=vacancy_ids)

        if language_filter:
            vacancies = vacancies.filter(language_filter)

    # 2. Фільтрація за рівнем
    if hasattr(user_cv, 'level') and user_cv.level:
        vacancies = vacancies.filter(level=user_cv.level)

    # 3. Фільтрація за категоріями
    if hasattr(user_cv, 'categories') and user_cv.categories:
        primary_category = user_cv.categories[0] if len(user_cv.categories) > 0 else None
        if primary_category:
            vacancies = vacancies.filter(categories__contains=[primary_category])

    # 4. Фільтрація за локацією
    location_filter = Q()

    # Включаємо віддалені вакансії, якщо користувач не вказав небажання працювати віддалено
    if getattr(user_cv, 'is_remote', True) != False:
        location_filter |= Q(is_remote=True)

    # Якщо готовий до релокейту - включаємо все
    if getattr(user_cv, 'willing_to_relocate', False):
        # Не додаємо додаткових обмежень
        pass
    else:
        # Якщо не готовий до релокейту, перевіряємо точне співпадіння локації
        if getattr(user_cv, 'cities', None):
            location_filter |= Q(cities__overlap=user_cv.cities)
        if getattr(user_cv, 'countries', None):
            location_filter |= Q(countries__overlap=user_cv.countries)

    # Виключаємо віддалені вакансії, якщо користувач явно не хоче працювати віддалено
    if getattr(user_cv, 'is_remote', None) is False:
        location_filter &= ~Q(is_remote=True)

    # Додаємо гібридні вакансії, якщо користувач готовий до офісної роботи
    if getattr(user_cv, 'is_office', None) is True and getattr(user_cv, 'cities', None):
        location_filter |= Q(is_hybrid=True, cities__overlap=user_cv.cities)

    if location_filter:
        vacancies = vacancies.filter(location_filter)

    # 5. Фільтрація за зарплатою
    if (hasattr(user_cv, 'salary_min') and hasattr(user_cv, 'salary_max') and
            hasattr(user_cv, 'salary_currency') and
            user_cv.salary_min is not None and user_cv.salary_max is not None and user_cv.salary_currency):

        cv_min_usd = convert_to_usd(user_cv.salary_min, user_cv.salary_currency)
        cv_max_usd = convert_to_usd(user_cv.salary_max, user_cv.salary_currency)

        if cv_min_usd is not None and cv_max_usd is not None:
            tolerance = Decimal('0.20')
            lower_bound = cv_min_usd * (1 - tolerance)
            upper_bound = cv_max_usd * (1 + tolerance)

            # Створюємо список ID вакансій, що відповідають критеріям
            vacancy_ids = []
            for vacancy in vacancies:
                if (hasattr(vacancy, 'salary_min') and hasattr(vacancy, 'salary_max') and
                        hasattr(vacancy, 'salary_currency') and
                        vacancy.salary_min is not None and vacancy.salary_max is not None and vacancy.salary_currency):

                    vacancy_min_usd = convert_to_usd(vacancy.salary_min, vacancy.salary_currency)
                    vacancy_max_usd = convert_to_usd(vacancy.salary_max, vacancy.salary_currency)

                    if (vacancy_min_usd is not None and vacancy_max_usd is not None and
                            vacancy_max_usd >= lower_bound and vacancy_min_usd <= upper_bound):
                        vacancy_ids.append(vacancy.id)

            if vacancy_ids:
                vacancies = vacancies.filter(id__in=vacancy_ids)

    return vacancies
