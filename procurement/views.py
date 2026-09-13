from rest_framework import viewsets
from .models import Supplier, PurchaseOrder
from .serializers import SupplierSerializer, PurchaseOrderSerializer


class SupplierViewSet(viewsets.ModelViewSet):
    queryset = Supplier.objects.all()
    serializer_class = SupplierSerializer


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """UC-6: Generate Automatic Purchase Order"""
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
