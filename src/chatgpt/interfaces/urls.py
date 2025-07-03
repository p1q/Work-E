from django.urls import path
from chatgpt.interfaces.views import ChatGPTAPIView, ChatGPTPlanAPIView

urlpatterns = [
    path('', ChatGPTAPIView.as_view(), name='chatgpt'),
    path('plan/', ChatGPTPlanAPIView.as_view(), name='chatgpt-plan'),
]
