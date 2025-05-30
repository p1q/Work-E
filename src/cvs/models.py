from django.db import models
from django.core.validators import FileExtensionValidator


class CV(models.Model):
    full_name = models.CharField(max_length=255)
    email = models.EmailField()
    cv_file = models.FileField(
        upload_to='cvs/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'rtf'])],
        help_text='Upload your CV (pdf, doc, docx, rtf)'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.email})"
