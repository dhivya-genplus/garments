from rest_framework.routers import DefaultRouter
from django.urls import path, include
from apps.ledger.views import (
    StockMovementViewSet,
    StageStockViewSet,
    VoucherViewSet,
)

router = DefaultRouter()
router.register(r'stock-movements', StockMovementViewSet, basename='stock-movements')
router.register(r'stage-stock', StageStockViewSet, basename='stage-stock')
router.register(r'vouchers', VoucherViewSet, basename='vouchers')

urlpatterns = [
    path('', include(router.urls)),
]
