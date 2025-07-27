from rest_framework import generics, filters
from rest_framework.permissions import AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from matching.models import Match
from matching.interfaces.serializers import MatchSerializer


class MatchListView(generics.ListAPIView):
    queryset = Match.objects.all().select_related('user', 'vacancy')
    serializer_class = MatchSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        'user__id': ['exact'],
        'vacancy__id': ['exact'],
        'score': ['gte', 'lte'],
        'match_quality': ['exact'],
    }
    ordering_fields = ['score', 'user__email', 'vacancy__title']
    ordering = ['-score']


class MatchDetailView(generics.RetrieveAPIView):
    queryset = Match.objects.all().select_related('user', 'vacancy')
    serializer_class = MatchSerializer
    permission_classes = [AllowAny]
