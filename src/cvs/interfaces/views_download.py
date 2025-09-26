from django.http import Http404, FileResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.core.cache import cache
import mimetypes
import os


class DownloadFileView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token):
        file_path = cache.get(f"cv_download_token:{token}")
        if not file_path or not os.path.exists(file_path):
            raise Http404("Посилання недійсне або прострочене.")

        cache.delete(f"cv_download_token:{token}")

        content_type, _ = mimetypes.guess_type(file_path)
        response = FileResponse(
            open(file_path, 'rb'),
            content_type=content_type or 'application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
