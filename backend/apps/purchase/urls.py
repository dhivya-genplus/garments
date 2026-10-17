from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.purchase.views import (
    YarnPOViewSet, YarnPODeliveryViewSet, YarnPOBalanceViewSet,
    CompanyYarnTypeViewSet, YarnPoReturnViewSet
)

router = DefaultRouter()
router.register(r'yarn-types', CompanyYarnTypeViewSet, basename='company-yarn-type')
router.register(r'yarn-pos', YarnPOViewSet, basename='yarn-po')
router.register(r'deliveries', YarnPODeliveryViewSet, basename='yarn-po-delivery')
router.register(r'balances', YarnPOBalanceViewSet, basename='yarn-po-balance')
router.register(r'yarn-po-returns', YarnPoReturnViewSet, basename='yarn-po-return')

urlpatterns = [
    path('', include(router.urls)),
]
