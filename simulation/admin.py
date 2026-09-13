from django.contrib import admin
from .models import SensorReading


@admin.register(SensorReading)
class SensorReadingAdmin(admin.ModelAdmin):
    list_display = ('asset', 'temperature', 'vibration', 'is_anomaly', 'timestamp')
    list_filter = ('is_anomaly', 'asset')
    readonly_fields = [f.name for f in SensorReading._meta.fields]

    def has_add_permission(self, request):
        return False
