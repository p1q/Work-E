from rest_framework import serializers


class LanguageDetectSerializer(serializers.Serializer):
    text = serializers.CharField()
