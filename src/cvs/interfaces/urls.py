from django.urls import path
from .views import (CVListCreateView, CVRetrieveDestroyView, CVByEmailPostView, LastCVByEmailPostView,
                    GenerateCVView, AdaptCoverLetterView, AnalyzeCVView, ExtractTextFromCVView, GetDownloadLinkView)
from .views_download import DownloadFileView

urlpatterns = [
    path('', CVListCreateView.as_view(), name='cv-list-create'),
    path('<int:pk>/', CVRetrieveDestroyView.as_view(), name='cv-detail'),
    path('by-email/', CVByEmailPostView.as_view(), name='cv-by-email'),
    path('last-by-email/', LastCVByEmailPostView.as_view(), name='cv-last-by-email'),
    path('generate-cv/', GenerateCVView.as_view()),
    path('adapt-cover-letter/', AdaptCoverLetterView.as_view()),
    path('extract-text/', ExtractTextFromCVView.as_view(), name='cv-extract-text'),
    path('analyze/', AnalyzeCVView.as_view(), name='cv-analyze'),
    path('get-download-link/', GetDownloadLinkView.as_view(), name='get-download-link'),
    path('download-cv-file/<uuid:token>/', DownloadFileView.as_view(), name='download-cv-file'),
]
