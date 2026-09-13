from rest_framework.routers import DefaultRouter
from .views import MaintenanceViewSet

router = DefaultRouter()
router.register('work-orders', MaintenanceViewSet)

urlpatterns = router.urls
