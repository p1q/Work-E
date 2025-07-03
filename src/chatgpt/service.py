import openai
import tiktoken
from django.conf import settings

openai.api_key = settings.OPENAI_API_KEY

PRICING = {
    "gpt-3.5-turbo": {"input": 0.0015, "output": 0.0020},
    "gpt-4": {"input": 0.0300, "output": 0.0600},
}


def generate_chat_response(prompt: str, model: str = "gpt-3.5-turbo", temperature: float = 0.7) -> str:
    response = openai.ChatCompletion.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
    )
    return response.choices[0].message.content


def count_tokens(text: str, model: str) -> int:
    try:
        enc = tiktoken.encoding_for_model(model)
    except KeyError:
        enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def estimate_cost(prompt: str, model: str, max_tokens: int = 0) -> dict:
    prompt_tokens = count_tokens(prompt, model)
    rates = PRICING.get(model, {"input": 0.0, "output": 0.0})

    cost_prompt = prompt_tokens * rates["input"] / 1000
    cost_completion = max_tokens * rates["output"] / 1000
    total_cost = cost_prompt + cost_completion

    return {
        "model": model,
        "prompt_tokens": prompt_tokens,
        "estimated_completion_tokens": max_tokens,
        "cost_prompt": round(cost_prompt, 6),
        "cost_completion": round(cost_completion, 6),
        "total_cost": round(total_cost, 6),
        "pricing": rates,
    }
