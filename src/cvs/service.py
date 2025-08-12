import json
import logging
import requests
import pdfplumber
import io
from django.conf import settings
from django.core.exceptions import ValidationError
from .models import CV
from src.openapi.service import call_openapi_ai
from src.openapi.prompts import CV_ANALYSIS_PROMPT

logger = logging.getLogger(__name__)


def extract_text_from_cv(cv):
    if not cv.cv_file:
        logger.warning(f"До CV {cv.id} не прикріплений файл")
        raise ValidationError("До файлу резюме не прикріплений PDF.")

    try:
        cv_file = cv.cv_file.open('rb')
        pdf_content = cv_file.read()
        cv_file.close()
        pdf_stream = io.BytesIO(pdf_content)
        extracted_text = ""
        method_used = "pdf_text"

        try:
            with pdfplumber.open(pdf_stream) as pdf:
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        cleaned_page_text = ''.join(line for line in page_text.splitlines() if line.strip())
                        text_parts.append(cleaned_page_text)
                extracted_text = "".join(text_parts).strip()
        except Exception as e:
            logger.error(f"Помилка pdfplumber для CV {cv.id}: {e}", exc_info=True)
            raise ValidationError(
                'Не вдалося видобути текст із PDF файлу. Файл може бути сканованим (без текстового шару), порожнім або пошкодженим.')

        if extracted_text:
            logger.debug(f"Успішно видобуто текст з CV {cv.id} методом {method_used}.")
            return extracted_text, method_used, cv.id, cv.cv_file.name
        else:
            logger.warning(f"Не вдалося видобути текст із CV {cv.id}")
            raise ValidationError(
                'Не вдалося видобути текст із PDF файлу. Файл може бути сканованим (без текстового шару), порожнім або пошкодженим.')

    except FileNotFoundError:
        file_path = cv.cv_file.path if cv.cv_file else "Шлях невідомий"
        logger.error(f"Файл CV для CV {cv.id} не знайдено на диску за шляхом: {file_path}")
        raise ValidationError(f'Файл резюме не знайдено на сервері за шляхом: {file_path}')
    except Exception as e:
        logger.error(f"Неочікувана помилка під час видобування тексту для CV {cv.id}: {e}", exc_info=True)
        raise ValidationError(f'Сталася неочікувана помилка під час обробки файлу резюме: {str(e)}')


def analyze_cv_with_ai(cv_id, user_id, cv_text_override=None):
    try:
        try:
            cv = CV.objects.get(id=cv_id, user_id=user_id)
        except CV.DoesNotExist:
            logger.error(f"CV з ID {cv_id} для користувача {user_id} не знайдено.")
            raise ValidationError("CV не знайдено.")

        # Визначення тексту CV
        if cv_text_override is not None:
            cv_text = cv_text_override
            method_used = "provided_by_view"
            extracted_cv_id = cv.id
            filename = cv.cv_file.name if cv.cv_file else "unknown"
            logger.debug(f"Використано текст CV, наданий з views.py, для CV {cv.id}.")
        else:
            cv_text, method_used, extracted_cv_id, filename = extract_text_from_cv(cv)

        if not cv_text:
            logger.warning(f"Не вдалося видобути текст з CV {cv_id} користувача {user_id}.")
            raise ValidationError("Не вдалося видобути текст з резюме.")

        prompt = CV_ANALYSIS_PROMPT.format(cv_text=cv_text)
        logger.debug(f"Сформовано промпт довжиною {len(prompt)} символів для CV {cv_id}.")

        ai_url = getattr(settings, 'OPENAPI_AI_URL')
        if not ai_url:
            logger.error("OPENAPI_AI_URL не налаштовано в settings.")
            raise Exception("OPENAPI_AI_URL не налаштовано.")

        ai_request_data = {
            "model": getattr(settings, 'OPENAPI_AI_MODEL', 'default-model'),
            "messages": [{"role": "user", "content": prompt}]
        }

        logger.info(f"Надсилання запиту до ШІ для аналізу CV {cv_id} користувача {user_id}...")
        logger.debug(f"Дані запиту до ШІ: {ai_request_data}")

        ai_response_data = call_openapi_ai(messages=ai_request_data['messages'], model=ai_request_data['model'])

        if not ai_response_data:
            logger.error(f"ШІ повернув порожню відповідь для CV {cv_id} користувача {user_id}.")
            raise Exception("Порожня відповідь від ШІ.")

        logger.info(f"Отримано відповідь від ШІ для CV {cv_id} користувача {user_id}.")
        logger.debug(f"Сирий відповідь від ШІ (тип: {type(ai_response_data)}): {ai_response_data}")

        # 1. Витягти content
        content = ""
        if 'choices' in ai_response_data and ai_response_data['choices']:
            content = ai_response_data['choices'][0].get('message', {}).get('content', '')
        elif 'message' in ai_response_data: # Альтернативна структура?
             content = ai_response_data.get('message', {}).get('content', '')
        else:
            logger.warning(f"Неочікувана структура відповіді ШІ для CV {cv_id}: {list(ai_response_data.keys()) if isinstance(ai_response_data, dict) else type(ai_response_data)}")
            content = str(ai_response_data) # Перетворити на рядок, якщо структура зовсім неочікувана

        # 2. Видалити обгортку ```json ... ```
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:] # Видалити ```json
        if content.endswith("```"):
            content = content[:-3] # Видалити ```

        if not content:
             logger.error(f"Відповідь ШІ для CV {cv_id} не містить content або він порожній після очищення.")
             raise Exception("Порожній або некоректний content у відповіді ШІ.")

        # 3. Перетворити JSON-рядок у Python-словник
        try:
            parsed_data = json.loads(content)
            logger.info(f"Успішно розпаршено JSON з відповіді ШІ для CV {cv_id}.")
            # 4. Повернути словник
            return parsed_data
        except json.JSONDecodeError as e:
            logger.error(f"Помилка декодування JSON з відповіді ШІ для CV {cv_id}: {e}. Неочищений content: {content[:200]}...")
            raise Exception(f"Помилка обробки відповіді ШІ: Недійсний JSON. {str(e)}")

    except ValidationError:
        raise
    except requests.exceptions.Timeout:
        logger.error(f"Таймаут при запиті до ШІ для CV {cv_id} користувача {user_id}.")
        raise Exception("Таймаут сервісу ШІ.")
    except requests.exceptions.ConnectionError:
        logger.error(f"Помилка з'єднання з сервісом ШІ для CV {cv_id} користувача {user_id}.")
        raise Exception("Помилка з'єднання з сервісом ШІ.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Помилка HTTP-запиту до ШІ для CV {cv_id} користувача {user_id}: {e}", exc_info=True)
        raise Exception(f'Помилка взаємодії з сервісом ШІ: {str(e)}')
    except Exception as e:
        logger.error(f"Неочікувана помилка при аналізі CV {cv_id} користувача {user_id} ШІ: {e}", exc_info=True)
        raise Exception(f'Сталася неочікувана помилка: {str(e)}')
