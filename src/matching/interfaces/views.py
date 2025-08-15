import logging
import random
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from cvs.models import CV
from vacancy.models import Vacancy
from matching.models import Match
from cvs.interfaces.views import _get_latest_cv_for_user

logger = logging.getLogger(__name__)


def calculate_match():
    return {
        'score': round(random.uniform(50, 100), 2),
        'match_quality': random.choice(['Low', 'Medium', 'High']),
        'skills_match': round(random.uniform(0, 100), 2),
        'tools_match': round(random.uniform(0, 100), 2),
        'responsibilities_match': round(random.uniform(0, 100), 2),
        'languages_match': round(random.uniform(0, 100), 2),
        'location_match': round(random.uniform(0, 100), 2),
        'salary_match': round(random.uniform(0, 100), 2),
    }


class MatchesForUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, user_id):
        logger.info(f"Отримання матчів для користувача {user_id}")

        cv, error_response = _get_latest_cv_for_user(user_id, logger)
        if error_response:
            return error_response

        existing_matches = Match.objects.filter(user_id=user_id)
        existing_vacancy_ids = set(existing_matches.values_list('vacancy_id', flat=True))

        all_vacancies = Vacancy.objects.all()
        new_matches_to_create = []

        for vacancy in all_vacancies:
            if vacancy.id not in existing_vacancy_ids:
                match_data = calculate_match(cv, vacancy)
                new_match = Match(
                    user_id=user_id,
                    vacancy=vacancy,
                    **match_data
                )
                new_matches_to_create.append(new_match)

        if new_matches_to_create:
            Match.objects.bulk_create(new_matches_to_create)
            logger.info(f"Створено {len(new_matches_to_create)} нових матчів для користувача {user_id}")

        matches = Match.objects.filter(user_id=user_id).select_related('vacancy')
        result = []
        for match in matches:
            result.append({
                'vacancy_id': match.vacancy.id,
                'score': match.score,
                'match_quality': match.match_quality
            })

        return Response(result, status=status.HTTP_200_OK)
