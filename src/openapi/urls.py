from django.urls import path
from .interfaces import views

urlpatterns = [
    path('chat/', views.OpenAPIChatView.as_view(), name='openapi-chat'),
]
