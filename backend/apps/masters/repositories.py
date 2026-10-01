from typing import Optional
from django.db.models import QuerySet
from core.base_repositories import CompanyScopedRepository
from apps.masters.models import (
    UnitOfMeasurement, PartyMaster, YarnCountMaster, YarnTypeMaster,
    ColorShadeMaster, YarnMaster, FabricTypeMaster, FabricMaster,
    ProcessMaster, WarehouseMaster
)

class UOMRepository(CompanyScopedRepository[UnitOfMeasurement]):
    model = UnitOfMeasurement


class PartyRepository(CompanyScopedRepository[PartyMaster]):
    model = PartyMaster

    @classmethod
    def list_by_party_type(cls, company_id: int, party_type: str) -> QuerySet[PartyMaster]:
        return cls.get_for_company(company_id).filter(party_type=party_type, is_active=True)


class YarnCountRepository(CompanyScopedRepository[YarnCountMaster]):
    model = YarnCountMaster


class YarnTypeRepository(CompanyScopedRepository[YarnTypeMaster]):
    model = YarnTypeMaster


class ColorShadeRepository(CompanyScopedRepository[ColorShadeMaster]):
    model = ColorShadeMaster


class YarnRepository(CompanyScopedRepository[YarnMaster]):
    model = YarnMaster

    @classmethod
    def get_for_company(cls, company_id: int) -> QuerySet[YarnMaster]:
        return cls.get_queryset().filter(company_id=company_id).select_related(
            "yarn_type", "yarn_count", "color_shade", "uom"
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
