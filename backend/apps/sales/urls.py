from __future__ import annotations
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.sales.views import YarnSalesViewSet, YarnSalesReturnViewSet

router = DefaultRouter()
router.register(r'yarn-sales', YarnSalesViewSet, basename='yarn-sales')
router.register(r'yarn-sales-returns', YarnSalesReturnViewSet, basename='yarn-sales-return')

urlpatterns = [
    path('', include(router.urls)),
]
