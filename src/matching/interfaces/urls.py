from django.urls import path
from matching.interfaces.views import MatchesForUserView

urlpatterns = [
    path('<int:user_id>/', MatchesForUserView.as_view(), name='matches-for-user'),
]
