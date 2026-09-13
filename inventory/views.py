from rest_framework import viewsets, decorators, response
from .models import Inventory
from .serializers import InventorySerializer


class InventoryViewSet(viewsets.ModelViewSet):
    """UC-3: Receive Stock / UC-4: Issue Stock / UC-9: Cycle Count"""
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer

    @decorators.action(detail=False, methods=['get'])
    def low_stock(self, request):
        """UC-6 helper: items at/below reorder level"""
        items = [i for i in self.get_queryset() if i.needs_reorder]
        serializer = self.get_serializer(items, many=True)
        return response.Response(serializer.data)
