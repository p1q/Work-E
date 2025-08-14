from rest_framework import serializers

from vacancy.models import Vacancy, VacancyCategory, Country, City, Currency


class VacancySerializer(serializers.ModelSerializer):
    categories = serializers.ListField(child=serializers.CharField(max_length=100), required=False,
                                       help_text="Категорії вакансії")
    skills = serializers.ListField(child=serializers.CharField(), required=False,
                                   help_text="Ключові технічні навички та технології")
    responsibilities = serializers.ListField(child=serializers.CharField(), required=False,
                                             help_text="Обов'язки кандидата")
    countries = serializers.MultipleChoiceField(choices=Country.choices, required=False, help_text="Країни")
    cities = serializers.MultipleChoiceField(choices=City.choices, required=False, help_text="Міста або 'Віддалено'")
    salary_currency = serializers.ChoiceField(choices=Currency.choices, required=False, help_text="Валюта зарплати")
    languages = serializers.ListField(child=serializers.DictField(), required=False, help_text="Мови")

    class Meta:
        model = Vacancy
        fields = ['id', 'title', 'description', 'link', 'countries', 'cities',
                  'skills', 'responsibilities', 'categories', 'languages', 'location',
                  'salary_min', 'salary_max', 'salary_currency', 'level',
                  'english_level', 'is_remote', 'is_hybrid', 'willing_to_relocate']

    def validate(self, data):
        if 'categories' not in data or not data['categories']:
            raise serializers.ValidationError({"categories": "Це поле є обов'язковим."})
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['location'] = instance.location
        data['salary_range'] = instance.salary_range
        return data
