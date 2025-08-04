import os

from django.conf import settings
from django.contrib.auth import get_user_model
from pikepdf import Pdf, PdfError
from rest_framework import serializers

from ..models import CV

User = get_user_model()


class CVGenerationSerializer(serializers.Serializer):
    name = serializers.CharField()
    lastname = serializers.CharField()
    experience = serializers.ListField(child=serializers.DictField())
    skills = serializers.ListField(child=serializers.DictField())
    education = serializers.ListField(child=serializers.DictField())


class CoverLetterSerializer(serializers.Serializer):
    coverLetter = serializers.CharField()
    job_description = serializers.CharField()


class CVSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    filename = serializers.CharField(read_only=True)
    email = serializers.EmailField(write_only=True)
    cv_file = serializers.FileField(write_only=True)

    class Meta:
        model = CV
        fields = ['id', 'user', 'email', 'filename', 'cv_file', 'uploaded_at']
        read_only_fields = ['id', 'user', 'filename', 'uploaded_at']

    def validate_cv_file(self, file):
        # 1) Size checks
        if file.size == 0:
            raise serializers.ValidationError("File cannot be empty.")
        if file.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            max_mb = settings.FILE_UPLOAD_MAX_MEMORY_SIZE // (1024 * 1024)
            raise serializers.ValidationError(f"Maximum allowed file size is {max_mb}MB.")

        # 2) Extension check
        ext = os.path.splitext(file.name)[1].lower()
        if ext != '.pdf':
            raise serializers.ValidationError("Only PDF files are allowed.")

        # 3) PDF content validation via pikepdf
        try:
            self._validate_pdf_with_pikepdf(file)
        except serializers.ValidationError:
            raise
        except Exception:
            raise serializers.ValidationError("Invalid or corrupted PDF file.")
        finally:
            file.seek(0)

        return file

    def _validate_pdf_with_pikepdf(self, file):
        file.seek(0)
        try:
            pdf = Pdf.open(file, allow_overwriting_input=False)
        except PdfError:
            raise serializers.ValidationError("Invalid or corrupted PDF file.")

        # Empty PDF?
        if len(pdf.pages) == 0:
            raise serializers.ValidationError("Empty PDF file.")

        # Check for any embedded files/attachments
        try:
            # QPDF exposes embedded files under pdf.attachments
            attachments = list(pdf.attachments.keys())
        except Exception:
            # if attribute missing, assume no attachments
            attachments = []

        if attachments:
            names = ", ".join(attachments)
            raise serializers.ValidationError(f"PDF contains embedded files: {names}")

    def create(self, validated_data):
        email = validated_data.pop('email')
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'email': f'User with email \"{email}\" not found.'
            })
        return CV.objects.create(user=user, **validated_data)


class ExtractTextFromCVRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(help_text="ID користувача")


class ExtractTextFromCVResponseSerializer(serializers.Serializer):
    text = serializers.CharField(help_text="Витягнутий текст з PDF")
    method = serializers.CharField(help_text="Метод витягнення: 'pdf_text'")
    cv_id = serializers.IntegerField(help_text="ID використаного CV")
    filename = serializers.CharField(help_text="Ім'я файлу CV")
