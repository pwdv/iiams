from rest_framework import serializers

from .models import MaintenanceRequest, MaintenancePart


class MaintenancePartSerializer(serializers.ModelSerializer):
    total_cost = serializers.ReadOnlyField()

    class Meta:
        model = MaintenancePart
        fields = "__all__"


class MaintenanceRequestSerializer(serializers.ModelSerializer):
    parts_used = MaintenancePartSerializer(many=True, read_only=True)

    class Meta:
        model = MaintenanceRequest
        fields = "__all__"