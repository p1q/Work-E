import io
import json
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
        cv = CV.objects.get(id=cv_id, user_id=user_id)
    except CV.DoesNotExist:
        logger.error(f"CV з ID {cv_id} для користувача {user_id} не знайдено.")
        raise ValidationError("CV не знайдено.")

    # Видобути текст
    if cv_text_override is not None:
        cv_text = cv_text_override
        logger.debug(f"Використано наданий текст для CV {cv.id}.")
    else:
        cv_text, _, _, _ = extract_text_from_cv(cv)
        if not cv_text:
            raise ValidationError("Не вдалося видобути текст з резюме.")

    # Виклик ШІ
    prompt = CV_ANALYSIS_PROMPT.format(cv_text=cv_text)
    ai_response_data = call_openapi_ai(messages=[{"role": "user", "content": prompt}],
                                       model=getattr(settings, 'OPENAPI_AI_MODEL', 'default-model'))

    # Витягти JSON
    content = ""
    if 'choices' in ai_response_data and ai_response_data['choices']:
        content = ai_response_data['choices'][0].get('message', {}).get('content', '')
    elif 'message' in ai_response_data:
        content = ai_response_data.get('message', {}).get('content', '')
    else:
        content = str(ai_response_data)

    # Очистити від ```json
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.endswith("```"):
        content = content[:-3]
    content = content.strip()

    if not content:
        raise Exception("Порожній content від ШІ.")

    try:
        parsed_data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"Недійсний JSON: {content[:200]}")
        raise Exception(f"Недійсний JSON: {str(e)}")

    # 1. WorkOptions
    if cv.work_options is None:
        cv.work_options = WorkOptions.objects.create()
    wo = cv.work_options
    wo.countries = parsed_data.get("countries") or []
    wo.cities = parsed_data.get("cities") or []
    wo.is_office = parsed_data.get("is_office")
    wo.is_remote = parsed_data.get("is_remote")
    wo.is_hybrid = parsed_data.get("is_hybrid")
    wo.willing_to_relocate = parsed_data.get("willing_to_relocate")
    wo.save()

    # 2. Skills
    Skill.objects.filter(cv=cv).delete()
    for i, name in enumerate(parsed_data.get("skills", [])):
        if isinstance(name, str) and name.strip():
            Skill.objects.create(cv=cv, name=name.strip(), order_index=i)

    # 3. Languages
    Language.objects.filter(cv=cv).delete()
    for i, lang_data in enumerate(parsed_data.get("languages", [])):
        if isinstance(lang_data, dict):
            lang_name = lang_data.get("language")
            lang_level = lang_data.get("level")
            if lang_name and isinstance(lang_name, str):
                Language.objects.create(
                    cv=cv,
                    name=lang_name.strip(),
                    level=lang_level if lang_level in [c[0] for c in Language.LEVEL_CHOICES] else None,
                    order_index=i
                )

    # 4. Поля в CV
    cv.level = parsed_data.get("level")
    cv.categories = parsed_data.get("categories") or []
    cv.salary_min = parsed_data.get("salary_min")
    cv.salary_max = parsed_data.get("salary_max")
    cv.salary_currency = parsed_data.get("salary_currency")
    cv.analyzed = True
    cv.save(update_fields=[
        'level', 'categories', 'salary_min', 'salary_max', 'salary_currency', 'analyzed'
    ])

    # Повернути дані для відповіді
    return {
        "level": cv.level,
        "categories": cv.categories,
        "countries": wo.countries,
        "cities": wo.cities,
        "is_office": wo.is_office,
        "is_remote": wo.is_remote,
        "is_hybrid": wo.is_hybrid,
        "willing_to_relocate": wo.willing_to_relocate,
        "skills": [s.name for s in Skill.objects.filter(cv=cv).order_by('order_index')],
        "languages": [
            {"language": l.name, "level": l.level}
            for l in Language.objects.filter(cv=cv).order_by('order_index')
        ],
        "salary_min": cv.salary_min,
        "salary_max": cv.salary_max,
        "salary_currency": cv.salary_currency,
    }
