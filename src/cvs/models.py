import os
from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator


class CV(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cvs'
    )
    cv_file = models.FileField(
        upload_to='cv-files/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text='Upload your CV (PDF only)'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    skills = models.TextField(blank=True, null=True)
    tools = models.TextField(blank=True, null=True)
    responsibilities = models.TextField(blank=True, null=True)
    languages = models.TextField(blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    salary_range = models.CharField(max_length=255, blank=True, null=True)

    english_level = models.CharField(max_length=50, blank=True, null=True,
                                     help_text="User's English level (e.g., A1, A2, B1, B2, C1, C2)")
    willing_to_relocate = models.BooleanField(default=False, help_text="Is the user willing to relocate?")

    def __str__(self):
        return f"CV #{self.id} for User {self.user_id}: {os.path.basename(self.cv_file.name)}"

    @property
    def filename(self):
        return os.path.basename(self.cv_file.name)
