from django.urls import path
from chatgpt.interfaces.views import ChatGPTAPIView

urlpatterns = [
    path('', ChatGPTAPIView.as_view(), name='chatgpt'),
]
