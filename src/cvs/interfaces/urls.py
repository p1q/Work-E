from django.urls import path
from .views import CVListCreateView

urlpatterns = [
    path('', CVListCreateView.as_view(), name='cv-list-create'),
]
