import io
import logging

import pdfplumber
from django.conf import settings
from django.core.exceptions import ValidationError

from src.openapi.prompts import CV_ANALYSIS_PROMPT
from src.openapi.service import call_openapi_ai
from .models import CV

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
        extracted_text, method_used = extract_text_from_pdf_bytes(pdf_stream)
        return extracted_text, method_used, cv.id, cv.cv_file.name

    except FileNotFoundError:
        file_path = cv.cv_file.path if cv.cv_file else "Шлях невідомий"
        logger.error(f"Файл CV для CV {cv.id} не знайдено на диску за шляхом: {file_path}")
        raise ValidationError(f'Файл резюме не знайдено на сервері за шляхом: {file_path}')
    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Неочікувана помилка під час видобування тексту для CV {cv.id}: {e}", exc_info=True)
        raise ValidationError(f'Сталася неочікувана помилка під час обробки файлу резюме: {str(e)}')


def analyze_cv_with_ai(cv_id, user_id, cv_text_override=None):
    try:
        if cv_text_override is not None:
            logger.info(f"Використовується cv_text_override для аналізу (cv_id: {cv_id}, user_id: {user_id}).")
            extracted_text = cv_text_override
        else:
            logger.info(f"Шукаємо CV з ID {cv_id} для користувача {user_id}")
            cv = CV.objects.get(id=cv_id, user_id=user_id)
            logger.info(f"Знайдено CV {cv.id} для користувача {user_id}")
            extracted_text, method_used, extracted_cv_id, filename = extract_text_from_cv(cv)

            if not extracted_text:
                logger.error(f"Не вдалося видобути текст із CV {cv.id}")
                raise ValidationError(
                    'Не вдалося видобути текст із PDF файлу. Файл може бути сканованим (без текстового шару), порожнім або пошкодженим.')

        prompt = CV_ANALYSIS_PROMPT.format(cv_text=extracted_text)
        ai_response_data = call_openapi_ai(messages=[{"role": "user", "content": prompt}],
                                           model=getattr(settings, 'OPENAPI_AI_MODEL', 'default-model'))

        content = ""
        if 'choices' in ai_response_data and ai_response_data['choices']:
            content = ai_response_data['choices'][0].get('message', {}).get('content', '')
        elif 'message' in ai_response_data:
            content = ai_response_data.get('message', {}).get('content', '')
        else:
            content = str(ai_response_data)

        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        if not content:
            logger.error(f"Content порожній після обробки відповіді ШІ: {ai_response_data}")
            raise Exception("Порожній content від ШІ.")
        return content

    except ValidationError:
        raise
    except Exception as e:
        logger.error(f"Неочікувана помилка при аналізі CV {cv_id}: {e}", exc_info=True)
        raise ValidationError(f'Сталася неочікувана помилка під час аналізу резюме: {str(e)}')


def extract_text_from_pdf_bytes(pdf_stream: io.BytesIO):
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
        logger.error(f"Помилка pdfplumber при обробці BytesIO: {e}", exc_info=True)
        raise ValidationError(
            'Не вдалося видобути текст із PDF файлу. Файл може бути порожнім або пошкодженим.')

    if not extracted_text:
        logger.warning("PDF BytesIO не містить витягненого тексту.")
        raise ValidationError(
            'Не вдалося видобути текст із PDF файлу. Файл може бути порожнім або пошкодженим.')

    logger.debug(f"Успішно видобуто текст з PDF BytesIO, методом {method_used}.")
    return extracted_text, method_used
