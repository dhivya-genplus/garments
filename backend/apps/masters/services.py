from typing import Dict, Any, Optional
from django.db import transaction
from core.base_services import BaseService
from core.exceptions import ValidationError, ResourceNotFound, ConflictError
from core.constants import YarnCategory, FabricCategory
from apps.authentication.models import User
from apps.masters.models import (
    UnitOfMeasurement, PartyMaster, YarnCountMaster,
    ColorShadeMaster, YarnMaster, FabricTypeMaster, FabricMaster,
    ProcessMaster, WarehouseMaster, TaxMaster
)
from apps.masters.repositories import (
    UOMRepository, PartyRepository, YarnCountRepository,
    ColorShadeRepository, YarnRepository, FabricTypeRepository, FabricRepository,
    ProcessRepository, WarehouseRepository
)

class UOMService(BaseService):
    @classmethod
    @transaction.atomic
    def create_uom(cls, company_id: int, data: Dict[str, Any], user: Optional[User] = None) -> UnitOfMeasurement:
        code = data.get("code", "").upper().strip()
        if not code:
            raise ValidationError("UOM code is required.")

        if UnitOfMeasurement.objects.filter(company_id=company_id, code=code, is_deleted=False).exists():
            raise ConflictError(f"UOM with code '{code}' already exists.")

        data["company_id"] = company_id
        data["code"] = code
        data["created_by"] = user
        return UnitOfMeasurement.objects.create(**data)


class PartyService(BaseService):
    @classmethod
    @transaction.atomic
    def create_party(cls, company_id: int, data: Dict[str, Any], user: Optional[User] = None) -> PartyMaster:
        code = data.get("code", "").upper().strip()
        if not code:
            raise ValidationError("Party code is required.")

        if PartyMaster.objects.filter(company_id=company_id, code=code, is_deleted=False).exists():
            raise ConflictError(f"Party with code '{code}' already exists.")

        data["company_id"] = company_id
        data["code"] = code
        data["created_by"] = user
        return PartyMaster.objects.create(**data)

    @classmethod
    @transaction.atomic
    def update_party(cls, party_id: int, company_id: int, data: Dict[str, Any], user: Optional[User] = None) -> PartyMaster:
        party = PartyRepository.get_by_id_and_company(party_id, company_id)
        if not party:
            raise ResourceNotFound(f"Party with ID {party_id} not found.")

        code = data.get("code")
        if code and code.upper() != party.code:
            if PartyMaster.objects.filter(company_id=company_id, code=code.upper(), is_deleted=False).exclude(id=party_id).exists():
                raise ConflictError(f"Party code '{code}' is already used.")
            data["code"] = code.upper()

        data["updated_by"] = user
        return PartyRepository.update(party, **data)


class YarnService(BaseService):
    @classmethod
    @transaction.atomic
    def create_yarn(cls, company_id: int, data: Dict[str, Any], user: Optional[User] = None) -> YarnMaster:
        yarn_code = data.get("yarn_code", "").upper().strip()
        if not yarn_code:
            raise ValidationError("Yarn code is required.")

        if YarnMaster.objects.filter(company_id=company_id, yarn_code=yarn_code, is_deleted=False).exists():
            raise ConflictError(f"Yarn with code '{yarn_code}' already exists.")

        # If Dyed Yarn, color shade is recommended/validated
        category = data.get("category", YarnCategory.GREY)
        color_shade_id = data.get("color_shade_id") or (data.get("color_shade").id if data.get("color_shade") else None)
        if category == YarnCategory.DYED and not color_shade_id:
            raise ValidationError("Color shade is required for Dyed Yarn.")

        data["company_id"] = company_id
        data["yarn_code"] = yarn_code
        data["created_by"] = user
        return YarnMaster.objects.create(**data)

    @classmethod
    @transaction.atomic
    def update_yarn(cls, yarn_id: int, company_id: int, data: Dict[str, Any], user: Optional[User] = None) -> YarnMaster:
        yarn = YarnRepository.get_by_id_and_company(yarn_id, company_id)
        if not yarn:
            raise ResourceNotFound(f"Yarn with ID {yarn_id} not found.")

        yarn_code = data.get("yarn_code")
        if yarn_code and yarn_code.upper() != yarn.yarn_code:
            if YarnMaster.objects.filter(company_id=company_id, yarn_code=yarn_code.upper(), is_deleted=False).exclude(id=yarn_id).exists():
                raise ConflictError(f"Yarn code '{yarn_code}' is already used.")
            data["yarn_code"] = yarn_code.upper()

        data["updated_by"] = user
        return YarnRepository.update(yarn, **data)


class FabricService(BaseService):
    @classmethod
    @transaction.atomic
    def create_fabric(cls, company_id: int, data: Dict[str, Any], user: Optional[User] = None) -> FabricMaster:
        fabric_code = data.get("fabric_code", "").upper().strip()
        if not fabric_code:
            raise ValidationError("Fabric code is required.")

        if FabricMaster.objects.filter(company_id=company_id, fabric_code=fabric_code, is_deleted=False).exists():
            raise ConflictError(f"Fabric with code '{fabric_code}' already exists.")

        category = data.get("category", FabricCategory.GREY)
        color_shade_id = data.get("color_shade_id") or (data.get("color_shade").id if data.get("color_shade") else None)
        if category == FabricCategory.DYED and not color_shade_id:
            raise ValidationError("Color shade is required for Dyed Fabric.")

        data["company_id"] = company_id
        data["fabric_code"] = fabric_code
        data["created_by"] = user
        return FabricMaster.objects.create(**data)

    @classmethod
    @transaction.atomic
    def update_fabric(cls, fabric_id: int, company_id: int, data: Dict[str, Any], user: Optional[User] = None) -> FabricMaster:
        fabric = FabricRepository.get_by_id_and_company(fabric_id, company_id)
        if not fabric:
            raise ResourceNotFound(f"Fabric with ID {fabric_id} not found.")

        fabric_code = data.get("fabric_code")
        if fabric_code and fabric_code.upper() != fabric.fabric_code:
            if FabricMaster.objects.filter(company_id=company_id, fabric_code=fabric_code.upper(), is_deleted=False).exclude(id=fabric_id).exists():
                raise ConflictError(f"Fabric code '{fabric_code}' is already used.")
            data["fabric_code"] = fabric_code.upper()

        data["updated_by"] = user
        return FabricRepository.update(fabric, **data)


class ProcessService(BaseService):
    @classmethod
    @transaction.atomic
    def create_process(cls, company_id: int, data: Dict[str, Any], user: Optional[User] = None) -> ProcessMaster:
        code = data.get("process_code", "").upper().strip()
        if not code:
            raise ValidationError("Process code is required.")

        if ProcessMaster.objects.filter(company_id=company_id, process_code=code, is_deleted=False).exists():
            raise ConflictError(f"Process with code '{code}' already exists.")

        data["company_id"] = company_id
        data["process_code"] = code
        data["created_by"] = user
        return ProcessMaster.objects.create(**data)


class WarehouseService(BaseService):
    @classmethod
    @transaction.atomic
    def create_warehouse(cls, company_id: int, data: Dict[str, Any], user: Optional[User] = None) -> WarehouseMaster:
        code = data.get("warehouse_code", "").upper().strip()
        if not code:
            raise ValidationError("Warehouse code is required.")

        if WarehouseMaster.objects.filter(company_id=company_id, warehouse_code=code, is_deleted=False).exists():
            raise ConflictError(f"Warehouse with code '{code}' already exists.")

        data["company_id"] = company_id
        data["warehouse_code"] = code
        data["created_by"] = user
        return WarehouseMaster.objects.create(**data)


class TaxService(BaseService):
    DEFAULT_TAX_RATES = [
        {"tax_name": "GST 0% (Exempt)", "tax_code": "GST_0", "tax_percent": "0.00", "cgst_percent": "0.00", "sgst_percent": "0.00", "igst_percent": "0.00", "hsn_sac_code": "", "is_default": False},
        {"tax_name": "GST 5% (Yarn)", "tax_code": "GST_5", "tax_percent": "5.00", "cgst_percent": "2.50", "sgst_percent": "2.50", "igst_percent": "5.00", "hsn_sac_code": "5205", "is_default": True},
        {"tax_name": "GST 12% (Fabrics)", "tax_code": "GST_12", "tax_percent": "12.00", "cgst_percent": "6.00", "sgst_percent": "6.00", "igst_percent": "12.00", "hsn_sac_code": "5208", "is_default": False},
        {"tax_name": "GST 18% (Jobwork/Services)", "tax_code": "GST_18", "tax_percent": "18.00", "cgst_percent": "9.00", "sgst_percent": "9.00", "igst_percent": "18.00", "hsn_sac_code": "9988", "is_default": False},
        {"tax_name": "GST 28% (Special)", "tax_code": "GST_28", "tax_percent": "28.00", "cgst_percent": "14.00", "sgst_percent": "14.00", "igst_percent": "28.00", "hsn_sac_code": "", "is_default": False},
    ]

    @classmethod
    @transaction.atomic
    def seed_company_taxes(cls, company_id: int, user: Optional[User] = None):
        """Seed default GST tax rates for the company."""
        from decimal import Decimal
        taxes = []
        for rate in cls.DEFAULT_TAX_RATES:
            tax, _ = TaxMaster.objects.get_or_create(
                company_id=company_id,
                tax_code=rate["tax_code"],
                defaults={
                    "tax_name": rate["tax_name"],
                    "tax_percent": Decimal(rate["tax_percent"]),
                    "cgst_percent": Decimal(rate["cgst_percent"]),
                    "sgst_percent": Decimal(rate["sgst_percent"]),
                    "igst_percent": Decimal(rate["igst_percent"]),
                    "hsn_sac_code": rate["hsn_sac_code"],
                    "is_default": rate["is_default"],
                    "created_by": user,
                    "updated_by": user,
                }
            )
            taxes.append(tax)
        return taxes

