from django.urls import path
from vacancy.interfaces.views import VacancyListCreateView

urlpatterns = [
    path('vacancies/', VacancyListCreateView.as_view(), name='vacancy-list-create'),
]
