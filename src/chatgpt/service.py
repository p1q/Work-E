import openai
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY


def generate_chat_response(prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> str:
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )

    return response.choices[0].message.content
