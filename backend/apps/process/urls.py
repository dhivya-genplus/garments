from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.process.views import (
    ProcessStageViewSet,
    ProcessProgramViewSet,
)

router = DefaultRouter()
router.register(r'stages', ProcessStageViewSet, basename='process-stages')
router.register(r'programs', ProcessProgramViewSet, basename='process-programs')

urlpatterns = [
    path('', include(router.urls)),
]
