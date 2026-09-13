from django.contrib.auth.models import AbstractUser
from django.db import models


class Department(models.Model):
    dept_name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True)
    manager = models.ForeignKey(
        'users.User', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='managed_departments'
    )

    def __str__(self):
        return self.dept_name


class User(AbstractUser):
    """Represents user and role management with role-based access control."""

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', 'System Admin'
        MANAGER = 'MANAGER', 'Manager'
        WAREHOUSE = 'WAREHOUSE', 'Warehouse Staff'
        PROCUREMENT = 'PROCUREMENT', 'Procurement'
        TECHNICIAN = 'TECHNICIAN', 'Technician'
        AUDITOR = 'AUDITOR', 'Auditor'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.WAREHOUSE)
    department = models.ForeignKey(
        Department, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='employees'
    )

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"


class AuditLog(models.Model):
    """Audit records for sensitive operations."""

    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    ]

    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    table_affected = models.CharField(max_length=50)
    record_id = models.CharField(max_length=50, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"[{self.timestamp:%Y-%m-%d %H:%M}] {self.user} - {self.action} on {self.table_affected}"
