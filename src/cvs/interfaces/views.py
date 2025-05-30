from rest_framework import generics
from cvs.models import CV
from .serializers import CVSerializer


class CVListCreateView(generics.ListCreateAPIView):
    queryset = CV.objects.all()
    serializer_class = CVSerializer
