from django.urls import path
from .views import CVListCreateView, CVRetrieveDestroyView

urlpatterns = [
    path('', CVListCreateView.as_view(), name='cv-list-create'),
    path('<int:pk>/', CVRetrieveDestroyView.as_view(), name='cv-detail'),
]
