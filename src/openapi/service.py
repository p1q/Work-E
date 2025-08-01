import requests
from django.conf import settings
import json
import logging

logger = logging.getLogger(__name__)

OPENAPI_AI_URL = getattr(settings, 'OPENAPI_AI_URL', 'http://192.168.1.214:3264/api/chat/')
OPENAPI_AI_MODEL = getattr(settings, 'OPENAPI_AI_MODEL', 'qwen-max-latest')
OPENAPI_AI_TIMEOUT = getattr(settings, 'OPENAPI_AI_TIMEOUT', 30)


def extract_vacancy_data(description_text: str) -> dict:
    """
    Отправляет запрос к OpenAPI-совместимому ИИ для извлечения данных из описания вакансии.
    Возвращает словарь с извлеченными данными или пустой словарь в случае ошибки.
    """
    prompt = f"""
    Analyze the following job vacancy description and extract the specified parameters.
    Provide the result as a JSON object with the exact keys listed below.
    If a parameter cannot be determined or is not mentioned, leave its value as null or an empty list/object.

    Parameters to extract:
    1. skills: Array of strings. Key technical skills and competencies required (e.g., ["Python", "Django", "REST API"]).
    2. tools: Array of strings. Specific tools, technologies, or platforms mentioned (e.g., ["Git", "Docker", "AWS"]).
    3. languages: Array of objects. Languages required, including proficiency level if mentioned. Format: [{{"language": "English", "level": "B2"}}, ...]. If no level, use null for level.
    4. location_field: String. The primary location or work arrangement mentioned (e.g., "Kyiv, Ukraine", "Remote", "Hybrid: Kyiv or Remote").
    5. salary_range: String. The salary range mentioned, in the format "min-max currency" (e.g., "50000-70000 UAH", "60000 EUR", "Negotiable"). If not specified, null.
    6. level: String. The experience level required (e.g., "Junior", "Middle", "Senior", "Lead"). If not specified, null.
    7. english_level_required: String. The required English proficiency level (e.g., "A1", "A2", "B1", "B2", "C1", "C2"). If not specified, null.
    8. is_remote: Boolean. Is the position fully remote? (true/false). If not specified or unclear, null.
    9. is_hybrid: Boolean. Is the position hybrid (mix of remote/office)? (true/false). If not specified or unclear, null.
    10. willing_to_relocate: Boolean. Is the candidate expected to relocate? (true/false). If not specified or unclear, null.
    11. responsibilities: Array of strings. Key responsibilities listed (e.g., ["Develop web applications", "Write unit tests"]).

    Job Description:
    {description_text}

    JSON Output:
    """

    headers = {
        'Content-Type': 'application/json',
        # 'Authorization': f'Bearer {{settings.OPENAPI_AI_KEY}}' # Если нужна авторизация
    }

    data = {
        "model": OPENAPI_AI_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.1,
    }

    try:
        logger.debug(f"Calling OpenAPI AI at {{OPENAPI_AI_URL}} with model {{OPENAPI_AI_MODEL}}")
        response = requests.post(OPENAPI_AI_URL, headers=headers, json=data, timeout=OPENAPI_AI_TIMEOUT)
        response.raise_for_status()
        ai_response = response.json()

        content = ai_response.get('choices', [{{}}])[0].get('message', {{}}).get('content', '{{}}')

        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]

        extracted_data = json.loads(content)
        logger.info(f"OpenAPI AI data extracted successfully for description snippet.")
        return extracted_data

    except requests.exceptions.Timeout:
        logger.error(f"Timeout error calling OpenAPI AI (timeout={{OPENAPI_AI_TIMEOUT}}s)")
    except requests.exceptions.RequestException as e:
        logger.error(f"Network error calling OpenAPI AI: {{e}}")
    except json.JSONDecodeError as e:
        logger.error(
            f"Error decoding JSON from OpenAPI AI response: {{e}}. Raw content snippet: {{content[:200] if content else 'N/A'}}")
    except Exception as e:
        logger.error(f"Unexpected error in OpenAPI AI data extraction: {{e}}",
                     exc_info=True)

    return {{}}
