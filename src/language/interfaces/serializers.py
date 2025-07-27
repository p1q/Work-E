from rest_framework import serializers


class LanguageDetectSerializer(serializers.Serializer):
    text = serializers.CharField()


class LanguageDetectResponseSerializer(serializers.Serializer):
    language = serializers.CharField()
    confidence = serializers.FloatField()
