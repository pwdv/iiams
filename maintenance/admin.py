from django.contrib import admin

from .models import MaintenanceRequest, MaintenancePart


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "asset",
        "maintenance_type",
        "priority",
        "status",
        "technician",
        "scheduled_date",
        "cost",
    )

    list_filter = (
        "maintenance_type",
        "priority",
        "status",
    )

    search_fields = (
        "title",
        "description",
        "asset__asset_tag",
        "asset__serial_number",
    )


@admin.register(MaintenancePart)
class MaintenancePartAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "maintenance",
        "item",
        "quantity",
        "unit_cost",
        "total_cost",
        "created_at",
    )

    search_fields = (
        "maintenance__title",
        "item__item_name",
        "item__sku",
    )

    list_filter = (
        "created_at",
    )