from django.urls import path
from matching.interfaces.views import MatchListView, MatchDetailView

urlpatterns = [
    path('matches/', MatchListView.as_view(), name='match-list'),
    path('matches/<int:pk>/', MatchDetailView.as_view(), name='match-detail'),
]
