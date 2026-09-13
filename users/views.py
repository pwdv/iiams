from rest_framework import viewsets, permissions
from .models import User, Department, AuditLog
from .serializers import UserSerializer, DepartmentSerializer, AuditLogSerializer


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer


class UserViewSet(viewsets.ModelViewSet):
    """UC-8: Manage Users and Roles"""
    queryset = User.objects.all()
    serializer_class = UserSerializer


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
