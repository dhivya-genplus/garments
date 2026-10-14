from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.process.views import (
    ProcessStageViewSet,
    ProcessProgramViewSet,
    JobWorkViewSet,
    JobWorkPartyConfigViewSet,
)

router = DefaultRouter()
router.register(r'stages', ProcessStageViewSet, basename='process-stages')
router.register(r'programs', ProcessProgramViewSet, basename='process-programs')
router.register(r'job-works', JobWorkViewSet, basename='job-works')
router.register(r'job-work-party-configs', JobWorkPartyConfigViewSet, basename='job-work-party-configs')

urlpatterns = [
    path('', include(router.urls)),
]
