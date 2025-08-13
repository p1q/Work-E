from rest_framework import serializers
from vacancy.models import Vacancy, VacancyCategory, Country, City, Currency


class VacancySerializer(serializers.ModelSerializer):
    categories = serializers.MultipleChoiceField(choices=VacancyCategory.choices, help_text="Категорії вакансії")
    countries = serializers.MultipleChoiceField(choices=Country.choices, required=False, help_text="Країни")
    cities = serializers.MultipleChoiceField(choices=City.choices, required=False, help_text="Міста або 'Віддалено'")
    salary_currency = serializers.ChoiceField(choices=Currency.choices, required=False, help_text="Валюта зарплати")

    class Meta:
        model = Vacancy
        fields = [
            'id', 'title', 'description', 'link', 'countries', 'cities',
            'custom_eu_cities', 'salary_min', 'salary_max', 'salary_currency',
            'is_remote', 'is_hybrid', 'english_level', 'location_field',
            'skills', 'tools', 'responsibilities', 'categories'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        salary_min = data.get('salary_min')
        salary_max = data.get('salary_max')

        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            raise serializers.ValidationError("Мінімальна зарплата не може бути більшою за максимальну.")

        if (salary_min is not None or salary_max is not None) and not data.get('salary_currency'):
            raise serializers.ValidationError("Якщо вказана зарплата, необхідно вказати валюту.")

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['location'] = instance.location
        data['salary_range'] = instance.salary_range
        return data
