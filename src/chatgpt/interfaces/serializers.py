from rest_framework import serializers


class ChatGPTRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField(help_text="Your request")
    model = serializers.CharField(default="gpt-3.5-turbo", help_text="OpenAI model ID")
    temperature = serializers.FloatField(default=0.7, help_text="Generation temperature")


class ChatGPTResponseSerializer(serializers.Serializer):
    response = serializers.CharField(help_text="Model response text")
