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

EXCHANGE_RATES = {
    'UAH': 0.027,
    'EUR': 1.07,
    'USD': 1.0
}


def convert_to_usd(amount, currency):
    if currency not in EXCHANGE_RATES:
        return None
    return amount * Decimal(str(EXCHANGE_RATES[currency]))


class MatchesForUserView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, user_id, *args, **kwargs):
        if user_id is None:
            return Response({'error': 'user_id is required'}, status=400)

        try:
            user_id = int(user_id)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid user_id'}, status=400)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': f'User with ID {user_id} not found.'}, status=404)

        user_cv = CV.objects.filter(user=user).order_by('-uploaded_at').first()
        if not user_cv:
            return Response({'error': f'Resumé for user {user_id} not found.'}, status=404)

        cv_data = {
            'languages': user_cv.languages,
            'level': user_cv.level,
            'categories': user_cv.categories,
            'is_office': user_cv.is_office,
            'is_remote': user_cv.is_remote,
            'willing_to_relocate': user_cv.willing_to_relocate,
            'salary_min': user_cv.salary_min,
            'salary_max': user_cv.salary_max,
        }

        vacancies = get_filtered_vacancies(user_cv)

        matches = []
        for vacancy in vacancies:
            matches.append({
                'vacancy_id': vacancy.id,
                'title': vacancy.title,
                'score': 100,
                'match_quality': 'High',
                'skills_match': 100,
                'location_match': 100,
                'salary_match': 100,
            })

        return Response(matches)
