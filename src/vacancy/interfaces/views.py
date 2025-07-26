from rest_framework import generics

from ..models import Vacancy
from .serializers import VacancySerializer


class VacancyListCreateView(generics.ListCreateAPIView):
    queryset = Vacancy.objects.all()
    serializer_class = VacancySerializer

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class VacancyRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    queryset = Vacancy.objects.all()
    serializer_class = VacancySerializer

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
