from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.masters.views import (
    UOMViewSet, PartyMasterViewSet, YarnCountViewSet, YarnTypeViewSet,
    ColorShadeViewSet, YarnMasterViewSet, FabricTypeViewSet,
    FabricMasterViewSet, ProcessMasterViewSet, WarehouseMasterViewSet,
    QualityProgramViewSet, SubQualityProgramViewSet
)

router = DefaultRouter()
router.register(r'uom', UOMViewSet, basename='uom')
router.register(r'parties', PartyMasterViewSet, basename='party')
router.register(r'yarn-counts', YarnCountViewSet, basename='yarn-count')
router.register(r'yarn-types', YarnTypeViewSet, basename='yarn-type')
router.register(r'colors', ColorShadeViewSet, basename='color-shade')
router.register(r'yarns', YarnMasterViewSet, basename='yarn')
router.register(r'fabric-types', FabricTypeViewSet, basename='fabric-type')
router.register(r'fabrics', FabricMasterViewSet, basename='fabric')
router.register(r'processes', ProcessMasterViewSet, basename='process')
router.register(r'warehouses', WarehouseMasterViewSet, basename='warehouse')
router.register(r'quality-programs', QualityProgramViewSet, basename='quality-program')
router.register(r'quality-program-sizes', SubQualityProgramViewSet, basename='quality-program-size')

urlpatterns = [
    path('', include(router.urls)),
]
