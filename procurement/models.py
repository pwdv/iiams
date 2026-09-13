from django.conf import settings
from django.db import models


class Supplier(models.Model):
    name = models.CharField(max_length=150)
    contact_person = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    performance_score = models.FloatField(default=0)

    def __str__(self):
        return self.name


class PurchaseOrder(models.Model):
    """Represents purchase order generation."""

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        SENT = 'SENT', 'Sent'
        PARTIALLY_DELIVERED = 'PARTIALLY_DELIVERED', 'Partially Delivered'
        DELIVERED = 'DELIVERED', 'Delivered'
        CANCELLED = 'CANCELLED', 'Cancelled'

    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name='purchase_orders')
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='purchase_orders'
    )
    order_date = models.DateField(auto_now_add=True)
    expected_delivery = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def __str__(self):
        return f"PO-{self.id} ({self.get_status_display()})"
