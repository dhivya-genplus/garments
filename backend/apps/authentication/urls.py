from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from apps.authentication.views import (
    LoginView, CurrentUserProfileView, ChangePasswordView,
    SwitchFinancialYearView, AvailableModulesView,
    CompanyViewSet, FinancialYearViewSet, AdminUserViewSet,
    EmployeeUserViewSet, RoleViewSet
)

router = DefaultRouter()
router.register(r'companies', CompanyViewSet, basename='company')
router.register(r'financial-years', FinancialYearViewSet, basename='financial-year')
router.register(r'admin-users', AdminUserViewSet, basename='admin-user')
router.register(r'employees', EmployeeUserViewSet, basename='employee')
router.register(r'roles', RoleViewSet, basename='role')

urlpatterns = [
    # Auth endpoints
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', CurrentUserProfileView.as_view(), name='current_user'),
    path('auth/switch-financial-year/', SwitchFinancialYearView.as_view(), name='switch_financial_year'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('auth/modules/', AvailableModulesView.as_view(), name='available_modules'),

    # Management endpoints
    path('', include(router.urls)),
]
