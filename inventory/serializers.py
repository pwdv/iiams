from rest_framework import serializers
from .models import Inventory


class InventorySerializer(serializers.ModelSerializer):
    needs_reorder = serializers.BooleanField(read_only=True)

    class Meta:
        model = Inventory
        fields = '__all__'
