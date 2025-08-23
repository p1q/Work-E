import logging

from cvs.models import CV
from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework.views import APIView
from vacancy.models import Vacancy

from src.matching.service import calculate_languages_match, calculate_responsibilities_match, calculate_tools_match, \
    calculate_salary_match, calculate_location_match, calculate_weighted_match_score, calculate_skills_match

User = get_user_model()
logger = logging.getLogger(__name__)


class MatchesForUserView(APIView):
    permission_classes = []

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': f'User with ID {user_id} not found.'}, status=404)

        user_cv = CV.objects.filter(user=user).order_by('-uploaded_at').first()
        if not user_cv:
            return Response({'error': f'Resumé for user {user_id} not found.'}, status=404)

        try:
            vacancies = Vacancy.objects.all()
            if hasattr(user_cv, 'level') and user_cv.level:
                vacancies = vacancies.filter(level=user_cv.level)
            if hasattr(user_cv, 'categories') and user_cv.categories.exists():
                vacancies = vacancies.filter(categories__in=user_cv.categories.all()).distinct()
            if (hasattr(user_cv, 'languages') and user_cv.languages.exists() and
                    any(lang.level for lang in user_cv.languages.all() if lang.level)):
                required_langs = [
                    lang.language for lang in user_cv.languages.all()
                    if lang.level and lang.level.strip()
                ]
                if required_langs:
                    vacancies = vacancies.filter(languages__language__in=required_langs).distinct()
            if hasattr(user_cv, 'countries') and user_cv.countries.exists():
                vacancies = vacancies.filter(countries__in=user_cv.countries.all()).distinct()
            if hasattr(user_cv, 'cities') and user_cv.cities.exists():
                vacancies = vacancies.filter(cities__in=user_cv.cities.all()).distinct()
            if hasattr(user_cv, 'is_remote') and user_cv.is_remote:
                vacancies = vacancies.filter(is_remote=True)
            if (hasattr(user_cv, 'salary_min') and user_cv.salary_min is not None and
                    hasattr(user_cv, 'salary_max') and user_cv.salary_max is not None and
                    hasattr(user_cv, 'salary_currency') and user_cv.salary_currency):
                vacancies = vacancies.filter(
                    salary_currency=user_cv.salary_currency,
                    salary_max__gte=user_cv.salary_min,
                    salary_min__lte=user_cv.salary_max
                )
            logger.info(f"Found {vacancies.count()} vacancies for CV {user_cv.id} after filtering.")
        except Exception as e:
            logger.error(f"Error filtering vacancies for CV {user_cv.id}: {e}", exc_info=True)
            vacancies = Vacancy.objects.none()

        matches = []
        for vacancy in vacancies:
            try:
                skills_match = calculate_skills_match(
                    list(user_cv.skills.values_list('name', flat=True)) if hasattr(user_cv.skills, 'all') else getattr(
                        user_cv, 'skills', []),
                    list(vacancy.skills.values_list('name', flat=True)) if hasattr(vacancy.skills, 'all') else getattr(
                        vacancy, 'skills', [])
                )
                location_match = calculate_location_match(user_cv, vacancy)
                salary_match = calculate_salary_match(user_cv, vacancy)
                tools_match = calculate_tools_match(
                    getattr(user_cv, 'tools', []),
                    getattr(vacancy, 'tools', [])
                )
                responsibilities_match = calculate_responsibilities_match(
                    getattr(user_cv, 'responsibilities', []),
                    getattr(vacancy, 'responsibilities', [])
                )
                languages_match = calculate_languages_match(
                    [
                        {"language": lang.language, "level": lang.level}
                        for lang in (
                        user_cv.languages.all() if hasattr(user_cv.languages, 'all') else getattr(user_cv, 'languages',
                                                                                                  []))
                    ],
                    [
                        {"language": lang.language, "level": lang.level}
                        for lang in (
                        vacancy.languages.all() if hasattr(vacancy.languages, 'all') else getattr(vacancy, 'languages',
                                                                                                  []))
                    ]
                )

                score = calculate_weighted_match_score(
                    skills_match=skills_match,
                    location_match=location_match,
                    salary_match=salary_match,
                    tools_match=tools_match,
                    responsibilities_match=responsibilities_match,
                    languages_match=languages_match
                )

                match_quality = 'High' if score >= 80 else ('Medium' if score >= 50 else 'Low')

                matches.append({
                    'vacancy_id': vacancy.id,
                    'title': vacancy.title,
                    'score': round(score, 2),
                    'match_quality': match_quality,
                    'skills_match': round(skills_match, 2),
                    'location_match': round(location_match, 2),
                    'salary_match': round(salary_match, 2),
                    'tools_match': round(tools_match, 2),
                    'responsibilities_match': round(responsibilities_match, 2),
                    'languages_match': round(languages_match, 2)
                })
            except Exception as e:
                logger.error(f"Error calculating match for vacancy {vacancy.id} and CV {user_cv.id}: {e}",
                             exc_info=True)
                continue

        return Response(matches)
