from rest_framework.routers import DefaultRouter
from .views import InventoryViewSet

router = DefaultRouter()
router.register('items', InventoryViewSet)

urlpatterns = router.urls
