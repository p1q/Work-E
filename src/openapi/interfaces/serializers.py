from rest_framework import serializers


class MessageSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[('user', 'User'), ('assistant', 'Assistant'), ('system', 'System')])
    content = serializers.CharField()


class OpenAPIChatRequestSerializer(serializers.Serializer):
    messages = MessageSerializer(many=True)
    model = serializers.CharField(max_length=100, required=False, allow_blank=True,
                                  default='')
    chatId = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')

    def validate_messages(self, value):
        if not value:
            raise serializers.ValidationError("Messages list cannot be empty.")
        return value


class OpenAPIChatResponseSerializer(serializers.Serializer):
    ai_response = serializers.DictField(child=serializers.CharField())
