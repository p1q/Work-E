from rest_framework import serializers


class ChatGPTRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField(help_text="Your request to the model")
    model = serializers.CharField(default="gpt-3.5-turbo", help_text="OpenAI model ID")
    temperature = serializers.FloatField(default=0.7, help_text="Generation temperature")


class ChatGPTResponseSerializer(serializers.Serializer):
    response = serializers.CharField(help_text="Model response text")


class ChatGPTPlanRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField(help_text="Prompt text to be analyzed")
    model = serializers.CharField(default="gpt-3.5-turbo", help_text="OpenAI model ID")
    max_tokens = serializers.IntegerField(
        default=0,
        help_text="Maximum number of tokens expected in the response"
    )


class ChatGPTPlanResponseSerializer(serializers.Serializer):
    model = serializers.CharField(help_text="OpenAI model ID")
    prompt_tokens = serializers.IntegerField(help_text="Number of tokens in the prompt")
    estimated_completion_tokens = serializers.IntegerField(help_text="Expected number of tokens in the response")
    cost_prompt = serializers.FloatField(help_text="Estimated cost of prompt tokens in USD")
    cost_completion = serializers.FloatField(help_text="Estimated cost of completion tokens in USD")
    total_cost = serializers.FloatField(help_text="Estimated total cost in USD")
    pricing = serializers.DictField(help_text="Model pricing per 1,000 tokens in USD")
