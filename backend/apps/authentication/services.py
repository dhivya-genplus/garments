from typing import List, Dict, Any, Optional
from datetime import date
from django.db import transaction
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from core.base_services import BaseService
from core.exceptions import ValidationError, ResourceNotFound, PermissionDeniedError, ConflictError, AuthenticationError
from core.constants import UserRoles, ModulePermissions
from apps.authentication.models import Company, FinancialYear, User, Role, Privilege
from apps.authentication.repositories import (
    CompanyRepository, FinancialYearRepository, UserRepository,
    RoleRepository, PrivilegeRepository
)

class FinancialYearService(BaseService):
    @classmethod
    @transaction.atomic
    def create_financial_year(cls, company_id: int, data: Dict[str, Any], user: Optional[User] = None) -> FinancialYear:
        code = data.get("code", "").strip()
        if not code:
            raise ValidationError("Financial Year code is required (e.g. '2025-2026').")

        if FinancialYearRepository.get_by_code(company_id, code):
            raise ConflictError(f"Financial Year with code '{code}' already exists for this company.")

        is_current = data.get("is_current", False)
        if is_current:
            # Unset any existing current financial year for this company
            FinancialYear.objects.filter(company_id=company_id, is_current=True).update(is_current=False)

        data.pop("company", None)
        data["company_id"] = company_id
        data["code"] = code
        data["created_by"] = user
        fy = FinancialYear.objects.create(**data)
        return fy

    @classmethod
    @transaction.atomic
    def set_current_financial_year(cls, company_id: int, fy_id: int, user: Optional[User] = None) -> FinancialYear:
        fy = FinancialYearRepository.get_by_id_and_company(fy_id, company_id)
        if not fy:
            raise ResourceNotFound(f"Financial Year with ID {fy_id} not found.")

        FinancialYear.objects.filter(company_id=company_id, is_current=True).update(is_current=False)
        fy.is_current = True
        fy.updated_by = user
        fy.save(update_fields=["is_current", "updated_by", "updated_on"])
        return fy


class CompanyService(BaseService):
    @classmethod
    @transaction.atomic
    def create_company(cls, data: Dict[str, Any], creator: Optional[User] = None) -> Company:
        code = data.get("code", "").upper().strip()
        if not code:
            raise ValidationError("Company code is required.", details={"code": "Required field."})
        
        if CompanyRepository.get_by_code(code):
            raise ConflictError(f"Company with code '{code}' already exists.")

        data["code"] = code
        data["created_by"] = creator
        company = CompanyRepository.create(**data)

        # 1. Initialize Default Financial Year for the company
        current_year = date.today().year
        # Financial year in India usually runs April 1 to March 31
        start_date = date(current_year, 4, 1)
        end_date = date(current_year + 1, 3, 31)
        fy_code = f"{current_year}-{current_year + 1}"
        FinancialYear.objects.create(
            company=company,
            name=f"FY {fy_code}",
            code=fy_code,
            start_date=start_date,
            end_date=end_date,
            is_current=True,
            created_by=creator
        )

        # 2. Initialize default roles & privileges for this company
        cls._create_default_roles(company, creator)
        return company

    @classmethod
    @transaction.atomic
    def update_company(cls, company_id: int, data: Dict[str, Any], user: User) -> Company:
        company = CompanyRepository.get_by_id(company_id)
        if not company:
            raise ResourceNotFound(f"Company with ID {company_id} not found.")

        code = data.get("code")
        if code and code.upper() != company.code:
            existing = CompanyRepository.get_by_code(code.upper())
            if existing and existing.id != company.id:
                raise ConflictError(f"Company code '{code}' is already used.")
            data["code"] = code.upper()

        data["updated_by"] = user
        return CompanyRepository.update(company, **data)

    @classmethod
    def _create_default_roles(cls, company: Company, creator: Optional[User] = None):
        """Creates default role templates for newly registered company."""
        # 1. Company Admin Role
        admin_role = Role.objects.create(
            company=company,
            name="Company Administrator",
            code="ADMIN",
            description="Full access to all company modules and configuration.",
            is_system_role=True,
            created_by=creator
        )
        for mod, _ in ModulePermissions.ALL_MODULES:
            Privilege.objects.create(
                role=admin_role,
                module=mod,
                can_create=True,
                can_read=True,
                can_update=True,
                can_delete=True,
                can_approve=True,
                can_export=True,
                created_by=creator
            )

        # 2. Employee / Operator Role
        operator_role = Role.objects.create(
            company=company,
            name="Garment Production Operator",
            code="OPERATOR",
            description="Operational access to enter master data and daily processes.",
            is_system_role=False,
            created_by=creator
        )
        for mod, _ in ModulePermissions.ALL_MODULES:
            if mod.startswith("masters_"):
                Privilege.objects.create(
                    role=operator_role,
                    module=mod,
                    can_create=True,
                    can_read=True,
                    can_update=True,
                    can_delete=False,
                    can_approve=False,
                    can_export=True,
                    created_by=creator
                )

        # 3. Viewer Role
        viewer_role = Role.objects.create(
            company=company,
            name="Viewer / Auditor",
            code="VIEWER",
            description="Read-only view access across all masters and reports.",
            is_system_role=False,
            created_by=creator
        )
        for mod, _ in ModulePermissions.ALL_MODULES:
            Privilege.objects.create(
                role=viewer_role,
                module=mod,
                can_create=False,
                can_read=True,
                can_update=False,
                can_delete=False,
                can_approve=False,
                can_export=True,
                created_by=creator
            )


class UserService(BaseService):
    @classmethod
    @transaction.atomic
    def create_user(cls, data: Dict[str, Any], creator: Optional[User] = None) -> User:
        email = data.get("email", "").lower().strip()
        username = data.get("username", email).strip()
        password = data.pop("password", None)

        if not email:
            raise ValidationError("Email is required.")
        if not password:
            raise ValidationError("Password is required.")

        if UserRepository.get_by_email(email):
            raise ConflictError(f"User with email '{email}' already exists.")
        if UserRepository.get_by_username(username):
            raise ConflictError(f"Username '{username}' is already taken.")

        role = data.get("role", UserRoles.COMPANY_USER)
        company = data.get("company")
        is_superadmin = data.get("is_superadmin", False)
        is_company_admin = data.get("is_company_admin", False)

        # Normalize role split
        if role == UserRoles.SUPER_ADMIN or is_superadmin:
            is_superadmin = True
            is_company_admin = False
            role = UserRoles.SUPER_ADMIN
            company = None
        elif role == UserRoles.ADMIN_USER or is_company_admin:
            is_company_admin = True
            is_superadmin = False
            role = UserRoles.ADMIN_USER
            if not company:
                raise ValidationError("Company is required for Company Admin User.")
        else:
            role = UserRoles.COMPANY_USER
            is_superadmin = False
            is_company_admin = False
            if not company:
                raise ValidationError("Company is required for Company User (Employee).")

        data["email"] = email
        data["username"] = username
        data["role"] = role
        data["company"] = company
        data["is_superadmin"] = is_superadmin
        data["is_company_admin"] = is_company_admin

        if is_superadmin:
            data["is_staff"] = True
            data["is_superuser"] = True

        custom_role_id = data.pop("custom_role_id", None)
        if custom_role_id:
            data["custom_role"] = RoleRepository.get_by_id(custom_role_id)
        elif role == UserRoles.ADMIN_USER and company:
            data["custom_role"] = Role.objects.filter(company=company, code="ADMIN").first()

        # Set default active financial year if not supplied
        active_fy_id = data.pop("active_financial_year_id", None)
        if active_fy_id:
            data["active_financial_year"] = FinancialYearRepository.get_by_id(active_fy_id)
        elif company:
            data["active_financial_year"] = company.current_financial_year

        user = User(**data)
        user.set_password(password)
        user.save()
        return user

    @classmethod
    @transaction.atomic
    def update_user(cls, user_id: int, data: Dict[str, Any], modifier: User) -> User:
        target_user = UserRepository.get_by_id(user_id)
        if not target_user:
            raise ResourceNotFound(f"User with ID {user_id} not found.")

        # Permission check: Super Admin can modify anyone. Admin User can modify users in their company.
        if not modifier.is_super_admin:
            if modifier.is_admin_user:
                if target_user.company_id != modifier.company_id:
                    raise PermissionDeniedError("Cannot modify users outside your company.")
                if target_user.is_superadmin:
                    raise PermissionDeniedError("Company admin cannot modify super admin users.")
            elif modifier.id != target_user.id:
                raise PermissionDeniedError("You can only modify your own profile.")

        password = data.pop("password", None)
        if password:
            target_user.set_password(password)

        custom_role_id = data.pop("custom_role_id", None)
        if custom_role_id is not None:
            if custom_role_id == "":
                target_user.custom_role = None
            else:
                target_user.custom_role = RoleRepository.get_by_id(custom_role_id)

        active_fy_id = data.pop("active_financial_year_id", None)
        if active_fy_id is not None:
            if active_fy_id == "":
                target_user.active_financial_year = None
            else:
                target_user.active_financial_year = FinancialYearRepository.get_by_id(active_fy_id)

        for field, val in data.items():
            setattr(target_user, field, val)

        target_user.save()
        return target_user


class RolePrivilegeService(BaseService):
    @classmethod
    @transaction.atomic
    def create_role(cls, company_id: Optional[int], name: str, code: str, description: str = "", privileges: List[Dict[str, Any]] = None, creator: Optional[User] = None) -> Role:
        existing = RoleRepository.get_by_code_and_company(code, company_id)
        if existing:
            raise ConflictError(f"Role code '{code}' already exists for this company.")

        role = Role.objects.create(
            company_id=company_id,
            name=name,
            code=code.upper(),
            description=description,
            created_by=creator
        )

        if privileges:
            cls.sync_privileges(role, privileges, creator)

        return role

    @classmethod
    @transaction.atomic
    def update_role(cls, role_id: int, data: Dict[str, Any], privileges: Optional[List[Dict[str, Any]]] = None, user: Optional[User] = None) -> Role:
        role = RoleRepository.get_by_id(role_id)
        if not role:
            raise ResourceNotFound(f"Role with ID {role_id} not found.")

        if role.is_system_role and "code" in data and data["code"] != role.code:
            raise ValidationError("System role codes cannot be modified.")

        for k, v in data.items():
            setattr(role, k, v)
        role.updated_by = user
        role.save()

        if privileges is not None:
            cls.sync_privileges(role, privileges, user)

        return role

    @classmethod
    @transaction.atomic
    def sync_privileges(cls, role: Role, privileges_data: List[Dict[str, Any]], user: Optional[User] = None):
        Privilege.objects.filter(role=role).delete()
        new_privileges = []
        for p in privileges_data:
            module = p.get("module")
            if not module:
                continue
            new_privileges.append(Privilege(
                role=role,
                module=module,
                can_create=p.get("can_create", False),
                can_read=p.get("can_read", True),
                can_update=p.get("can_update", False),
                can_delete=p.get("can_delete", False),
                can_approve=p.get("can_approve", False),
                can_export=p.get("can_export", False),
                created_by=user
            ))
        if new_privileges:
            Privilege.objects.bulk_create(new_privileges)


class AuthService(BaseService):
    @classmethod
    def login(cls, email: str, password: str) -> Dict[str, Any]:
        if not email or not password:
            raise ValidationError("Email and password are required.")

        user = authenticate(username=email, password=password)
        if not user:
            user_obj = User.objects.filter(username__iexact=email).first()
            if user_obj:
                user = authenticate(username=user_obj.email, password=password)

        if not user:
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active or user.is_deleted:
            raise AuthenticationError("This account is inactive or has been disabled.")

        if user.company and not user.company.is_active:
            raise AuthenticationError("Your company account is inactive. Please contact support.")

        refresh = RefreshToken.for_user(user)
        refresh["email"] = user.email
        refresh["role"] = user.role
        refresh["is_superadmin"] = user.is_super_admin
        refresh["is_admin_user"] = user.is_admin_user
        refresh["company_id"] = user.company_id if user.company else None
        refresh["company_name"] = user.company.name if user.company else None
        refresh["active_financial_year_id"] = user.active_financial_year_id if user.active_financial_year else None

        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "employee_code": user.employee_code,
                "department": user.department,
                "designation": user.designation,
                "phone": user.phone,
                "role": user.role,
                "role_display": user.get_role_display(),
                "is_superadmin": user.is_super_admin,
                "is_admin_user": user.is_admin_user,
                "is_company_user": user.is_company_user,
                "company": {
                    "id": user.company.id,
                    "name": user.company.name,
                    "code": user.company.code,
                } if user.company else None,
                "active_financial_year": {
                    "id": user.active_financial_year.id,
                    "name": user.active_financial_year.name,
                    "code": user.active_financial_year.code,
                    "start_date": str(user.active_financial_year.start_date),
                    "end_date": str(user.active_financial_year.end_date),
                } if user.active_financial_year else None,
                "custom_role": {
                    "id": user.custom_role.id,
                    "name": user.custom_role.name,
                    "code": user.custom_role.code,
                } if user.custom_role else None
            }
        }
