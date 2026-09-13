from rest_framework import viewsets
from .models import Category, Location, Asset
from .serializers import CategorySerializer, LocationSerializer, AssetSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer


class AssetViewSet(viewsets.ModelViewSet):
    """UC-1: Register New Asset / UC-2: Track Asset Location"""
    queryset = Asset.objects.all()
    serializer_class = AssetSerializer
