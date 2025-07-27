from rest_framework import serializers


class VacancySerializer(serializers.Serializer):
    title = serializers.CharField(max_length=100, help_text="Назва вакансії")
    location = serializers.CharField(max_length=100, help_text="Місце розташування вакансії")
    salary = serializers.CharField(max_length=50, help_text="Зарплата для вакансії")
    description = serializers.CharField(max_length=500, help_text="Опис вакансії")
