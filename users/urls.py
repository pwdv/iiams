from rest_framework.routers import DefaultRouter
from .views import UserViewSet, DepartmentViewSet, AuditLogViewSet

router = DefaultRouter()
router.register('accounts', UserViewSet)
router.register('departments', DepartmentViewSet)
router.register('audit-log', AuditLogViewSet)

urlpatterns = router.urls
