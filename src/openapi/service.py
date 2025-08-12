import requests
from django.conf import settings
import json
import logging

from src.settings import OPENAPI_AI_URL

logger = logging.getLogger(__name__)

OPENAPI_AI_MODEL = getattr(settings, 'OPENAPI_AI_MODEL', 'qwen-max-latest')
OPENAPI_AI_TIMEOUT = getattr(settings, 'OPENAPI_AI_TIMEOUT', 30)


def call_openapi_ai(messages: list, model: str = None, chat_id: str = "", stream: bool = False) -> dict:
    if model is None:
        model = OPENAPI_AI_MODEL

    headers = {
        'Content-Type': 'application/json',
    }
    data = {
        "model": model,
        "messages": messages,
        "chatId": chat_id,
        "stream": stream
    }

    try:
        logger.debug(f"Calling OpenAPI AI at {OPENAPI_AI_URL} with model {model}")
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
    prompt = f"""
    Analyze the following job vacancy description and extract the specified parameters.
    Provide the result as a JSON object with the exact keys listed below.
    If a parameter cannot be determined or is not mentioned, leave its value as null or an empty list/object.

    Parameters to extract:
    1. skills: Array of strings. Key technical skills,  technologies, specific tools, and competencies mentioned (e.g., ["Python", "Django", "Git", "Docker", "AWS", "REST API"]).
    2. languages: Array of objects. Languages required, including proficiency level if mentioned. Format: [{{"language": "English", "level": "B2"}}, ...]. If no level, use null for level.
    3. location: String. The candidate's location mentioned (e.g., "Kyiv", "Lviv", "Odesa"). Only city/town here, do not add area or country!
    4. salary_range: String. The salary range mentioned, in the format "min-max currency" (e.g., "50000-70000 UAH", "60000 EUR"). If not specified, null.
    5. level: String. The experience level required (e.g., "Junior", "Middle", "Senior", "Lead"). If not specified, null.
    6. english_level: String. The required English proficiency level (e.g., "A1", "A2", "B1", "B2", "C1", "C2"). If not specified, null.
    7. is_remote: Boolean. Is the position fully remote? (true/false). If not specified or unclear, null.
    8. is_hybrid: Boolean. Is the position hybrid (mix of remote/office)? (true/false). If not specified or unclear, null.
    9. willing_to_relocate: Boolean. Is the candidate expected to relocate? (true/false). If not specified or unclear, null.
    10. responsibilities: Array of strings. Key responsibilities listed (e.g., ["Develop web applications", "Write unit tests"]).

    Job Description:
    {description_text}

    JSON Output:
    """

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
