from django.urls import path
from .views import VacancyListCreateView, VacancyRetrieveDestroyView

urlpatterns = [
    path('', VacancyListCreateView.as_view(), name='vacancy-list-create'),
    path('<int:pk>/', VacancyRetrieveDestroyView.as_view(), name='vacancy-detail'),
]
