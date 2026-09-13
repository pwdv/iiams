from django.conf import settings
from django.db import models

from assets.models import Asset
from inventory.models import Inventory


class MaintenanceRequest(models.Model):

    class MaintenanceType(models.TextChoices):
        PREVENTIVE = "PREVENTIVE", "Preventive"
        CORRECTIVE = "CORRECTIVE", "Corrective"

    class Priority(models.TextChoices):
        LOW = "LOW", "Low"
        MEDIUM = "MEDIUM", "Medium"
        HIGH = "HIGH", "High"
        CRITICAL = "CRITICAL", "Critical"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Open"
        IN_PROGRESS = "IN_PROGRESS", "In Progress"
        ON_HOLD = "ON_HOLD", "On Hold"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name="maintenance_requests",
    )

    maintenance_type = models.CharField(
        max_length=20,
        choices=MaintenanceType.choices,
        default=MaintenanceType.CORRECTIVE,
    )

    priority = models.CharField(
        max_length=20,
        choices=Priority.choices,
        default=Priority.MEDIUM,
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
    )

    title = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="maintenance_assignments",
    )

    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="maintenance_requests_created",
    )

    scheduled_date = models.DateTimeField(
        null=True,
        blank=True,
    )

    started_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
    )

    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    resolution_notes = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.asset}"


class MaintenancePart(models.Model):

    maintenance = models.ForeignKey(
        MaintenanceRequest,
        on_delete=models.CASCADE,
        related_name="parts_used",
    )

    item = models.ForeignKey(
        Inventory,
        on_delete=models.PROTECT,
        related_name="maintenance_usage",
    )

    quantity = models.PositiveIntegerField()

    unit_cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
    )

    notes = models.CharField(
        max_length=255,
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.item} x {self.quantity}"

    @property
    def total_cost(self):
        return self.quantity * self.unit_cost