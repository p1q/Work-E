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


def analyze_cv_with_ai(cv_id, user_id):
    try:
        try:
            cv = CV.objects.get(id=cv_id, user_id=user_id)
        except CV.DoesNotExist:
            logger.error(f"CV з ID {cv_id} для користувача {user_id} не знайдено.")
            raise ValidationError("CV не знайдено.")

        cv_text, method_used, extracted_cv_id, filename = extract_text_from_cv(cv)
        if not cv_text:
            logger.error(f"Не вдалося видобути текст з CV {cv_id} користувача {user_id}.")
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
        ai_response_data = call_openapi_ai(messages=ai_request_data['messages'], model=ai_request_data['model'])

        if not ai_response_data:
            logger.error(f"ШІ повернув порожню відповідь для CV {cv_id} користувача {user_id}.")
            raise Exception("Порожня відповідь від ШІ.")

        logger.info(f"Отримано відповідь від ШІ для CV {cv_id} користувача {user_id}.")
        return ai_response_data

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
