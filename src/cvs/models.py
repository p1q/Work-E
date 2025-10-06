import re
import uuid

from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField


def validate_name(value):
    if not re.match(r'^[a-zA-Zа-яА-ЯіїєґІЇЄҐ\- ]+$', value):
        raise ValidationError(_('Поле може містити лише літери, дефіс та пробіли.'))
    if len(value.strip()) == 0:
        raise ValidationError(_('Поле не може складатися лише з пробілів.'))


def validate_position(value):
    if len(value) > 120:
        raise ValidationError(_('Значення не може бути довшим за 120 символів.'))


def validate_overview(value):
    if len(value) > 2000:
        raise ValidationError(_('Огляд не може перевищувати 2000 символів.'))


def validate_hobbies(value):
    if len(value) > 1000:
        raise ValidationError(_('Хобі не може перевищувати 1000 символів.'))


def validate_date_order(start_date, end_date):
    if start_date and end_date and start_date > end_date:
        raise ValidationError(_('Дата початку не може бути пізніше дати завершення.'))


def validate_work_experience_position(value):
    if not (1 <= len(value) <= 120):
        raise ValidationError(_('Посада повинна містити від 1 до 120 символів.'))


def validate_work_experience_company(value):
    if not (1 <= len(value) <= 120):
        raise ValidationError(_('Назва компанії повинна містити від 1 до 120 символів.'))


def validate_education_major(value):
    if len(value) > 200:
        raise ValidationError(_('Спеціальність не може перевищувати 200 символів.'))


def validate_education_institution(value):
    if len(value) > 200:
        raise ValidationError(_('Навчальний заклад не може перевищувати 200 символів.'))


def validate_course_name(value):
    if len(value) > 200:
        raise ValidationError(_('Назва курсу не може перевищувати 200 символів.'))


def validate_course_provider(value):
    if len(value) > 200:
        raise ValidationError(_('Провайдер курсу не може перевищувати 200 символів.'))


def validate_skill_name(value):
    if len(value) > 100:
        raise ValidationError(_('Назва навички не може перевищувати 100 символів.'))


def validate_language_name(value):
    if len(value) > 100:
        raise ValidationError(_('Назва мови не може перевищувати 100 символів.'))


class WorkOptions(models.Model):
    countries = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True
    )
    cities = ArrayField(
        models.CharField(max_length=50),
        default=list,
        blank=True
    )
    is_office = models.BooleanField(null=True, blank=True)
    is_remote = models.BooleanField(null=True, blank=True)
    is_hybrid = models.BooleanField(null=True, blank=True)
    willing_to_relocate = models.BooleanField(null=True, blank=True)

    def __str__(self):
        return f"WorkOptions for CV"


class CV(models.Model):
    STATUS_CHOICES = [
        ('draft', _('Чернетка')),
        ('published', _('Опубліковано')),
    ]

    LOCALE_CHOICES = [
        ('uk-UA', 'uk-UA'),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cvs')
    position_target = models.CharField(max_length=120, blank=True, validators=[validate_position])
    personal_first_name = models.CharField(max_length=80, validators=[validate_name])
    personal_last_name = models.CharField(max_length=80, validators=[validate_name])
    personal_email = models.EmailField(validators=[EmailValidator()])
    personal_phone = PhoneNumberField(blank=True)
    personal_date_of_birth = models.DateField(null=True, blank=True)
    personal_gender = models.CharField(max_length=20, blank=True)
    personal_address_street = models.CharField(max_length=200, blank=True)
    personal_address_city = models.CharField(max_length=120)
    personal_address_postal_code = models.CharField(max_length=20, blank=True)
    personal_address_country = models.CharField(max_length=100)
    personal_address_country_code = models.CharField(max_length=2, blank=True)
    personal_overview = models.TextField(blank=True, validators=[validate_overview])
    personal_hobbies = models.TextField(blank=True, validators=[validate_hobbies])
    work_options = models.OneToOneField(WorkOptions, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    locale = models.CharField(max_length=10, choices=LOCALE_CHOICES, default='uk-UA')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    links_cv_file = models.CharField(max_length=255, blank=True)
    links_linkedin_url = models.URLField(blank=True)
    links_portfolio_url = models.URLField(blank=True)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=3, blank=True)
    analyzed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'personal_email'], name='unique_user_email_per_cv')
        ]

    def clean(self):
        super().clean()
        if self.salary_min and self.salary_max and self.salary_min > self.salary_max:
            raise ValidationError(_('Мінімальна зарплата не може бути більшою за максимальну.'))

    def save(self, *args, **kwargs):
        if self.personal_email:
            self.personal_email = self.personal_email.lower()
        super().save(*args, **kwargs)


class WorkExperience(models.Model):
    LEVEL_CHOICES = []

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='work_experiences')
    position = models.CharField(max_length=120, validators=[validate_work_experience_position])
    company = models.CharField(max_length=120, validators=[validate_work_experience_company])
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    responsibilities = models.TextField(blank=True)
    order_index = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        if self.end_date is None:
            self.is_current = True
        else:
            self.is_current = False
            validate_date_order(self.start_date, self.end_date)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Education(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='educations')
    major = models.CharField(max_length=200, blank=True, validators=[validate_education_major])
    institution = models.CharField(max_length=200, validators=[validate_education_institution])
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    order_index = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        validate_date_order(self.start_date, self.end_date)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=200, validators=[validate_course_name])
    provider = models.CharField(max_length=200, validators=[validate_course_provider])
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    order_index = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        validate_date_order(self.start_date, self.end_date)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)


class Skill(models.Model):
    LEVEL_CHOICES = [
        ('basic', _('Базовий')),
        ('intermediate', _('Середній')),
        ('advanced', _('Просунутий')),
        ('expert', _('Експерт')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100, validators=[validate_skill_name])
    description = models.TextField(blank=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, null=True, blank=True)
    order_index = models.PositiveIntegerField(default=0)


class Language(models.Model):
    LEVEL_CHOICES = [
        ('A1', 'A1'),
        ('A2', 'A2'),
        ('B1', 'B1'),
        ('B2', 'B2'),
        ('C1', 'C1'),
        ('C2', 'C2'),
        ('native', _('Рідна')),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='languages')
    name = models.CharField(max_length=100, validators=[validate_language_name])
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    description = models.TextField(blank=True)
    order_index = models.PositiveIntegerField(default=0)
