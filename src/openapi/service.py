import requests
from django.conf import settings
import json
import logging

from src.openapi.prompts import VACANCY_ANALYSIS_PROMPT
from src.settings import OPENAPI_AI_URL

logger = logging.getLogger(__name__)

OPENAPI_AI_MODEL = getattr(settings, 'OPENAPI_AI_MODEL', 'qwen3-coder-plus')
OPENAPI_AI_TIMEOUT = getattr(settings, 'OPENAPI_AI_TIMEOUT', 30)


def call_openapi_ai(messages: list, model: str = None, chat_id: str = "", stream: bool = False,
                    temperature: float = 0.7) -> dict:
    if not OPENAPI_AI_URL:
        logger.error("OPENAPI_AI_URL не налаштовано в settings.")
        return {}

    if model is None:
        model = OPENAPI_AI_MODEL

    headers = {'Content-Type': 'application/json'}

    data = {
        "model": model,
        "messages": messages,
        "chatId": chat_id,
        "stream": stream,
        "temperature": temperature
    }

    try:
        logger.debug(f"Calling OpenAPI AI at {OPENAPI_AI_URL} with model {model} and temperature {temperature}")
        response = requests.post(OPENAPI_AI_URL, headers=headers, json=data, timeout=OPENAPI_AI_TIMEOUT)
        response.raise_for_status()
        ai_response = response.json()
        logger.info("OpenAPI AI call successful.")
        return ai_response
    except requests.exceptions.Timeout:
        logger.error(f"Timeout error calling OpenAPI AI (timeout={OPENAPI_AI_TIMEOUT}s)")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error calling OpenAPI AI: {e}")
    except json.JSONDecodeError as e:
        logger.error(
            f"Error decoding JSON from OpenAPI AI response: {e}. Raw response text: {response.text[:500] if 'response' in locals() else 'N/A'}")
    except Exception as e:
        logger.error(f"Unexpected error in OpenAPI AI call: {e}", exc_info=True)
    return {}


def extract_vacancy_data(description_text: str) -> dict:
    prompt = VACANCY_ANALYSIS_PROMPT.format(vacancy_text=description_text)

    messages = [{"role": "user", "content": prompt}]
    raw_response = call_openapi_ai(messages=messages, temperature=0.1)

    if not raw_response:
        logger.warning("OpenAPI AI returned no data for vacancy extraction.")
        return {}

    try:
        content = ""
        if 'choices' in raw_response and raw_response['choices']:
            content = raw_response['choices'][0].get('message', {}).get('content', '')
        elif 'message' in raw_response:
            content = raw_response.get('message', {}).get('content', '')
        else:
            logger.warning(
                f"Unexpected AI response structure for vacancy extraction: {list(raw_response.keys()) if isinstance(raw_response, dict) else type(raw_response)}")
            content = str(raw_response)

        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]

        extracted_data = json.loads(content)
        logger.info("OpenAPI AI data extracted successfully for vacancy description.")
        return extracted_data

    except json.JSONDecodeError as e:
        logger.error(
            f"Error decoding JSON from OpenAPI AI response content for vacancy: {e}. Raw content snippet: {content[:200] if content else 'N/A'}")
    except Exception as e:
        logger.error(f"Unexpected error processing OpenAPI AI response for vacancy: {e}", exc_info=True)

    return {}
