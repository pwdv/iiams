from django.contrib import admin
from .models import Supplier, PurchaseOrder


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'contact_person', 'email', 'performance_score')
    search_fields = ('name',)


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'status', 'order_date', 'expected_delivery', 'total_value')
    list_filter = ('status', 'supplier')
