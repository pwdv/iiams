from django.db import models
from assets.models import Category
from procurement.models import Supplier


class Inventory(models.Model):
    """Represents stock receiving, issuing, and cycle counting."""

    item_name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='inventory_items')
    sku = models.CharField(max_length=50, unique=True)
    supplier = models.ForeignKey(
        Supplier, null=True, blank=True, on_delete=models.SET_NULL, related_name='inventory_items'
    )
    quantity_on_hand = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=10)
    reorder_qty = models.PositiveIntegerField(default=50)

    class Meta:
        verbose_name_plural = 'inventory items'

    @property
    def needs_reorder(self):
        return self.quantity_on_hand <= self.reorder_level

    def __str__(self):
        return f"{self.item_name} ({self.sku})"
