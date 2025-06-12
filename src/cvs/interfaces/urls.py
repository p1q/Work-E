from django.urls import path
from .views import (
    CVListCreateView,
    CVRetrieveDestroyView,
    CVByEmailPostView,
    LastCVByEmailPostView,
)

urlpatterns = [
    path('', CVListCreateView.as_view(), name='cv-list-create'),
    path('<int:pk>/', CVRetrieveDestroyView.as_view(), name='cv-detail'),
    path('by-email/', CVByEmailPostView.as_view(), name='cv-by-email'),
    path('last-by-email/', LastCVByEmailPostView.as_view(), name='cv-last-by-email'),
]
