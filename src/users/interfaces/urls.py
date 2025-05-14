from django.urls import path
from users.interfaces.views import (
    UserListCreateView,
    UserRetrieveUpdateDestroyView,
    RegisterView,
    LoginView
)

urlpatterns = [
    path('', UserListCreateView.as_view(), name='user-list-create'),
    path('<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
]
