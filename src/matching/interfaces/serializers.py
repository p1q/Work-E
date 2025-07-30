from rest_framework import serializers
from matching.models import Match
from src.users.interfaces.serializers import UserSerializer
from src.vacancy.interfaces.serializers import VacancySerializer


class MatchSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    vacancy = VacancySerializer(read_only=True)
    match_quality = serializers.CharField(read_only=True)

    class Meta:
        model = Match
        fields = [
            'id', 'user', 'vacancy', 'score', 'match_quality',
            'skills_match', 'tools_match', 'responsibilities_match',
            'languages_match', 'location_match', 'salary_match'
        ]
