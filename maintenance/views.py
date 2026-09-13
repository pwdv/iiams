from rest_framework import viewsets

from .models import MaintenanceRequest
from .serializers import MaintenanceRequestSerializer


class MaintenanceViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRequest.objects.all()
    serializer_class = MaintenanceRequestSerializer