from django.urls import path
from .views import LanguageDetectView

urlpatterns = [
    path('detect/', LanguageDetectView.as_view(), name='language-detect'),
]
