from django.urls import path
from .views import (
    CVListCreateView,
    CVRetrieveDestroyView,
    CVByEmailView
)

urlpatterns = [
    path('', CVListCreateView.as_view(), name='cv-list-create'),
    path('<int:pk>/', CVRetrieveDestroyView.as_view(), name='cv-detail'),
    path('by-email/', CVByEmailView.as_view(), name='cv-by-email'),
]
