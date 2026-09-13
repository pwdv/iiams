from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, LocationViewSet, AssetViewSet

router = DefaultRouter()
router.register('categories', CategoryViewSet)
router.register('locations', LocationViewSet)
router.register('items', AssetViewSet)

urlpatterns = router.urls
