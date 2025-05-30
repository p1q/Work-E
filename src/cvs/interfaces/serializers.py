from rest_framework import serializers
from cvs.models import CV


class CVSerializer(serializers.ModelSerializer):
    class Meta:
        model = CV
        fields = ['id', 'full_name', 'email', 'cv_file', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
