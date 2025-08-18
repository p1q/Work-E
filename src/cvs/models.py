import os
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.contrib.postgres.fields import ArrayField


class CV(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cvs')
    cv_file = models.FileField(upload_to='cv-files/', validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
                               help_text='Upload your CV (PDF only)')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    analyzed = models.BooleanField(default=False)

    level = models.CharField(max_length=20, blank=True, null=True)
    categories = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    countries = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    cities = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    is_remote = models.BooleanField(null=True, blank=True)
    is_hybrid = models.BooleanField(null=True, blank=True)
    willing_to_relocate = models.BooleanField(null=True, blank=True)
    languages_detailed = models.JSONField(null=True, blank=True)
    skills_detailed = ArrayField(models.CharField(max_length=100), default=list, blank=True)
    salary_min = models.PositiveIntegerField(null=True, blank=True)
    salary_max = models.PositiveIntegerField(null=True, blank=True)
    salary_currency = models.CharField(max_length=3, null=True, blank=True)

    def __str__(self):
        return f"CV #{self.id} for User {self.user_id}: {os.path.basename(self.cv_file.name)}"

    @property
    def filename(self):
        return os.path.basename(self.cv_file.name)

    class Meta:
        pass
