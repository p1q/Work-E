from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.conf import settings

username_validator = RegexValidator(
    regex=r'^[A-Za-z0-9._-]+$',
    message=_('Username may contain only letters, numbers, dots, underscores and hyphens.')
)


class User(AbstractUser):
    # Basic user info
    username = models.CharField(
        _('username'),
        max_length=30,
        unique=True,
        help_text=_('Required. 30 characters or fewer. Letters, digits, dots, underscores and hyphens only.'),
        error_messages={'unique': _("A user with that username already exists.")},
    )

    # OAuth fields
    google_id = models.CharField(_('Google ID'), max_length=255, unique=True, null=True, blank=True)
    linkedin_id = models.CharField(_('LinkedIn ID'), max_length=255, unique=True, null=True, blank=True)
    avatar_url = models.URLField(_('Avatar URL'), max_length=1000, blank=True, null=True)

    # Profile fields (merged from UserProfile)
    overview = models.TextField(blank=True, null=True)
    hobbies = models.TextField(blank=True, null=True)
    motivation_letter = models.TextField(blank=True, null=True)
    linkedin = models.URLField(max_length=500, blank=True, null=True)
    github = models.URLField(max_length=500, blank=True, null=True)
    ip = models.GenericIPAddressField(blank=True, null=True)

    # List fields stored as JSON
    programming_languages = models.JSONField(default=list, blank=True)  # ["Python", "JS"]
    skills = models.JSONField(default=list, blank=True)  # ["Django", "React"]

    # Personal info can remain a separate model if you need one-to-one detailed structure
    personal_info = models.OneToOneField(
        "PersonalInfo",
        on_delete=models.CASCADE,
        related_name="user",
        null=True,
        blank=True
    )

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class PersonalInfo(models.Model):
    desired_position = models.CharField(max_length=255, blank=True, null=True)
    first_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(unique=True, max_length=255)
    phone = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.desired_position})"

class Experience(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="experiences",
        null=True,   # allow NULL for existing rows
        blank=True
    )
    position = models.CharField(max_length=255, blank=True, null=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.position} at {self.company}"


class Education(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="education",
        null=True,
        blank=True
    )
    specialization = models.CharField(max_length=255, blank=True, null=True)
    institution = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.specialization} at {self.institution}"


class Course(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses",
        null=True,
        blank=True
    )
    specialization = models.CharField(max_length=255, blank=True, null=True)
    institution = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.specialization} ({self.institution})"


class Language(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="foreign_languages",
        null=True,
        blank=True
    )

    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"
    FLUENT = "Fluent"
    NATIVE = "Native"

    LEVEL_CHOICES = [
        (BEGINNER, "Beginner"),
        (INTERMEDIATE, "Intermediate"),
        (ADVANCED, "Advanced"),
        (FLUENT, "Fluent"),
        (NATIVE, "Native"),
    ]

    name = models.CharField(max_length=100, blank=True, null=True)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.level})"