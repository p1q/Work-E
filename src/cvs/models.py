from django.db import models
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from phonenumber_field.modelfields import PhoneNumberField
from src.cvs.storage import CVFileStorage
import uuid
from django.contrib.postgres.fields import ArrayField

User = get_user_model()


def validate_name(value):
    if not value.strip():
        raise ValidationError('Поле не може складатися лише з пробілів.')
    if not all(c.isalpha() or c in ['-', ' '] for c in value):
        raise ValidationError('Поле може містити лише літери, дефіс та пробіли.')


def validate_date_order(start_date, end_date):
    if start_date and end_date and start_date > end_date:
        raise ValidationError('Дата початку не може бути пізніше дати завершення.')


def validate_personal_name(value):
    if not value.strip():
        raise ValidationError('Поле не може бути порожнім.')
    if len(value) > 80:
        raise ValidationError('Поле не може перевищувати 80 символів.')
    if not all(c.isalpha() or c in ['-', ' '] for c in value.strip()):
        raise ValidationError('Поле може містити лише літери, дефіс та пробіли.')


class WorkOptions(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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

    def clean(self):
        super().clean()
        if self.is_remote and self.is_hybrid:
            raise ValidationError("Посада не може бути одночасно повністю віддаленою і гібридною.")


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    street = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=120, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)

    def __str__(self):
        parts = [self.street, self.city, self.postal_code, self.country]
        return ", ".join([part for part in parts if part])


class Personal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=80, validators=[validate_personal_name])
    last_name = models.CharField(max_length=80, validators=[validate_personal_name])
    email = models.EmailField()
    phone = PhoneNumberField(blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    address = models.OneToOneField(Address, on_delete=models.SET_NULL, null=True, blank=True)
    overview = models.TextField(max_length=2000, blank=True)
    hobbies = models.TextField(max_length=1000, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class CV(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
    ]

    id = models.BigAutoField(primary_key=True)  # Temporarily keep as BigAutoField to avoid casting issues
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cvs')
    cv_file = models.FileField(upload_to='cvs/', storage=CVFileStorage, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    locale = models.CharField(max_length=10, default='uk-UA')
    analyzed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Personal Information (as nested object)
    personal = models.OneToOneField(Personal, on_delete=models.SET_NULL, null=True, blank=True)

    # Position Target
    position_target = models.CharField(max_length=120, blank=True)

    # Work Options
    work_options = models.OneToOneField(WorkOptions, on_delete=models.SET_NULL, null=True, blank=True)

    # Links
    linkedin_url = models.URLField(blank=True)
    portfolio_url = models.URLField(blank=True)

    # Salary
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=3, blank=True)

    def clean(self):
        super().clean()
        if self.salary_min is not None and self.salary_max is not None and self.salary_min > self.salary_max:
            raise ValidationError('Мінімальна зарплата не може бути більшою за максимальну.')

    @property
    def cv_file_name(self):
        return self.cv_file.name.split('/')[-1] if self.cv_file.name else ''

    def __str__(self):
        first_name = self.personal.first_name if self.personal else 'Unknown'
        last_name = self.personal.last_name if self.personal else 'Unknown'
        return f"CV of {first_name} {last_name} ({self.user.email})"


class WorkExperience(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='work_experiences')
    position = models.CharField(max_length=120)
    company = models.CharField(max_length=120)
    start_date = models.DateField()  # Format YYYY-MM (stored as first day of month)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    responsibilities = models.TextField(blank=True)
    order_index = models.PositiveIntegerField(default=0)

    def clean(self):
        super().clean()
        validate_date_order(self.start_date, self.end_date)
        if not (1 <= len(self.position) <= 120):
            raise ValidationError({'position': 'Посада має бути від 1 до 120 символів.'})
        if not (1 <= len(self.company) <= 120):
            raise ValidationError({'company': 'Компанія має бути від 1 до 120 символів.'})

    def save(self, *args, **kwargs):
        self.is_current = self.end_date is None
        super().save(*args, **kwargs)


class Education(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='educations')
    major = models.CharField(max_length=200)
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
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    level = models.CharField(max_length=12, choices=LEVEL_CHOICES, null=True, blank=True)
    order_index = models.PositiveIntegerField(default=0)


class Language(models.Model):
    LEVEL_CHOICES = [
        ('A1', 'A1'),
        ('A2', 'A2'),
        ('B1', 'B1'),
        ('B2', 'B2'),
        ('C1', 'C1'),
        ('C2', 'C2'),
        ('native', 'Native'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cv = models.ForeignKey(CV, on_delete=models.CASCADE, related_name='languages')
    name = models.CharField(max_length=50)
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, null=True, blank=True)
    description = models.TextField(blank=True)
    order_index = models.PositiveIntegerField(default=0)
