import os
from rest_framework import serializers
from django.contrib.auth import get_user_model
from cvs.models import CV

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
        if file.size == 0:
            raise serializers.ValidationError("File cannot be empty.")
        if file.size > 1 * 1024 * 1024:
            raise serializers.ValidationError("Maximum allowed file size is 1MB.")

        ext = os.path.splitext(file.name)[1].lower()
        valid_extensions = ['.pdf', '.doc', '.docx', '.rtf']
        if ext not in valid_extensions:
            raise serializers.ValidationError(f"Unsupported file extension: {ext}")

        try:
            if ext == '.pdf':
                self._validate_pdf(file)
            elif ext == '.docx':
                self._validate_docx(file)
            elif ext == '.doc':
                self._validate_doc(file)
            elif ext == '.rtf':
                self._validate_rtf(file)
        except Exception:
            raise serializers.ValidationError("File content does not match declared type or is corrupted.")

        return file

    def _validate_pdf(self, file):
        from PyPDF2 import PdfReader
        file.seek(0)
        reader = PdfReader(file)
        if not reader.pages:
            raise ValueError("Empty PDF file")
        file.seek(0)

    def _validate_docx(self, file):
        import zipfile
        file.seek(0)
        if not zipfile.is_zipfile(file):
            raise ValueError("Not a valid .docx file")
        with zipfile.ZipFile(file) as docx_zip:
            if 'word/document.xml' not in docx_zip.namelist():
                raise ValueError("Missing content in .docx")
        file.seek(0)

    def _validate_doc(self, file):
        file.seek(0)
        header = file.read(8)
        if not header.startswith(b'\xD0\xCF\x11\xE0'):
            raise ValueError("Not a valid .doc file")
        file.seek(0)

    def _validate_rtf(self, file):
        file.seek(0)
        header = file.read(10)
        if not header.lstrip().startswith(b'{\\rtf'):
            raise ValueError("Not a valid RTF file")
        file.seek(0)

    def create(self, validated_data):
        email = validated_data.pop('email')
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({
                'email': f'User with email \"{email}\" not found.'
            })
        return CV.objects.create(user=user, **validated_data)
