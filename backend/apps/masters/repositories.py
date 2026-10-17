from typing import Optional
from django.db.models import QuerySet
from core.base_repositories import CompanyScopedRepository
from apps.masters.models import (
    UnitOfMeasurement, PartyMaster, YarnCountMaster,
    ColorShadeMaster, YarnMaster, FabricTypeMaster, FabricMaster,
    ProcessMaster, WarehouseMaster
)

class UOMRepository(CompanyScopedRepository[UnitOfMeasurement]):
    model = UnitOfMeasurement


class PartyRepository(CompanyScopedRepository[PartyMaster]):
    model = PartyMaster

    @classmethod
    def get_for_company(cls, company_id: int) -> QuerySet[PartyMaster]:
        return cls.get_queryset().filter(company_id=company_id).prefetch_related(
            "roles", "contacts", "addresses", "bank_details", "documents"
        ).select_related(
            "capability", "default_purchase_price_list", "default_sales_price_list", "default_job_work_price_list"
        )

    @classmethod
    def get_by_id_and_company(cls, party_id: int, company_id: int) -> Optional[PartyMaster]:
        return cls.get_for_company(company_id).filter(id=party_id).first()

    @classmethod
    def get_by_code(cls, company_id: int, code: str) -> Optional[PartyMaster]:
        return cls.get_queryset().filter(company_id=company_id, code=code.upper().strip()).first()

    @classmethod
    def list_by_party_type(cls, company_id: int, party_type: str) -> QuerySet[PartyMaster]:
        return cls.get_for_company(company_id).filter(party_type=party_type, is_active=True)

    @classmethod
    def list_by_role(cls, company_id: int, role: str) -> QuerySet[PartyMaster]:
        from django.db.models import Q
        return cls.get_for_company(company_id).filter(
            Q(party_type=role) | Q(roles__role=role, roles__is_deleted=False),
            is_active=True
        ).distinct()

    @classmethod
    def list_active(cls, company_id: int) -> QuerySet[PartyMaster]:
        return cls.get_for_company(company_id).filter(is_active=True)


class YarnCountRepository(CompanyScopedRepository[YarnCountMaster]):
    model = YarnCountMaster


class ColorShadeRepository(CompanyScopedRepository[ColorShadeMaster]):
    model = ColorShadeMaster


class YarnRepository(CompanyScopedRepository[YarnMaster]):
    model = YarnMaster

    @classmethod
    def get_for_company(cls, company_id: int) -> QuerySet[YarnMaster]:
        return cls.get_queryset().filter(company_id=company_id).select_related(
            "yarn_count", "color_shade", "uom"
        )

    @classmethod
    def list_by_category(cls, company_id: int, category: str) -> QuerySet[YarnMaster]:
        return cls.get_for_company(company_id).filter(category=category, is_active=True)


class FabricTypeRepository(CompanyScopedRepository[FabricTypeMaster]):
    model = FabricTypeMaster


class FabricRepository(CompanyScopedRepository[FabricMaster]):
    model = FabricMaster

    @classmethod
    def get_for_company(cls, company_id: int) -> QuerySet[FabricMaster]:
        return cls.get_queryset().filter(company_id=company_id).select_related(
            "fabric_type", "yarn", "color_shade", "uom"
        )

    @classmethod
    def list_by_category(cls, company_id: int, category: str) -> QuerySet[FabricMaster]:
        return cls.get_for_company(company_id).filter(category=category, is_active=True)


class ProcessRepository(CompanyScopedRepository[ProcessMaster]):
    model = ProcessMaster


class WarehouseRepository(CompanyScopedRepository[WarehouseMaster]):
    model = WarehouseMaster

    @classmethod
    def list_by_type(cls, company_id: int, warehouse_type: str) -> QuerySet[WarehouseMaster]:
        return cls.get_for_company(company_id).filter(warehouse_type=warehouse_type, is_active=True)
