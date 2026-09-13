from rest_framework.routers import DefaultRouter
from .views import SensorReadingViewSet

router = DefaultRouter()
router.register('sensor-readings', SensorReadingViewSet)

urlpatterns = router.urls
