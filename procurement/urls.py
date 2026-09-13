from rest_framework.routers import DefaultRouter
from .views import SupplierViewSet, PurchaseOrderViewSet

router = DefaultRouter()
router.register('suppliers', SupplierViewSet)
router.register('purchase-orders', PurchaseOrderViewSet)

urlpatterns = router.urls
