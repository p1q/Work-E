from django.db import transaction
from .models import Match
from src.users.models import User
from src.vacancy.models import Vacancy
import re

WEIGHTS = {
    'skills': 0.25,
    'tools': 0.15,
    'responsibilities': 0.20,
    'languages': 0.15,
    'location': 0.15,
    'salary': 0.10,
}


def normalize_text(text):
    if not text:
        return set()
    return set(re.split(r'[,;.\s]+', text.lower().strip()))


def calculate_similarity(text1, text2):
    set1 = normalize_text(text1)
    set2 = normalize_text(text2)
    if not set1 and not set2:
        return 100.0
    if not set1 or not set2:
        return 0.0
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return (len(intersection) / len(union)) * 100


def calculate_salary_match(cv_salary_range, vacancy_salary_range):
    if not cv_salary_range or not vacancy_salary_range:
        return 50.0
    try:
        cv_min, cv_max = map(int, cv_salary_range.split('-'))
        vac_min, vac_max = map(int, vacancy_salary_range.split('-'))

        if cv_max < vac_min or vac_max < cv_min:
            return 0.0
        overlap_min = max(cv_min, vac_min)
        overlap_max = min(cv_max, vac_max)
        overlap = max(0, overlap_max - overlap_min)
        range_sum = (cv_max - cv_min) + (vac_max - vac_min)
        if range_sum == 0:
            return 100.0
        return (2 * overlap / range_sum) * 100
    except:
        return 50.0


def calculate_location_match(cv_location, vacancy_location):
    if not cv_location or not vacancy_location:
        return 50.0
    cv_parts = set(cv_location.lower().split(','))
    vac_parts = set(vacancy_location.lower().split(','))
    if cv_parts == vac_parts:
        return 100.0
    elif cv_parts & vac_parts:
        return 75.0
    else:
        return 0.0


def create_or_update_match(user: User, vacancy: Vacancy):
    from src.cvs.models import CV
    user_cv = CV.objects.filter(user=user).order_by('-uploaded_at').first()
    if not user_cv:
        return None

    skills_match = calculate_similarity(user_cv.skills, vacancy.skills)
    tools_match = calculate_similarity(user_cv.tools, vacancy.tools)
    responsibilities_match = calculate_similarity(user_cv.responsibilities, vacancy.responsibilities)
    languages_match = calculate_similarity(user_cv.languages, vacancy.languages)
    location_match = calculate_location_match(user_cv.location_field, vacancy.location_field)
    salary_match = calculate_salary_match(user_cv.salary_range, vacancy.salary_range)

    score = (
            skills_match * WEIGHTS['skills'] +
            tools_match * WEIGHTS['tools'] +
            responsibilities_match * WEIGHTS['responsibilities'] +
            languages_match * WEIGHTS['languages'] +
            location_match * WEIGHTS['location'] +
            salary_match * WEIGHTS['salary']
    )

    match, created = Match.objects.update_or_create(
        user=user,
        vacancy=vacancy,
        defaults={
            'score': round(score, 2),
            'skills_match': round(skills_match, 2),
            'tools_match': round(tools_match, 2),
            'responsibilities_match': round(responsibilities_match, 2),
            'languages_match': round(languages_match, 2),
            'location_match': round(location_match, 2),
            'salary_match': round(salary_match, 2),
        }
    )
    return match


def bulk_create_matches():
    from src.cvs.models import CV
    users_with_cv = User.objects.filter(cvs__isnull=False).distinct()
    vacancies = Vacancy.objects.all()

    with transaction.atomic():
        Match.objects.all().delete()
        for user in users_with_cv:
            for vacancy in vacancies:
                create_or_update_match(user, vacancy)
