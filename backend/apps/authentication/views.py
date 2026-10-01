from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from core.permissions import IsSuperAdmin, IsAdminUser, IsCompanyUser
from core.constants import ModulePermissions, UserRoles
from apps.authentication.models import Company, FinancialYear, User, Role
from apps.authentication.serializers import (
    CompanySerializer, FinancialYearSerializer, UserSerializer,
    UserCreateSerializer, UserUpdateSerializer, RoleSerializer,
    LoginSerializer, ChangePasswordSerializer, SwitchFinancialYearSerializer
)
from apps.authentication.services import (
    CompanyService, FinancialYearService, UserService,
    RolePrivilegeService, AuthService
)
from apps.authentication.repositories import (
    CompanyRepository, FinancialYearRepository, UserRepository, RoleRepository
)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = AuthService.login(
            email=serializer.validated_data["email"],
            password=serializer.validated_data["password"]
        )
        return Response(result, status=status.HTTP_200_OK)


class CurrentUserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        serializer = UserUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = UserService.update_user(request.user.id, serializer.validated_data, request.user)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)


class SwitchFinancialYearView(APIView):
    """Allows user to switch their active working financial year."""
    permission_classes = [IsCompanyUser]

    def post(self, request):
        serializer = SwitchFinancialYearSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        fy_id = serializer.validated_data["financial_year_id"]

        company_id = request.user.company_id if request.user.company else None
        if not request.user.is_super_admin and company_id:
            fy = FinancialYearRepository.get_by_id_and_company(fy_id, company_id)
        else:
            fy = FinancialYearRepository.get_by_id(fy_id)

        if not fy:
            return Response({"detail": "Invalid financial year selected."}, status=status.HTTP_400_BAD_REQUEST)

        request.user.active_financial_year = fy
        request.user.save(update_fields=["active_financial_year"])

        return Response({
            "message": f"Active financial year switched to {fy.name}",
            "active_financial_year": FinancialYearSerializer(fy).data
        }, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data["old_password"]):
            return Response(
                {"detail": "Incorrect old password."},
                status=status.HTTP_400_BAD_REQUEST
            )

        request.user.set_password(serializer.validated_data["new_password"])
        request.user.save()
        return Response({"message": "Password changed successfully."}, status=status.HTTP_200_OK)


class AvailableModulesView(APIView):
    """Returns all system modules for setting up role privileges."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        modules = [
            {"code": code, "name": name}
            for code, name in ModulePermissions.ALL_MODULES
        ]
        return Response({"modules": modules}, status=status.HTTP_200_OK)


class CompanyViewSet(ModelViewSet):
    """
    Company Management Endpoint:
    - Super Admin: Full CRUD on all companies
    - Admin User: Read & Update their own company
    """
    serializer_class = CompanySerializer

    def get_permissions(self):
        if self.action in ['create', 'destroy']:
            return [IsSuperAdmin()]
        return [IsAdminUser()]

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            return CompanyRepository.list_all()
        return CompanyRepository.get_queryset().filter(id=user.company_id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company = CompanyService.create_company(serializer.validated_data, request.user)
        return Response(CompanySerializer(company).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)
        company = CompanyService.update_company(instance.id, serializer.validated_data, request.user)
        return Response(CompanySerializer(company).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        CompanyRepository.soft_delete(instance, user=request.user)
        return Response({"message": f"Company '{instance.name}' deleted successfully."}, status=status.HTTP_200_OK)


class FinancialYearViewSet(ModelViewSet):
    """
    Financial Year Management Endpoint:
    - Super Admin: Full oversight across all companies
    - Admin User: Manage FY for their company
    """
    permission_classes = [IsAdminUser]
    serializer_class = FinancialYearSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            company_id = self.request.query_params.get('company_id')
            if company_id:
                return FinancialYearRepository.get_for_company(company_id)
            return FinancialYearRepository.list_all_for_superadmin()
        return FinancialYearRepository.get_for_company(user.company_id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user = request.user
        company_id = data.get("company").id if (user.is_super_admin and data.get("company")) else user.company_id
        if not company_id:
            return Response({"detail": "Company is required."}, status=status.HTTP_400_BAD_REQUEST)

        fy = FinancialYearService.create_financial_year(company_id, data, user)
        return Response(FinancialYearSerializer(fy).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='set-current')
    def set_current(self, request, pk=None):
        instance = self.get_object()
        fy = FinancialYearService.set_current_financial_year(instance.company_id, instance.id, request.user)
        return Response(FinancialYearSerializer(fy).data, status=status.HTTP_200_OK)


class AdminUserViewSet(ModelViewSet):
    """
    Admin User (Company Admins) Management:
    - Super Admin: Can create/assign/manage Admin Users across all companies
    """
    permission_classes = [IsSuperAdmin]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        company_id = self.request.query_params.get('company_id')
        return UserRepository.list_admin_users(company_id=company_id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        data["role"] = UserRoles.ADMIN_USER
        data["is_company_admin"] = True
        user = UserService.create_user(data, request.user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)
        user = UserService.update_user(instance.id, serializer.validated_data, request.user)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete(user=request.user)
        return Response({"message": f"Admin user '{instance.email}' deactivated."}, status=status.HTTP_200_OK)


class EmployeeUserViewSet(ModelViewSet):
    """
    Company User / Employee Management:
    - Super Admin: Full global view and management across all companies
    - Admin User: Manage employees within their own company
    """
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            company_id = self.request.query_params.get('company_id')
            return UserRepository.list_company_users(company_id=company_id)
        return UserRepository.list_company_users(company_id=user.company_id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        if not request.user.is_super_admin:
            data["company"] = request.user.company

        data["role"] = UserRoles.COMPANY_USER
        data["is_company_admin"] = False
        data["is_superadmin"] = False

        user = UserService.create_user(data, request.user)
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)
        user = UserService.update_user(instance.id, serializer.validated_data, request.user)
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.soft_delete(user=request.user)
        return Response({"message": f"Employee '{instance.email}' deactivated."}, status=status.HTTP_200_OK)


class RoleViewSet(ModelViewSet):
    """
    Roles & Granular Privileges Management:
    - Super Admin: Manage global & company-specific roles and privileges
    - Admin User: Manage roles and privileges within their company
    """
    permission_classes = [IsAdminUser]
    serializer_class = RoleSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_super_admin:
            company_id = self.request.query_params.get('company_id')
            if company_id:
                return RoleRepository.list_for_company(company_id)
            return RoleRepository.list_all_for_superadmin()
        return RoleRepository.list_for_company(user.company_id)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        company = data.get("company") if request.user.is_super_admin else request.user.company
        company_id = company.id if company else None

        privileges_data = request.data.get("privileges", [])
        role = RolePrivilegeService.create_role(
            company_id=company_id,
            name=data["name"],
            code=data["code"],
            description=data.get("description", ""),
            privileges=privileges_data,
            creator=request.user
        )
        return Response(RoleSerializer(role).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)

        privileges_data = request.data.get("privileges")
        role = RolePrivilegeService.update_role(
            role_id=instance.id,
            data=serializer.validated_data,
            privileges=privileges_data,
            user=request.user
        )
        return Response(RoleSerializer(role).data, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.is_system_role:
            return Response({"detail": "System roles cannot be deleted."}, status=status.HTTP_400_BAD_REQUEST)
        RoleRepository.soft_delete(instance, user=request.user)
        return Response({"message": f"Role '{instance.name}' deleted."}, status=status.HTTP_200_OK)
