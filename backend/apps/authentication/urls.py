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
    # Direct auth endpoints
    path('login/', LoginView.as_view(), name='login_direct'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh_direct'),
    path('me/', CurrentUserProfileView.as_view(), name='current_user_direct'),
    path('switch-financial-year/', SwitchFinancialYearView.as_view(), name='switch_financial_year_direct'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password_direct'),
    path('modules/', AvailableModulesView.as_view(), name='available_modules_direct'),

    # Backward-compatible prefixed auth endpoints
    path('auth/login/', LoginView.as_view(), name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/me/', CurrentUserProfileView.as_view(), name='current_user'),
    path('auth/switch-financial-year/', SwitchFinancialYearView.as_view(), name='switch_financial_year'),
    path('auth/change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('auth/modules/', AvailableModulesView.as_view(), name='available_modules'),

    # Management endpoints
    path('', include(router.urls)),
]
