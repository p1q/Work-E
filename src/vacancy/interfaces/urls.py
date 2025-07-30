from django.urls import path
from vacancy.interfaces.views import VacancyListCreateView

from src.vacancy.interfaces.views import VacancyRetrieveDestroyView

urlpatterns = [
    path('', VacancyListCreateView.as_view(), name='vacancy-list-create'),
    path('<int:pk>/', VacancyRetrieveDestroyView.as_view(), name='vacancy-detail'),
]
