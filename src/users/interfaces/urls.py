from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserListCreateView,
    UserRetrieveUpdateDestroyView,
    RegisterView,
    LoginView,
    CurrentUserView,
    profile,   # функціональний в’ю
)
from .views_google import GoogleLoginView
from .views_linkedin import LinkedInLoginView
from .views_auth import LogoutView

urlpatterns = [
    # users CRUD
    path('', UserListCreateView.as_view(), name='user-list-create'),
    path('<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),

    # auth
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('current/', CurrentUserView.as_view(), name='current-user'),

    # social logins
    path('google/login/', GoogleLoginView.as_view(), name='google-login'),
    path('linkedin/login/', LinkedInLoginView.as_view(), name='linkedin-login'),

    # path('profile/', profile, name='cv-profile'),
]
