import os
from rest_framework import serializers
from django.contrib.auth import get_user_model
from cvs.models import CV
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

User = get_user_model()


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
        # Step 1: size checks
        if file.size == 0:
            raise serializers.ValidationError("File cannot be empty.")
        if file.size > settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            max_mb = settings.FILE_UPLOAD_MAX_MEMORY_SIZE // (1024 * 1024)
            raise serializers.ValidationError(f"Maximum allowed file size is {max_mb}MB.")

        # Step 2: extension check
        ext = os.path.splitext(file.name)[1].lower()
        if ext != '.pdf':
            raise serializers.ValidationError("Only PDF files are allowed.")

        # Step 3: PDF content validation
        try:
            self._validate_pdf(file)
        except serializers.ValidationError:
            # пробрасываем уже готовое сообщение
            raise
        except Exception:
            raise serializers.ValidationError("Invalid or corrupted PDF file.")

        return file

    def _validate_pdf(self, file):
        file.seek(0)
        try:
            reader = PdfReader(file)
        except PdfReadError:
            raise serializers.ValidationError("Invalid or corrupted PDF file.")

        # Проверка на пустой PDF
        if not getattr(reader, 'pages', None):
            raise serializers.ValidationError("Empty PDF file.")

        # Проверка на EmbeddedFiles
        try:
            root = reader.trailer["/Root"]
            names = root.get("/Names")
            if names and names.get("/EmbeddedFiles"):
                raise serializers.ValidationError("PDF contains embedded files.")
        except Exception:
            # Игнорируем любые непредвиденные структуры
            pass
        finally:
            file.seek(0)

    def create(self, validated_data):
        email = validated_data.pop('email')
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'email': f'User with email "{email}" not found.'
            })
        return CV.objects.create(user=user, **validated_data)
