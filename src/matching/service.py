import requests
from django.conf import settings
import json
import logging
from src.openapi.prompts import VACANCY_ANALYSIS_PROMPT
from src.settings import OPENAPI_AI_URL

logger = logging.getLogger(__name__)
OPENAPI_AI_MODEL = getattr(settings, 'OPENAPI_AI_MODEL', 'qwen-max-latest')

WEIGHTS = {
    'skills': 0.25,
    'tools': 0.15,
    'responsibilities': 0.20,
    'languages': 0.15,
    'location': 0.15,
    'salary': 0.10,
}


def extract_vacancy_data(description_text: str) -> dict:
    logger.info("Sending vacancy text to OpenAPI AI for data extraction.")
    prompt = VACANCY_ANALYSIS_PROMPT.format(vacancy_text=description_text)

    payload = {
        "model": OPENAPI_AI_MODEL,
        "input": {
            "messages": [
                {"role": "system",
                 "content": "You are a helpful assistant that extracts structured data from job vacancy descriptions."},
                {"role": "user", "content": prompt}
            ]
        }
    }

    headers = {"Authorization": f"Bearer {settings.OPENAPI_AI_API_KEY}", "Content-Type": "application/json"}
    try:
        response = requests.post(OPENAPI_AI_URL, headers=headers, json=payload)
        response.raise_for_status()
        response_data = response.json()
        logger.info("Received response from OpenAPI AI.")

        content = response_data.get("output", {}).get("choices", [{}])[0].get("message", {}).get("content", "")
        if not content:
            logger.error("Empty 'content' in OpenAPI AI response.")
            return {}

        if content.startswith("```json"):
            json_str = content[7:]
            if json_str.endswith("```"):
                json_str = json_str[:-3]
        elif content.startswith("```"):
            json_str = content.strip("` \n")
        else:
            json_str = content

        extracted_data = json.loads(json_str)
        logger.info("OpenAPI AI data extracted successfully for vacancy description.")
        return extracted_data

    except json.JSONDecodeError as e:
        logger.error(
            f"Error decoding JSON from OpenAPI AI response content for vacancy: {e}. Raw content snippet: {content[:200] if content else 'N/A'}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error processing OpenAPI AI response for vacancy: {e}", exc_info=True)
        return {}
