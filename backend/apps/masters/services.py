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


import re
from decimal import Decimal
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.db.models import Sum, Max
from django.utils import timezone
from core.base_services import BaseService
from core.exceptions import ValidationError, ResourceNotFound, ConflictError
from core.constants import (
    PartyTypes, PartyCategory, AddressTypes, GstRegistrationType,
    GstTreatment, PaymentModes, VerificationStatus, PartyDocumentTypes
)
from apps.authentication.models import User
from apps.masters.models import (
    UnitOfMeasurement, PartyMaster, PartyRole, PartyContact,
    PartyAddress, PartyBankDetail, PartyCapability, PartyDocument,
    YarnCountMaster, FabricTypeMaster, ProcessMaster
)
from apps.masters.repositories import PartyRepository

GSTIN_REGEX = re.compile(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')
PAN_REGEX = re.compile(r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$')


class PartyService(BaseService):
    @classmethod
    def validate_statutory(cls, data: Dict[str, Any]) -> None:
        """Validates GSTIN and PAN according to Indian statutory rules, supporting unregistered parties."""
        gst_type = data.get("gst_registration_type", GstRegistrationType.REGULAR)
        gstin = (data.get("gst_number") or "").upper().strip()
        pan = (data.get("pan_number") or "").upper().strip()

        if gstin:
            data["gst_number"] = gstin
            if not GSTIN_REGEX.match(gstin):
                raise ValidationError("Invalid GSTIN format. Expected 15-character Indian Goods and Services Tax number (e.g. 33AABCT1234F1Z8).")
            # Automatically derive PAN from GSTIN (characters 3-12) if PAN not supplied
            extracted_pan = gstin[2:12]
            if not pan:
                pan = extracted_pan
                data["pan_number"] = pan
            elif pan != extracted_pan:
                raise ValidationError(f"Supplied PAN '{pan}' does not match characters 3-12 of GSTIN '{extracted_pan}'.")

        if gst_type in [GstRegistrationType.REGULAR, GstRegistrationType.COMPOSITION] and not gstin:
            # Note: For existing legacy parties or draft creation, allow empty if not mandatory,
            # but if type is explicitly Regular with non-empty registration requirements, flag warning or format.
            pass

        if pan:
            data["pan_number"] = pan
            if not PAN_REGEX.match(pan):
                raise ValidationError("Invalid PAN format. Expected 10-character Permanent Account Number (e.g. AABCT1234F).")

    @classmethod
    def validate_price_lists(cls, company_id: int, data: Dict[str, Any]) -> None:
        """Ensures linked price lists belong to the company, are active, and match correct type."""
        from apps.pricing.models import PriceList
        for field, expected_type in [
            ("default_purchase_price_list", "PURCHASE"),
            ("default_sales_price_list", "SALES"),
            ("default_job_work_price_list", "JOB_WORK")
        ]:
            val = data.get(field) or data.get(f"{field}_id")
            if val:
                pl_id = val.id if hasattr(val, 'id') else val
                pl = PriceList.objects.filter(id=pl_id, company_id=company_id, record_status="A").first()
                if not pl:
                    raise ValidationError(f"Invalid or inactive Price List selected for {field.replace('_', ' ')}.")

    @classmethod
    @transaction.atomic
    def create_party(cls, company_id: int, data: Dict[str, Any], user: Optional[User] = None) -> PartyMaster:
        code = data.get("code", "").upper().strip()
        if not code:
            raise ValidationError("Party code is required.")

        if PartyMaster.objects.filter(company_id=company_id, code=code, is_deleted=False).exists():
            raise ConflictError(f"Party with code '{code}' already exists.")

        cls.validate_statutory(data)
        cls.validate_price_lists(company_id, data)

        # Extract nested child records
        roles_data = data.pop("roles", [])
        contacts_data = data.pop("contacts", [])
        addresses_data = data.pop("addresses", [])
        bank_details_data = data.pop("bank_details", [])
        capability_data = data.pop("capability", None)
        documents_data = data.pop("documents", [])

        # Synchronize primary contact from nested data if available
        if contacts_data:
            primary_c = next((c for c in contacts_data if c.get("is_primary")), contacts_data[0])
            if not data.get("contact_person"):
                data["contact_person"] = primary_c.get("contact_person", "")
            if not data.get("phone"):
                data["phone"] = primary_c.get("mobile", "")
            if not data.get("email"):
                data["email"] = primary_c.get("email", "")
            if not data.get("whatsapp_number"):
                data["whatsapp_number"] = primary_c.get("whatsapp_number", "")
            if not data.get("website"):
                data["website"] = primary_c.get("website", "")

        # Synchronize primary address from nested data if available
        if addresses_data:
            primary_a = next((a for a in addresses_data if a.get("is_default") or a.get("address_type") == AddressTypes.REGISTERED), addresses_data[0])
            if not data.get("address_line1"):
                data["address_line1"] = primary_a.get("address_line1", "")
            if not data.get("address_line2"):
                data["address_line2"] = primary_a.get("address_line2", "")
            if not data.get("city"):
                data["city"] = primary_a.get("city", "")
            if not data.get("state"):
                data["state"] = primary_a.get("state", "")
            if not data.get("pincode"):
                data["pincode"] = primary_a.get("pincode", "")

        # Determine primary party_type
        if not data.get("party_type") and roles_data:
            first_role = roles_data[0]
            data["party_type"] = first_role.get("role") if isinstance(first_role, dict) else first_role
        elif not data.get("party_type"):
            data["party_type"] = PartyTypes.MILL

        data["company_id"] = company_id
        data["code"] = code
        data["created_by"] = user
        party = PartyMaster.objects.create(**data)

        # 1. Create Party Roles
        role_codes = set()
        if roles_data:
            for r in roles_data:
                role_val = r.get("role") if isinstance(r, dict) else r
                is_pri = r.get("is_primary", False) if isinstance(r, dict) else (role_val == party.party_type)
                if role_val and role_val not in role_codes:
                    role_codes.add(role_val)
                    PartyRole.objects.create(
                        company_id=company_id,
                        party=party,
                        role=role_val,
                        is_primary=is_pri,
                        created_by=user
                    )
        # Ensure party's primary role is represented in PartyRole
        if party.party_type not in role_codes:
            PartyRole.objects.create(
                company_id=company_id,
                party=party,
                role=party.party_type,
                is_primary=True,
                created_by=user
            )

        # 2. Create Contacts
        if contacts_data:
            for idx, c in enumerate(contacts_data):
                is_pri = c.get("is_primary", idx == 0)
                PartyContact.objects.create(
                    company_id=company_id,
                    party=party,
                    contact_person=c.get("contact_person", party.name),
                    designation=c.get("designation", ""),
                    mobile=c.get("mobile", party.phone or "+91 9876543210"),
                    alternate_mobile=c.get("alternate_mobile", ""),
                    email=c.get("email", party.email or ""),
                    alternate_email=c.get("alternate_email", ""),
                    whatsapp_number=c.get("whatsapp_number", ""),
                    website=c.get("website", ""),
                    is_primary=is_pri,
                    is_active=c.get("is_active", True),
                    created_by=user
                )

        # 3. Create Addresses
        if addresses_data:
            for idx, a in enumerate(addresses_data):
                is_def = a.get("is_default", idx == 0)
                PartyAddress.objects.create(
                    company_id=company_id,
                    party=party,
                    address_type=a.get("address_type", AddressTypes.REGISTERED),
                    address_line1=a.get("address_line1", party.address_line1 or "Main Road"),
                    address_line2=a.get("address_line2", party.address_line2 or ""),
                    country=a.get("country", "India"),
                    state=a.get("state", party.state or "Tamil Nadu"),
                    district=a.get("district", ""),
                    city=a.get("city", party.city or "Tirupur"),
                    area_locality=a.get("area_locality", ""),
                    pincode=a.get("pincode", party.pincode or "641601"),
                    gst_state_code=a.get("gst_state_code", (party.gst_number[:2] if party.gst_number else "")),
                    is_default=is_def,
                    is_active=a.get("is_active", True),
                    created_by=user
                )

        # 4. Create Bank Details
        if bank_details_data:
            for idx, b in enumerate(bank_details_data):
                is_def = b.get("is_default", idx == 0)
                PartyBankDetail.objects.create(
                    company_id=company_id,
                    party=party,
                    bank_name=b["bank_name"],
                    branch_name=b.get("branch_name", ""),
                    account_holder_name=b.get("account_holder_name", party.name),
                    account_number=b["account_number"],
                    ifsc_code=b.get("ifsc_code", "").upper().strip(),
                    upi_id=b.get("upi_id", ""),
                    preferred_payment_mode=b.get("preferred_payment_mode", PaymentModes.NEFT_RTGS),
                    beneficiary_verification_status=b.get("beneficiary_verification_status", VerificationStatus.UNVERIFIED),
                    is_default=is_def,
                    is_active=b.get("is_active", True),
                    created_by=user
                )

        # 5. Create Capability
        if capability_data:
            processes = capability_data.pop("processes_performed", [])
            yarn_counts = capability_data.pop("yarn_counts_handled", [])
            fabric_types = capability_data.pop("fabric_types_handled", [])

            cap = PartyCapability.objects.create(
                company_id=company_id,
                party=party,
                machine_types=capability_data.get("machine_types", ""),
                production_capacity=Decimal(str(capability_data.get("production_capacity", "0.000"))),
                capacity_uom_id=capability_data.get("capacity_uom_id"),
                min_job_work_qty=Decimal(str(capability_data.get("min_job_work_qty", "0.000"))),
                max_job_work_qty=Decimal(str(capability_data.get("max_job_work_qty", "0.000"))),
                standard_processing_days=capability_data.get("standard_processing_days", 0),
                procurement_lead_time_days=capability_data.get("procurement_lead_time_days", 0),
                default_uom_id=capability_data.get("default_uom_id"),
                quality_certifications=capability_data.get("quality_certifications", ""),
                sample_approval_required=capability_data.get("sample_approval_required", True),
                created_by=user
            )
            if processes:
                cap.processes_performed.set(processes)
            if yarn_counts:
                cap.yarn_counts_handled.set(yarn_counts)
            if fabric_types:
                cap.fabric_types_handled.set(fabric_types)

        return PartyRepository.get_by_id_and_company(party.id, company_id)

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

        cls.validate_statutory(data)
        cls.validate_price_lists(company_id, data)

        # Extract nested child records
        roles_data = data.pop("roles", None)
        contacts_data = data.pop("contacts", None)
        addresses_data = data.pop("addresses", None)
        bank_details_data = data.pop("bank_details", None)
        capability_data = data.pop("capability", None)

        # 1. Update roles if provided
        if roles_data is not None:
            PartyRole.objects.filter(party=party).delete()
            role_codes = set()
            for r in roles_data:
                role_val = r.get("role") if isinstance(r, dict) else r
                is_pri = r.get("is_primary", False) if isinstance(r, dict) else False
                if role_val and role_val not in role_codes:
                    role_codes.add(role_val)
                    PartyRole.objects.create(
                        company_id=company_id,
                        party=party,
                        role=role_val,
                        is_primary=is_pri,
                        created_by=user
                    )
            # Sync primary role to party_type
            primary_r = next((r for r in roles_data if isinstance(r, dict) and r.get("is_primary")), None)
            if primary_r:
                data["party_type"] = primary_r["role"]

        # 2. Update contacts if provided
        if contacts_data is not None:
            PartyContact.objects.filter(party=party).delete()
            for idx, c in enumerate(contacts_data):
                is_pri = c.get("is_primary", idx == 0)
                PartyContact.objects.create(
                    company_id=company_id,
                    party=party,
                    contact_person=c.get("contact_person", party.name),
                    designation=c.get("designation", ""),
                    mobile=c.get("mobile", party.phone or "+91 9876543210"),
                    alternate_mobile=c.get("alternate_mobile", ""),
                    email=c.get("email", party.email or ""),
                    alternate_email=c.get("alternate_email", ""),
                    whatsapp_number=c.get("whatsapp_number", ""),
                    website=c.get("website", ""),
                    is_primary=is_pri,
                    is_active=c.get("is_active", True),
                    created_by=user
                )
                if is_pri:
                    data["contact_person"] = c.get("contact_person", "")
                    data["phone"] = c.get("mobile", "")
                    data["email"] = c.get("email", "")

        # 3. Update addresses if provided
        if addresses_data is not None:
            PartyAddress.objects.filter(party=party).delete()
            for idx, a in enumerate(addresses_data):
                is_def = a.get("is_default", idx == 0)
                PartyAddress.objects.create(
                    company_id=company_id,
                    party=party,
                    address_type=a.get("address_type", AddressTypes.REGISTERED),
                    address_line1=a.get("address_line1", "Main Road"),
                    address_line2=a.get("address_line2", ""),
                    country=a.get("country", "India"),
                    state=a.get("state", "Tamil Nadu"),
                    district=a.get("district", ""),
                    city=a.get("city", "Tirupur"),
                    area_locality=a.get("area_locality", ""),
                    pincode=a.get("pincode", "641601"),
                    gst_state_code=a.get("gst_state_code", ""),
                    is_default=is_def,
                    is_active=a.get("is_active", True),
                    created_by=user
                )
                if is_def or a.get("address_type") == AddressTypes.REGISTERED:
                    data["address_line1"] = a.get("address_line1", "")
                    data["address_line2"] = a.get("address_line2", "")
                    data["city"] = a.get("city", "")
                    data["state"] = a.get("state", "")
                    data["pincode"] = a.get("pincode", "")

        # 4. Update bank details if provided
        if bank_details_data is not None:
            PartyBankDetail.objects.filter(party=party).delete()
            for idx, b in enumerate(bank_details_data):
                is_def = b.get("is_default", idx == 0)
                PartyBankDetail.objects.create(
                    company_id=company_id,
                    party=party,
                    bank_name=b["bank_name"],
                    branch_name=b.get("branch_name", ""),
                    account_holder_name=b.get("account_holder_name", party.name),
                    account_number=b["account_number"],
                    ifsc_code=b.get("ifsc_code", "").upper().strip(),
                    upi_id=b.get("upi_id", ""),
                    preferred_payment_mode=b.get("preferred_payment_mode", PaymentModes.NEFT_RTGS),
                    beneficiary_verification_status=b.get("beneficiary_verification_status", VerificationStatus.UNVERIFIED),
                    is_default=is_def,
                    is_active=b.get("is_active", True),
                    created_by=user
                )

        # 5. Update capability if provided
        if capability_data is not None:
            processes = capability_data.pop("processes_performed", None)
            yarn_counts = capability_data.pop("yarn_counts_handled", None)
            fabric_types = capability_data.pop("fabric_types_handled", None)

            cap, _ = PartyCapability.objects.get_or_create(
                party=party,
                defaults={"company_id": company_id, "created_by": user}
            )
            for k, v in capability_data.items():
                setattr(cap, k, v)
            cap.updated_by = user
            cap.save()

            if processes is not None:
                cap.processes_performed.set(processes)
            if yarn_counts is not None:
                cap.yarn_counts_handled.set(yarn_counts)
            if fabric_types is not None:
                cap.fabric_types_handled.set(fabric_types)

        data["updated_by"] = user
        return PartyRepository.update(party, **data)

    @classmethod
    @transaction.atomic
    def deactivate_party(cls, party_id: int, company_id: int, user: Optional[User] = None) -> PartyMaster:
        """Controlled deactivation: sets is_active=False while preserving historical transactions."""
        party = PartyRepository.get_by_id_and_company(party_id, company_id)
        if not party:
            raise ResourceNotFound(f"Party with ID {party_id} not found.")

        party.is_active = False
        party.updated_by = user
        party.save(update_fields=["is_active", "updated_by", "updated_on"])
        return party

    @classmethod
    def get_party_financial_summary(cls, party_id: int, company_id: int) -> Dict[str, Any]:
        """Calculates live outstanding balance and ledger metrics from posted currency ledger lines."""
        from apps.ledger.models import tl_voucher_line
        party = PartyRepository.get_by_id_and_company(party_id, company_id)
        if not party:
            raise ResourceNotFound(f"Party with ID {party_id} not found.")

        lines = tl_voucher_line.objects.filter(
            party_id=party_id,
            voucher__company_id=company_id,
            voucher__is_posted=True
        )

        aggregates = lines.aggregate(
            total_debit=Sum('debit'),
            total_credit=Sum('credit'),
            last_date=Max('voucher__voucher_date')
        )

        total_dr = Decimal(str(aggregates['total_debit'] or '0.00'))
        total_cr = Decimal(str(aggregates['total_credit'] or '0.00'))
        op_bal = Decimal(str(party.opening_balance or '0.00'))

        # Opening balance effect: DR is receivable (+), CR is payable (-)
        if party.opening_balance_type == 'DR':
            net_balance = (op_bal + total_dr) - total_cr
        else:
            net_balance = total_dr - (op_bal + total_cr)

        return {
            "party_id": party.id,
            "party_code": party.code,
            "party_name": party.name,
            "opening_balance": op_bal,
            "opening_balance_type": party.opening_balance_type,
            "total_debit": total_dr,
            "total_credit": total_cr,
            "net_outstanding_balance": net_balance,
            "balance_type": "RECEIVABLE" if net_balance > 0 else "PAYABLE" if net_balance < 0 else "NIL",
            "last_transaction_date": aggregates['last_date'],
            "posted_vouchers_count": lines.values('voucher_id').distinct().count(),
        }


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

