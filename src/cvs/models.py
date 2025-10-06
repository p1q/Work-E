import uuid
from django.conf import settings
from django.contrib.postgres.fields import ArrayField
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField

from src.cvs.storage import CVFileStorage


def validate_name(value):
    if not value.strip():
        raise ValidationError('Поле не може складатися лише з пробілів.')
    if not all(c.isalpha() or c in ['-', ' '] for c in value):
        raise ValidationError('Поле може містити лише літери, дефіс та пробіли.')


def validate_date_order(start_date, end_date):
    if start_date and end_date and start_date > end_date:
        raise ValidationError('Дата початку не може бути пізніше дати завершення.')


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
        ('draft', 'Чернетка'),
        ('published', 'Опубліковано'),
    ]

    LOCALE_CHOICES = [
        ('uk-UA', 'uk-UA'),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cvs')

    first_name = models.CharField(max_length=80, validators=[validate_name])
    last_name = models.CharField(max_length=80, validators=[validate_name])
    email = models.EmailField(validators=[EmailValidator()])
    phone = PhoneNumberField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True)
    street = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=120)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100)
    country_code = models.CharField(max_length=2, blank=True)
    overview = models.TextField(blank=True)
    hobbies = models.TextField(blank=True)

    position_target = models.CharField(max_length=120, blank=True)
    work_options = models.OneToOneField(WorkOptions, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    locale = models.CharField(max_length=10, choices=LOCALE_CHOICES, default='uk-UA')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cv_file = models.FileField(upload_to='', storage=CVFileStorage(), blank=True)
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=3, blank=True)
    level = models.CharField(max_length=20, blank=True)
    categories = ArrayField(
        models.CharField(max_length=50),
        default=list,
        size=None
    )
    analyzed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'email'], name='unique_user_email_per_cv')
        ]

    def clean(self):
        super().clean()
        if self.salary_min and self.salary_max and self.salary_min > self.salary_max:
            raise ValidationError('Мінімальна зарплата не може бути більшою за максимальну.')

    def __str__(self):
        return f"CV #{self.id} for User {self.user_id}: {self.cv_file.name if self.cv_file else 'No File'}"

    @property
    def filename(self):
        return self.cv_file.name if self.cv_file else "No File"


class WorkExperience(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='work_experiences')
    position = models.CharField(max_length=120)
    company = models.CharField(max_length=120)
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


class Education(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='educations')
    major = models.CharField(max_length=200, blank=True)
    institution = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    order_index = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        validate_date_order(self.start_date, self.end_date)


class Course(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=200)
    provider = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    order_index = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        validate_date_order(self.start_date, self.end_date)


class Skill(models.Model):
    LEVEL_CHOICES = [
        ('basic', 'Базовий'),
        ('intermediate', 'Середній'),
        ('advanced', 'Просунутий'),
        ('expert', 'Експерт'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
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
        ('native', 'Рідна'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='languages')
    name = models.CharField(max_length=100)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)
    description = models.TextField(blank=True)
    order_index = models.PositiveIntegerField(default=0)
