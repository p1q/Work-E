from drf_spectacular.utils import extend_schema
from rest_framework import generics

from ..models import Vacancy
from .serializers import VacancySerializer


@extend_schema(
    tags=['Vacancies'],
    responses={200: VacancySerializer(many=True)}
)
class VacancyListCreateView(generics.ListCreateAPIView):
    queryset = Vacancy.objects.all()
    serializer_class = VacancySerializer

    @extend_schema(
        request=VacancySerializer,
        responses={201: VacancySerializer, 400: None}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


@extend_schema(
    tags=['Vacancies'],
    responses={200: VacancySerializer}
)
class VacancyRetrieveDestroyView(generics.RetrieveDestroyAPIView):
    queryset = Vacancy.objects.all()
    serializer_class = VacancySerializer

    @extend_schema(
        responses={200: VacancySerializer, 404: None}
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        responses={204: None}
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
