from django.contrib import admin
from .models import Inventory


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'sku', 'category', 'supplier', 'quantity_on_hand', 'reorder_level', 'needs_reorder')
    list_filter = ('category', 'supplier')
    search_fields = ('item_name', 'sku')

    @admin.display(boolean=True, description='Needs reorder?')
    def needs_reorder(self, obj):
        return obj.needs_reorder
