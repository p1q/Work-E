from drf_spectacular.utils import extend_schema, OpenApiRequest
from rest_framework import generics

from src.schemas.vacancy import (VACANCY_LIST_RESPONSE, VACANCY_CREATE_REQUEST, VACANCY_DETAIL_RESPONSE,
                                 VACANCY_DELETE_RESPONSE, )
from .serializers import VacancySerializer
from vacancy.models import Vacancy


class VacancyListCreateView(generics.ListCreateAPIView):
    queryset = Vacancy.objects.all()
    serializer_class = VacancySerializer

    @extend_schema(
        responses={200: VACANCY_LIST_RESPONSE},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(**VACANCY_CREATE_REQUEST)
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class VacancyRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    queryset = Vacancy.objects.all()
    serializer_class = VacancySerializer

    @extend_schema(
        responses={200: VACANCY_DETAIL_RESPONSE},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        responses={204: VACANCY_DELETE_RESPONSE},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
