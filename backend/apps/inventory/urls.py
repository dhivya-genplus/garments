from __future__ import annotations
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.inventory.views import YarnStockViewSet, YarnInwardViewSet, YarnOutwardViewSet

router = DefaultRouter()
router.register(r'yarn-stock', YarnStockViewSet, basename='yarn-stock')
router.register(r'yarn-inwards', YarnInwardViewSet, basename='yarn-inward')
router.register(r'yarn-outwards', YarnOutwardViewSet, basename='yarn-outward')

urlpatterns = [
    path('', include(router.urls)),
]
