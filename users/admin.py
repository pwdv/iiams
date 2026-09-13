from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Department, AuditLog


@admin.register(User)
class IIAMSUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'department', 'is_active', 'is_staff')
    list_filter = ('role', 'department', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('IIAMS Info', {'fields': ('role', 'department')}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('dept_name', 'location', 'manager')
    search_fields = ('dept_name',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'action', 'table_affected', 'record_id')
    list_filter = ('action', 'table_affected')
    readonly_fields = [f.name for f in AuditLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
