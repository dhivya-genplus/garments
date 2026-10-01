from typing import Optional
from django.db.models import QuerySet
from core.base_repositories import BaseRepository, CompanyScopedRepository
from apps.authentication.models import Company, FinancialYear, User, Role, Privilege
from core.constants import UserRoles

class CompanyRepository(BaseRepository[Company]):
    model = Company

    @classmethod
    def get_by_code(cls, code: str) -> Optional[Company]:
        return cls.get_queryset().filter(code__iexact=code).first()

    @classmethod
    def list_active(cls) -> QuerySet[Company]:
        return cls.get_queryset().filter(is_active=True).order_by("name")


class FinancialYearRepository(CompanyScopedRepository[FinancialYear]):
    model = FinancialYear

    @classmethod
    def get_current_fy(cls, company_id: int) -> Optional[FinancialYear]:
        return cls.get_for_company(company_id).filter(is_current=True).first()

    @classmethod
    def get_by_code(cls, company_id: int, code: str) -> Optional[FinancialYear]:
        return cls.get_for_company(company_id).filter(code__iexact=code).first()

    @classmethod
    def list_all_for_superadmin(cls) -> QuerySet[FinancialYear]:
        return cls.get_queryset().select_related("company").order_by("-start_date")


class UserRepository(BaseRepository[User]):
    model = User

    @classmethod
    def get_by_email(cls, email: str) -> Optional[User]:
        return cls.get_queryset().filter(email__iexact=email).first()

    @classmethod
    def get_by_username(cls, username: str) -> Optional[User]:
        return cls.get_queryset().filter(username__iexact=username).first()

    @classmethod
    def list_by_company(cls, company_id: int) -> QuerySet[User]:
        return cls.get_queryset().filter(company_id=company_id).select_related("company", "custom_role", "active_financial_year").order_by("-date_joined")

    @classmethod
    def list_admin_users(cls, company_id: Optional[int] = None) -> QuerySet[User]:
        qs = cls.get_queryset().filter(role=UserRoles.ADMIN_USER)
        if company_id:
            qs = qs.filter(company_id=company_id)
        return qs.select_related("company", "custom_role").order_by("-date_joined")

    @classmethod
    def list_company_users(cls, company_id: Optional[int] = None) -> QuerySet[User]:
        qs = cls.get_queryset().filter(role=UserRoles.COMPANY_USER)
        if company_id:
            qs = qs.filter(company_id=company_id)
        return qs.select_related("company", "custom_role", "active_financial_year").order_by("-date_joined")

    @classmethod
    def list_superadmins(cls) -> QuerySet[User]:
        return cls.get_queryset().filter(role=UserRoles.SUPER_ADMIN).order_by("-date_joined")

    @classmethod
    def list_all_for_superadmin(cls) -> QuerySet[User]:
        return cls.get_queryset().select_related("company", "custom_role", "active_financial_year").order_by("-date_joined")


class RoleRepository(BaseRepository[Role]):
    model = Role

    @classmethod
    def list_for_company(cls, company_id: Optional[int]) -> QuerySet[Role]:
        return cls.get_queryset().filter(company_id=company_id).prefetch_related("privileges").order_by("name")

    @classmethod
    def get_by_code_and_company(cls, code: str, company_id: Optional[int]) -> Optional[Role]:
        return cls.get_queryset().filter(code__iexact=code, company_id=company_id).first()

    @classmethod
    def list_all_for_superadmin(cls) -> QuerySet[Role]:
        return cls.get_queryset().select_related("company").prefetch_related("privileges").order_by("name")


class PrivilegeRepository(BaseRepository[Privilege]):
    model = Privilege

    @classmethod
    def list_by_role(cls, role_id: int) -> QuerySet[Privilege]:
        return cls.get_queryset().filter(role_id=role_id)
