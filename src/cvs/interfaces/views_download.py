import logging
import os
from django.core.cache import cache
from django.http import Http404, FileResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
import mimetypes

logger = logging.getLogger(__name__)


class DownloadFileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        logger.info(f"Отримано запит на завантаження файлу за токеном: {token}")

        cache_key = f"cv_download_token:{token}"
        logger.debug(f"Шукаємо файл у кеші за ключем: {cache_key}")

        file_path = cache.get(cache_key)
        if not file_path:
            logger.error(f"Токен '{token}' не знайдено в кеші або прострочений.")
            raise Http404("Посилання для завантаження недійсне або прострочене.")

        logger.info(f"Знайдено шлях до файлу у кеші: {file_path}")

        if not os.path.exists(file_path):
            logger.error(f"Файл за шляхом '{file_path}' не існує на диску.")
            cache.delete(cache_key)  # Видаляємо некоректний токен
            raise Http404("Файл більше не доступний на сервері.")

        logger.info(f"Файл існує. Видаляємо токен '{token}' з кешу.")
        cache.delete(cache_key)

        logger.info(f"Віддаємо файл: {file_path}")
        content_type, _ = mimetypes.guess_type(file_path)
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type or 'application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
