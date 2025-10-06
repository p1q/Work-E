import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class CVFileStorage(FileSystemStorage):
    def __init__(self, location=None, base_url=None, *args, **kwargs):
        location = settings.CV_FILES_PATH or location
        if location:
            os.makedirs(location, exist_ok=True)
            super().__init__(location=location, base_url=base_url, *args, **kwargs)
        else:
            raise ValueError("CV_FILES_PATH не встановлено в налаштуваннях або змінних середовища.")
