from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.knitting.views import (
    KnittingProgramViewSet,
    GreyFabricStockViewSet,
    GreyFabricInwardViewSet,
    GreyFabricOutwardViewSet,
    GreyPOViewSet,
    GreyFabricSalesViewSet,
    GreyFabricSalesReturnViewSet,
)

router = DefaultRouter()
router.register(r'programs', KnittingProgramViewSet, basename='knitting-programs')
router.register(r'stock', GreyFabricStockViewSet, basename='grey-fabric-stock')
router.register(r'inwards', GreyFabricInwardViewSet, basename='grey-fabric-inwards')
router.register(r'outwards', GreyFabricOutwardViewSet, basename='grey-fabric-outwards')
router.register(r'grey-pos', GreyPOViewSet, basename='grey-pos')
router.register(r'sales', GreyFabricSalesViewSet, basename='grey-fabric-sales')
router.register(r'sales-returns', GreyFabricSalesReturnViewSet, basename='grey-fabric-sales-returns')

urlpatterns = [
    path('', include(router.urls)),
]
