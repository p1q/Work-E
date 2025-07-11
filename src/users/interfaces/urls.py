from django.urls import path
from users.interfaces.views import (
    UserListCreateView,
    UserRetrieveUpdateDestroyView,
    RegisterView,
    LoginView,
)
from users.interfaces.views_google import GoogleLoginView
from users.interfaces.views_linkedin import (
    LinkedInLoginView,
    LinkedInCallbackView,
)
from users.interfaces.views_auth import LogoutView

urlpatterns = [
    path('', UserListCreateView.as_view(), name='user-list-create'),
    path('<int:pk>/', UserRetrieveUpdateDestroyView.as_view(), name='user-detail'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),

    path('google/login/', GoogleLoginView.as_view(), name='google-login'),

    path('linkedin/login/', LinkedInLoginView.as_view(), name='linkedin-login'),
    path('linkedin/callback/', LinkedInCallbackView.as_view(), name='linkedin-callback'),

    path('logout/', LogoutView.as_view(), name='logout'),
]
