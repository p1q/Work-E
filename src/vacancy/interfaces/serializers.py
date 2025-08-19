from rest_framework import serializers

from vacancy.models import Vacancy, VacancyCategory, Country, City, Currency


class VacancySerializer(serializers.ModelSerializer):
    categories = serializers.ListField(
        child=serializers.CharField(max_length=100),
        required=False,
        help_text="Категорії вакансії"
    )
    skills = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Ключові технічні навички та технології"
    )
    responsibilities = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        help_text="Обов'язки"
    )
    languages = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text="Мови та рівні: [{'language': 'English', 'level': 'B2'}, ...]"
    )
    countries = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_null=True,
        help_text="Країни"
    )
    cities = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_null=True,
        help_text="Міста"
    )
    description = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Опис вакансії"
    )
    salary_currency = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Валюта зарплати (наприклад, UAH, USD, EUR)"
    )
    salary_min = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        help_text="Мінімальна зарплата"
    )
    salary_max = serializers.IntegerField(
        required=False,
        allow_null=True,
        min_value=1,
        help_text="Максимальна зарплата"
    )
    is_remote = serializers.BooleanField(
        required=False,
        allow_null=True,
        help_text="Чи є позиція повністю віддаленою?"
    )
    is_hybrid = serializers.BooleanField(
        required=False,
        allow_null=True,
        help_text="Чи є позиція гібридною (комбінація віддаленої/офісної роботи)?"
    )
    link = serializers.URLField(
        required=False,
        allow_null=True,
        help_text="Посилання на вакансію на сайті"
    )
    level = serializers.CharField(
        required=False,
        allow_null=True,
        help_text="Рівень досвіду (наприклад, Junior, Middle, Senior, Lead)"
    )
    title = serializers.CharField(
        max_length=255,
        help_text="Назва вакансії"
    )

    class Meta:
        model = Vacancy
        fields = [
            'id', 'title', 'description', 'link', 'countries', 'cities', 'skills', 'categories',
            'languages', 'salary_min', 'salary_max', 'salary_currency', 'level', 'is_remote', 'is_hybrid'
        ]

    def validate_categories(self, value):
        if not value:
            raise serializers.ValidationError("Це поле є обов'язковим.")
        return value

    def validate(self, data):
        is_remote = data.get('is_remote')
        is_hybrid = data.get('is_hybrid')

        if is_remote and is_hybrid:
            raise serializers.ValidationError(
                "Вакансія не може бути одночасно повністю віддаленою і гібридною."
            )

        salary_min = data.get('salary_min')
        salary_max = data.get('salary_max')

        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            raise serializers.ValidationError({
                'salary_min': 'Мінімальна зарплата не може бути більшою за максимальну.',
                'salary_max': 'Максимальна зарплата не може бути меншою за мінімальну.'
            })

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        return data
