from rest_framework import serializers
from ..models import Vacancy


class VacancySerializer(serializers.ModelSerializer):
    class Meta:
        model = Vacancy
        fields = ['id', 'title', 'link', 'location', 'salary', 'category', 'date', 'description',
                  'skills', 'tools', 'responsibilities', 'languages', 'location_field', 'salary_range']
