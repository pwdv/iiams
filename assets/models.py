from django.conf import settings
from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children'
    )
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Location(models.Model):
    building = models.CharField(max_length=100)
    floor = models.CharField(max_length=20, blank=True)
    room = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.building} - {self.floor} - {self.room}".strip(' -')


class Asset(models.Model):
    """Represents asset registration and asset location tracking."""

    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        MAINTENANCE = 'MAINTENANCE', 'Under Maintenance'
        RETIRED = 'RETIRED', 'Retired'
        UNKNOWN = 'UNKNOWN', 'Location Unknown'

    name = models.CharField(max_length=150)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='assets')
    serial_number = models.CharField(max_length=100, unique=True)
    location = models.ForeignKey(
        Location, null=True, blank=True, on_delete=models.SET_NULL, related_name='assets'
    )
    assigned_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='assigned_assets'
    )
    purchase_date = models.DateField(null=True, blank=True)
    purchase_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    current_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    tag_code = models.CharField(
        help_text='Synthetic QR / RFID tag generated automatically when registered'
    )
    last_seen = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new and not self.tag_code:
            self.tag_code = f"IIAMS-AST-{self.id:06d}"
            super().save(update_fields=['tag_code'])

    def __str__(self):
        return f"{self.name} ({self.serial_number})"


class AssetEvent(models.Model):
    """Operational history for asset assignment, transfer and status changes."""

    class EventType(models.TextChoices):
        REGISTERED = 'REGISTERED', 'Registered'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        UNASSIGNED = 'UNASSIGNED', 'Unassigned'
        TRANSFERRED = 'TRANSFERRED', 'Transferred'
        STATUS_CHANGED = 'STATUS_CHANGED', 'Status Changed'
        UPDATED = 'UPDATED', 'Updated'

    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='events')
    event_type = models.CharField(max_length=30, choices=EventType.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='asset_events'
    )
    from_location = models.ForeignKey(
        Location, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='asset_events_from'
    )
    to_location = models.ForeignKey(
        Location, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='asset_events_to'
    )
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='asset_events_from_user'
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='asset_events_to_user'
    )
    from_status = models.CharField(max_length=20, blank=True)
    to_status = models.CharField(max_length=20, blank=True)
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-created_at', '-id']

    def __str__(self):
        return f'{self.asset.serial_number} - {self.get_event_type_display()}'
