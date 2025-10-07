from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework import serializers

from ..models import CV, WorkExperience, Education, Course, Skill, Language, Personal, Address, WorkOptions

User = get_user_model()


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ['id', 'street', 'city', 'postal_code', 'country']
        read_only_fields = ['id']


class WorkOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkOptions
        fields = ['id', 'countries', 'cities', 'is_office', 'is_remote', 'is_hybrid', 'willing_to_relocate']
        read_only_fields = ['id']


class PersonalSerializer(serializers.ModelSerializer):
    address = AddressSerializer(required=False)

    class Meta:
        model = Personal
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone',
            'date_of_birth', 'gender', 'address', 'overview', 'hobbies'
        ]
        read_only_fields = ['id']

    def validate_first_name(self, value):
        if not (1 <= len(value.strip()) <= 80):
            raise serializers.ValidationError("Ім'я має бути від 1 до 80 символів.")
        if not all(c.isalpha() or c in ['-', ' '] for c in value.strip()):
            raise serializers.ValidationError("Ім'я може містити лише літери, дефіс та пробіли.")
        return value.strip()

    def validate_last_name(self, value):
        if not (1 <= len(value.strip()) <= 80):
            raise serializers.ValidationError("Прізвище має бути від 1 до 80 символів.")
        if not all(c.isalpha() or c in ['-', ' '] for c in value.strip()):
            raise serializers.ValidationError("Прізвище може містити лише літери, дефіс та пробіли.")
        return value.strip()


class WorkExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkExperience
        fields = [
            'id', 'position', 'company', 'start_date', 'end_date',
            'is_current', 'responsibilities', 'order_index'
        ]
        read_only_fields = ['id', 'is_current']

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Дата початку не може бути пізніше дати завершення.")
        return data


class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = [
            'id', 'major', 'institution', 'start_date', 'end_date',
            'description', 'order_index'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Дата початку не може бути пізніше дати завершення.")
        return data


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            'id', 'name', 'provider', 'start_date', 'end_date',
            'description', 'order_index'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and start_date > end_date:
            raise ValidationError("Дата початку не може бути пізніше дати завершення.")
        return data


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'description', 'level', 'order_index']
        read_only_fields = ['id']


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ['id', 'name', 'level', 'description', 'order_index']
        read_only_fields = ['id']


class CVSerializer(serializers.ModelSerializer):
    personal = PersonalSerializer(required=False)
    work_experiences = WorkExperienceSerializer(many=True, required=False)
    educations = EducationSerializer(many=True, required=False)
    courses = CourseSerializer(many=True, required=False)
    skills = SkillSerializer(many=True, required=False)
    languages = LanguageSerializer(many=True, required=False)
    work_options = WorkOptionsSerializer(required=False)
    links = serializers.SerializerMethodField()
    salary = serializers.SerializerMethodField()

    class Meta:
        model = CV
        fields = [
            'id', 'user_id', 'personal', 'position_target',
            'work_experiences', 'work_options', 'educations', 'courses',
            'skills', 'languages', 'status', 'locale',
            'created_at', 'updated_at', 'links', 'salary',
            'analyzed'
        ]
        read_only_fields = ['id', 'user_id', 'created_at', 'updated_at', 'analyzed']

    def get_links(self, obj):
        return {
            'cv_file': obj.cv_file_name,
            'linkedin_url': obj.linkedin_url,
            'portfolio_url': obj.portfolio_url,
        }

    def get_salary(self, obj):
        return {
            'salary_min': obj.salary_min,
            'salary_max': obj.salary_max,
            'salary_currency': obj.salary_currency,
        }

    def create(self, validated_data):
        work_experiences_data = validated_data.pop('work_experiences', [])
        educations_data = validated_data.pop('educations', [])
        courses_data = validated_data.pop('courses', [])
        skills_data = validated_data.pop('skills', [])
        languages_data = validated_data.pop('languages', [])
        work_options_data = validated_data.pop('work_options', {})
        personal_data = validated_data.pop('personal', {})
        address_data = personal_data.pop('address', {})

        address = None
        if address_data:
            address = Address.objects.create(**address_data)

        if personal_data:
            if address:
                personal = Personal.objects.create(address=address, **personal_data)
            else:
                personal = Personal.objects.create(**personal_data)
            validated_data['personal'] = personal

        if work_options_data:
            work_options = WorkOptions.objects.create(**work_options_data)
            validated_data['work_options'] = work_options

        cv = CV.objects.create(**validated_data)

        for exp_data in work_experiences_data:
            WorkExperience.objects.create(cv=cv, **exp_data)
        for edu_data in educations_data:
            Education.objects.create(cv=cv, **edu_data)
        for course_data in courses_data:
            Course.objects.create(cv=cv, **course_data)
        for skill_data in skills_data:
            Skill.objects.create(cv=cv, **skill_data)
        for lang_data in languages_data:
            Language.objects.create(cv=cv, **lang_data)

        return cv

    def update(self, instance, validated_data):
        work_experiences_data = validated_data.pop('work_experiences', None)
        educations_data = validated_data.pop('educations', None)
        courses_data = validated_data.pop('courses', None)
        skills_data = validated_data.pop('skills', None)
        languages_data = validated_data.pop('languages', None)
        work_options_data = validated_data.pop('work_options', None)
        personal_data = validated_data.pop('personal', None)
        address_data = personal_data.pop('address', {}) if personal_data else {}

        if personal_data and instance.personal:
            if address_data and instance.personal.address:
                for attr, value in address_data.items():
                    setattr(instance.personal.address, attr, value)
                instance.personal.address.save()
            elif address_data and not instance.personal.address:
                address = Address.objects.create(**address_data)
                instance.personal.address = address

            for attr, value in personal_data.items():
                if attr != 'address':  # Skip address as it's handled separately
                    setattr(instance.personal, attr, value)
            instance.personal.save()
        elif personal_data and not instance.personal:
            address = Address.objects.create(**address_data) if address_data else None
            personal = Personal.objects.create(address=address, **personal_data)
            instance.personal = personal

        if work_options_data and instance.work_options:
            for attr, value in work_options_data.items():
                setattr(instance.work_options, attr, value)
            instance.work_options.save()
        elif work_options_data and not instance.work_options:
            work_options = WorkOptions.objects.create(**work_options_data)
            instance.work_options = work_options

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if work_experiences_data is not None:
            instance.work_experiences.all().delete()
            for exp_data in work_experiences_data:
                WorkExperience.objects.create(cv=instance, **exp_data)

        if educations_data is not None:
            instance.educations.all().delete()
            for edu_data in educations_data:
                Education.objects.create(cv=instance, **edu_data)

        if courses_data is not None:
            instance.courses.all().delete()
            for course_data in courses_data:
                Course.objects.create(cv=instance, **course_data)

        if skills_data is not None:
            instance.skills.all().delete()
            for skill_data in skills_data:
                Skill.objects.create(cv=instance, **skill_data)

        if languages_data is not None:
            instance.languages.all().delete()
            for lang_data in languages_data:
                Language.objects.create(cv=instance, **lang_data)

        return instance

    def validate_position_target(self, value):
        if value and len(value) > 120:
            raise serializers.ValidationError("Посада/цільова позиція не може перевищувати 120 символів.")
        return value

    def validate_overview(self, value):
        if value and len(value) > 2000:
            raise serializers.ValidationError("Огляд не може перевищувати 2000 символів.")
        return value

    def validate_hobbies(self, value):
        if value and len(value) > 1000:
            raise serializers.ValidationError("Хобі не може перевищувати 1000 символів.")
        return value

    def validate(self, data):
        salary_min = data.get('salary_min')
        salary_max = data.get('salary_max')
        if salary_min is not None and salary_max is not None and salary_min > salary_max:
            raise serializers.ValidationError(
                {'salary_min': 'Мінімальна зарплата не може бути більшою за максимальну.'})
        return data


class AnalyzeCVRequestSerializer(serializers.Serializer):
    cv_id = serializers.UUIDField(required=True)


class AnalyzeCVResponseSerializer(serializers.Serializer):
    message = serializers.CharField()


class CoverLetterSerializer(serializers.Serializer):
    coverLetter = serializers.CharField()
    job_description = serializers.CharField()


class CVGenerationSerializer(serializers.Serializer):
    name = serializers.CharField()
    lastname = serializers.CharField()
    experience = serializers.ListField(child=serializers.DictField())
    skills = serializers.ListField(child=serializers.CharField())
    education = serializers.ListField(child=serializers.DictField())


class DownloadCVRequestSerializer(serializers.Serializer):
    cv_id = serializers.UUIDField(required=True)


class ExtractTextFromCVRequestSerializer(serializers.Serializer):
    cv_id = serializers.UUIDField(required=True)


class ExtractTextFromCVResponseSerializer(serializers.Serializer):
    text = serializers.CharField()
    method_used = serializers.CharField()
    extracted_cv_id = serializers.UUIDField()
    filename = serializers.CharField()
