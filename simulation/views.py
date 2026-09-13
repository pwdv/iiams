from rest_framework import viewsets
from .models import SensorReading
from .serializers import SensorReadingSerializer


class SensorReadingViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only simulation readings exposed through the API."""
    queryset = SensorReading.objects.all()
    serializer_class = SensorReadingSerializer
