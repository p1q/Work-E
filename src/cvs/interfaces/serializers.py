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
        # Step 1: size checks
        if file.size == 0:
            raise serializers.ValidationError("File cannot be empty.")
        if file.size > 1 * 1024 * 1024:
            raise serializers.ValidationError("Maximum allowed file size is 1MB.")

        # Step 2: extension check
        ext = os.path.splitext(file.name)[1].lower()
        if ext != '.pdf':
            raise serializers.ValidationError(f"Only PDF files are allowed.")

        # Step 3: PDF content validation
        try:
            self._validate_pdf(file)
        except Exception:
            raise serializers.ValidationError("Invalid or corrupted PDF file.")

        return file

    def _validate_pdf(self, file):
        from PyPDF2 import PdfReader
        file.seek(0)
        reader = PdfReader(file)

        if not reader.pages:
            raise ValueError("Empty PDF file")

        if reader.trailer.get("/Root", {}).get("/Names", {}).get("/EmbeddedFiles"):
            raise ValueError("PDF contains embedded files")

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
