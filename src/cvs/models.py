from django.db import models
from django.conf import settings
from django.core.validators import FileExtensionValidator
import os


class CV(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cvs'
    )
    cv_file = models.FileField(
        upload_to=settings.CV_FILES_PATH,
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'rtf'])],
        help_text='Upload your CV (pdf, doc, docx, rtf)'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CV #{self.id} for User {self.user_id}: {os.path.basename(self.cv_file.name)}"

    @property
    def filename(self):
        return os.path.basename(self.cv_file.name)
