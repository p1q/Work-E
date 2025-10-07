import io
import json, json5
import logging

import pdfplumber
from django.conf import settings
from django.core.exceptions import ValidationError

from src.openapi.prompts import CV_ANALYSIS_PROMPT
from src.openapi.service import call_openapi_ai
from .models import CV, Skill, Language, WorkOptions

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
            # is_temp_analysis = True # Більше не потрібно
        else:
            logger.info(f"Шукаємо CV з ID {cv_id} для користувача {user_id}")
            cv = CV.objects.get(id=cv_id, user_id=user_id)
            logger.info(f"Знайдено CV {cv.id} для користувача {user_id}")
            extracted_text, method_used, extracted_cv_id, filename = extract_text_from_cv(cv)

            if not extracted_text:
                logger.error(f"Не вдалося видобути текст із CV {cv.id}")
                raise ValidationError(
                    'Не вдалося видобути текст із PDF файлу. Файл може бути сканованим (без текстового шару), порожнім або пошкодженим.')
            # is_temp_analysis = False # Більше не потрібно

        prompt = CV_ANALYSIS_PROMPT.format(cv_text=extracted_text)
        ai_response_data = call_openapi_ai(messages=[{"role": "user", "content": prompt}],
                                           model=getattr(settings, 'OPENAPI_AI_MODEL', 'default-model'))

        # --- ЛОГУВАННЯ ВІДПОВІДІ ШІ ---
        logger.debug(f"Повна відповідь від ШІ: {ai_response_data}")
        # ---

        content = ""
        if 'choices' in ai_response_data and ai_response_data['choices']:
            content = ai_response_data['choices'][0].get('message', {}).get('content', '')
        elif 'message' in ai_response_data:  # <--- Виправлено: було 'ai_response_'
            content = ai_response_data.get('message', {}).get('content', '')
        else:
            content = str(ai_response_data)

        # --- ЛОГУВАННЯ ВИТЯГНУТОГО CONTENT ---
        logger.debug(f"Витягнутий content до очищення: '{content}'")
        # ---

        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        # --- ЛОГУВАННЯ CONTENT ПІСЛЯ ОЧИЩЕННЯ ---
        logger.debug(f"Витягнутий content після очищення: '{content}'")
        # ---

        if not content:
            logger.error(f"Content порожній після обробки відповіді ШІ: {ai_response_data}")
            raise Exception("Порожній content від ШІ.")

        # --- ВИКОРИСТАННЯ JSON5 ДЛЯ ВИПРАВЛЕННЯ ---
        try:
            # Спробуємо звичайний json.loads
            parsed_data = json.loads(content)
            logger.debug("JSON від ШІ розібрано стандартним json.loads.")
        except json.JSONDecodeError as e:
            logger.warning(f"Помилка стандартного JSON: {e}. Намагаємося виправити за допомогою json5...")
            try:
                # Використовуємо json5 для виправлення
                parsed_data = json5.loads(content)
                logger.info("JSON від ШІ успішно виправлено та розібрано за допомогою json5.")
            except (json.JSONDecodeError, ValueError) as fix_e:
                logger.error(f"Не вдалося виправити JSON: {fix_e}")
                logger.error(f"Оригінальний вміст: {content[:500]}...")
                raise Exception(f"Недійсний JSON: {str(fix_e)}")
        # --- КІНЕЦЬ ВИКОРИСТАННЯ JSON5 ---

        # --- ЗАБЕЗПЕЧЕННЯ ОБОВ'ЯЗКОВИХ ПОЛЕЙ У parsed_data ---
        # Якщо ШІ не повернув якісь поля, додаємо їх зі значеннями за замовчуванням
        # Це запобіжить помилкам валідації серіалайзера, якщо він вимагає їх.
        # Визначимо структуру за прикладом, який ти надіслав.
        # Якщо якісь ключові речі відсутні, можна створити їх.
        if 'personal' not in parsed_data:  # <--- Виправлено: було 'parsed_'
            parsed_data['personal'] = {}
        if 'work_options' not in parsed_data:  # <--- Виправлено: було 'parsed_'
            parsed_data['work_options'] = {}
        if 'skills' not in parsed_data:  # <--- Виправлено: було 'parsed_'
            parsed_data['skills'] = []
        if 'languages' not in parsed_data:  # <--- Виправлено: було 'parsed_'
            parsed_data['languages'] = []
        if 'work_experiences' not in parsed_data:
            parsed_data['work_experiences'] = []
        if 'educations' not in parsed_data:
            parsed_data['educations'] = []
        if 'courses' not in parsed_data:  # <--- Виправлено: було 'parsed_'
            parsed_data['courses'] = []
        if 'links' not in parsed_data:  # <--- Виправлено: було 'parsed_'
            parsed_data['links'] = {}
        if 'salary' not in parsed_data:  # <--- Виправлено: було 'parsed_'
            parsed_data['salary'] = {}

        # --- ДОДАТИ ПОЛЕ 'message', ЩОБ ВІДПОВІДАТИ SERIALIZER ---
        # Оскільки AnalyzeCVResponseSerializer вимагає 'message', додамо його
        parsed_data['message'] = "Аналіз резюме завершено успішно."
        # ---

        logger.info(f"Аналіз резюме (cv_id: {cv_id}, user_id: {user_id}) завершено успішно.")
        # Повертаємо виправлені та доповнені (включаючи 'message') дані від ШІ
        return parsed_data

    except CV.DoesNotExist:
        logger.error(f"CV з ID {cv_id} для користувача {user_id} не знайдено.")
        raise ValidationError("CV не знайдено.")
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
