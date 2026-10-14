from __future__ import annotations
from decimal import Decimal
from typing import Optional, Dict, Any, List
from django.db import transaction
from django.utils import timezone
from core.exceptions import ValidationError, ResourceNotFound
from core.constants import PriceListType, PriceListScope, PriceListItemType, YarnCategory
from apps.pricing.models import PriceList, PriceListItem, PriceListJobRule, PricingAudit
from apps.pricing.repositories import (
    PriceListRepository,
    PriceListItemRepository,
    PriceListJobRuleRepository,
    PricingAuditRepository
)


class PriceListService:
    @staticmethod
    @transaction.atomic
    def create_price_list(data: dict, company_id: int, user_id: Optional[int] = None) -> PriceList:
        code = data.get("price_list_code")
        if not code:
            raise ValidationError("Price list code is required.")

        # Check unique code per company for active records
        existing = PriceList.objects.filter(company_id=company_id, price_list_code=code.upper(), record_status="A").exists()
        if existing:
            raise ValidationError(f"Price list with code '{code}' already exists.")

        valid_from = data.get("valid_from")
        valid_to = data.get("valid_to")
        if valid_from and valid_to and valid_from > valid_to:
            raise ValidationError("valid_from date cannot be later than valid_to date.")

        scope = data.get("scope", PriceListScope.GENERAL)
        party_id = data.get("party_id")
        if scope == PriceListScope.PARTY_SPECIFIC and not party_id:
            raise ValidationError("party_id is required for Party-Specific price lists.")

        data["company_id"] = company_id
        data["created_by"] = user_id
        data["updated_by"] = user_id

        return PriceListRepository.create(data)

    @staticmethod
    @transaction.atomic
    def update_price_list(price_list_id: int, data: dict, company_id: int, user_id: Optional[int] = None) -> PriceList:
        price_list = PriceListRepository.get_by_id(price_list_id, company_id)
        if not price_list:
            raise ResourceNotFound(f"Price list #{price_list_id} not found.")

        valid_from = data.get("valid_from", price_list.valid_from)
        valid_to = data.get("valid_to", price_list.valid_to)
        if valid_from and valid_to and valid_from > valid_to:
            raise ValidationError("valid_from date cannot be later than valid_to date.")

        if user_id:
            data["updated_by"] = user_id

        return PriceListRepository.update(price_list, data)

    @staticmethod
    @transaction.atomic
    def delete_price_list(price_list_id: int, company_id: int, user_id: Optional[int] = None) -> None:
        price_list = PriceListRepository.get_by_id(price_list_id, company_id)
        if not price_list:
            raise ResourceNotFound(f"Price list #{price_list_id} not found.")

        price_list.soft_delete(user_id)
        # Soft delete child item lines and job rules
        PriceListItem.objects.filter(price_list_id=price_list_id, company_id=company_id).update(
            record_status="D",
            updated_by=user_id,
            updated_at=timezone.now()
        )
        PriceListJobRule.objects.filter(price_list_id=price_list_id, company_id=company_id).update(
            record_status="D",
            updated_by=user_id,
            updated_at=timezone.now()
        )

    @staticmethod
    @transaction.atomic
    def add_item(price_list_id: int, data: dict, company_id: int, user_id: Optional[int] = None) -> PriceListItem:
        price_list = PriceListRepository.get_by_id(price_list_id, company_id)
        if not price_list:
            raise ResourceNotFound(f"Price list #{price_list_id} not found.")

        base_rate = Decimal(str(data.get("base_rate", "0.00")))
        if base_rate < Decimal("0.00"):
            raise ValidationError("Base rate cannot be negative.")

        min_qty = Decimal(str(data.get("min_quantity", "0.000")))
        max_qty = data.get("max_quantity")
        if max_qty is not None:
            max_qty_dec = Decimal(str(max_qty))
            if max_qty_dec < min_qty:
                raise ValidationError("max_quantity cannot be less than min_quantity.")

        data["company_id"] = company_id
        data["price_list_id"] = price_list_id
        data["created_by"] = user_id
        data["updated_by"] = user_id

        return PriceListItemRepository.create(data)

    @staticmethod
    @transaction.atomic
    def update_item(item_id: int, data: dict, company_id: int, user_id: Optional[int] = None) -> PriceListItem:
        item = PriceListItemRepository.get_by_id(item_id, company_id)
        if not item:
            raise ResourceNotFound(f"Price list item #{item_id} not found.")

        if "base_rate" in data:
            base_rate = Decimal(str(data["base_rate"]))
            if base_rate < Decimal("0.00"):
                raise ValidationError("Base rate cannot be negative.")

        if user_id:
            data["updated_by"] = user_id

        return PriceListItemRepository.update(item, data)

    @staticmethod
    @transaction.atomic
    def delete_item(item_id: int, company_id: int, user_id: Optional[int] = None) -> None:
        item = PriceListItemRepository.get_by_id(item_id, company_id)
        if not item:
            raise ResourceNotFound(f"Price list item #{item_id} not found.")

        item.soft_delete(user_id)

    @staticmethod
    @transaction.atomic
    def add_job_rule(price_list_id: int, data: dict, company_id: int, user_id: Optional[int] = None) -> PriceListJobRule:
        price_list = PriceListRepository.get_by_id(price_list_id, company_id)
        if not price_list:
            raise ResourceNotFound(f"Price list #{price_list_id} not found.")

        job_rate = Decimal(str(data.get("job_rate", "0.0000")))
        if job_rate < Decimal("0.00"):
            raise ValidationError("Job rate cannot be negative.")

        min_qty = Decimal(str(data.get("min_quantity", "0.000")))
        max_qty = data.get("max_quantity")
        if max_qty is not None:
            max_qty_dec = Decimal(str(max_qty))
            if max_qty_dec < min_qty:
                raise ValidationError("max_quantity cannot be less than min_quantity.")

        data["company_id"] = company_id
        data["price_list_id"] = price_list_id
        data["created_by"] = user_id
        data["updated_by"] = user_id

        return PriceListJobRuleRepository.create(data)

    @staticmethod
    @transaction.atomic
    def update_job_rule(rule_id: int, data: dict, company_id: int, user_id: Optional[int] = None) -> PriceListJobRule:
        rule = PriceListJobRuleRepository.get_by_id(rule_id, company_id)
        if not rule:
            raise ResourceNotFound(f"Price list job rule #{rule_id} not found.")

        if "job_rate" in data:
            job_rate = Decimal(str(data["job_rate"]))
            if job_rate < Decimal("0.00"):
                raise ValidationError("Job rate cannot be negative.")

        if user_id:
            data["updated_by"] = user_id

        return PriceListJobRuleRepository.update(rule, data)

    @staticmethod
    @transaction.atomic
    def delete_job_rule(rule_id: int, company_id: int, user_id: Optional[int] = None) -> None:
        rule = PriceListJobRuleRepository.get_by_id(rule_id, company_id)
        if not rule:
            raise ResourceNotFound(f"Price list job rule #{rule_id} not found.")

        rule.soft_delete(user_id)

    @staticmethod
    @transaction.atomic
    def seed_default_price_lists(company_id: int, user_id: Optional[int] = None) -> List[PriceList]:
        """
        Seeds standard default price lists (General Purchase, Mill Party Contract,
        General Sales, and Customer Party Contract) with realistic textile rates.
        """
        import datetime
        from apps.masters.models import YarnCountMaster, PartyMaster

        count_30s = YarnCountMaster.objects.filter(company_id=company_id, count__icontains="30s").first()
        count_34s = YarnCountMaster.objects.filter(company_id=company_id, count__icontains="34s").first()
        count_40s = YarnCountMaster.objects.filter(company_id=company_id, count__icontains="40s").first()
        count_24s = YarnCountMaster.objects.filter(company_id=company_id, count__icontains="24s").first()
        count_2_40s = YarnCountMaster.objects.filter(company_id=company_id, count__icontains="2/40s").first()
        mill = PartyMaster.objects.filter(company_id=company_id, party_type="MILL").first()
        cust = PartyMaster.objects.filter(company_id=company_id, party_type="CUSTOMER").first()

        start_date = datetime.date(2026, 4, 1)
        end_date = datetime.date(2027, 3, 31)

        created_lists = []

        # 1. General Yarn Purchase Price List
        pl_gen_pur = PriceList.objects.filter(company_id=company_id, price_list_code="PL-PUR-GEN-2026", record_status="A").first()
        if not pl_gen_pur:
            pl_gen_pur = PriceListRepository.create({
                "company_id": company_id,
                "price_list_code": "PL-PUR-GEN-2026",
                "price_list_name": "Standard Yarn Purchase Price List 2026-27",
                "list_type": PriceListType.PURCHASE,
                "scope": PriceListScope.GENERAL,
                "valid_from": start_date,
                "valid_to": end_date,
                "is_default": True,
                "description": "Standard baseline procurement rates for spinning mill yarn.",
                "created_by": user_id,
                "updated_by": user_id,
            })
            if count_30s:
                # 30s Combed Slabs
                PriceListItemRepository.create({
                    "company_id": company_id,
                    "price_list_id": pl_gen_pur.id,
                    "item_type": PriceListItemType.YARN,
                    "yarn_count_id": count_30s.id,
                    "yarn_type": YarnCategory.GREY,
                    "min_quantity": Decimal("0.000"),
                    "max_quantity": Decimal("1000.000"),
                    "base_rate": Decimal("275.0000"),
                    "discount_percent": Decimal("0.00"),
                    "created_by": user_id,
                    "updated_by": user_id,
                })
                PriceListItemRepository.create({
                    "company_id": company_id,
                    "price_list_id": pl_gen_pur.id,
                    "item_type": PriceListItemType.YARN,
                    "yarn_count_id": count_30s.id,
                    "yarn_type": YarnCategory.GREY,
                    "min_quantity": Decimal("1001.000"),
                    "max_quantity": Decimal("5000.000"),
                    "base_rate": Decimal("275.0000"),
                    "discount_percent": Decimal("2.55"),  # Net ~268.00
                    "created_by": user_id,
                    "updated_by": user_id,
                })
                PriceListItemRepository.create({
                    "company_id": company_id,
                    "price_list_id": pl_gen_pur.id,
                    "item_type": PriceListItemType.YARN,
                    "yarn_count_id": count_30s.id,
                    "yarn_type": YarnCategory.GREY,
                    "min_quantity": Decimal("5001.000"),
                    "max_quantity": None,
                    "base_rate": Decimal("275.0000"),
                    "discount_percent": Decimal("4.73"),  # Net ~262.00
                    "created_by": user_id,
                    "updated_by": user_id,
                })
            if count_34s:
                PriceListItemRepository.create({
                    "company_id": company_id,
                    "price_list_id": pl_gen_pur.id,
                    "item_type": PriceListItemType.YARN,
                    "yarn_count_id": count_34s.id,
                    "yarn_type": YarnCategory.GREY,
                    "min_quantity": Decimal("0.000"),
                    "base_rate": Decimal("260.0000"),
                    "created_by": user_id,
                    "updated_by": user_id,
                })
            if count_40s:
                PriceListItemRepository.create({
                    "company_id": company_id,
                    "price_list_id": pl_gen_pur.id,
                    "item_type": PriceListItemType.YARN,
                    "yarn_count_id": count_40s.id,
                    "yarn_type": YarnCategory.GREY,
                    "min_quantity": Decimal("0.000"),
                    "base_rate": Decimal("310.0000"),
                    "created_by": user_id,
                    "updated_by": user_id,
                })
            if count_24s:
                PriceListItemRepository.create({
                    "company_id": company_id,
                    "price_list_id": pl_gen_pur.id,
                    "item_type": PriceListItemType.YARN,
                    "yarn_count_id": count_24s.id,
                    "yarn_type": YarnCategory.GREY,
                    "min_quantity": Decimal("0.000"),
                    "base_rate": Decimal("245.0000"),
                    "created_by": user_id,
                    "updated_by": user_id,
                })
            if count_2_40s:
                PriceListItemRepository.create({
                    "company_id": company_id,
                    "price_list_id": pl_gen_pur.id,
                    "item_type": PriceListItemType.YARN,
                    "yarn_count_id": count_2_40s.id,
                    "yarn_type": YarnCategory.WOUND,
                    "min_quantity": Decimal("0.000"),
                    "base_rate": Decimal("330.0000"),
                    "created_by": user_id,
                    "updated_by": user_id,
                })
        created_lists.append(pl_gen_pur)

        # 2. Party-Specific Yarn Purchase Price List (Mill Contract)
        if mill:
            pl_mill = PriceList.objects.filter(company_id=company_id, price_list_code="PL-PUR-LAKSHMI-2026", record_status="A").first()
            if not pl_mill:
                pl_mill = PriceListRepository.create({
                    "company_id": company_id,
                    "price_list_code": "PL-PUR-LAKSHMI-2026",
                    "price_list_name": f"{mill.name} - Annual Yarn Procurement Contract",
                    "list_type": PriceListType.PURCHASE,
                    "scope": PriceListScope.PARTY_SPECIFIC,
                    "party_id": mill.id,
                    "valid_from": start_date,
                    "valid_to": end_date,
                    "description": f"Agreed contract supply rates with {mill.name}.",
                    "created_by": user_id,
                    "updated_by": user_id,
                })
                if count_30s:
                    PriceListItemRepository.create({
                        "company_id": company_id,
                        "price_list_id": pl_mill.id,
                        "item_type": PriceListItemType.YARN,
                        "yarn_count_id": count_30s.id,
                        "yarn_type": YarnCategory.GREY,
                        "min_quantity": Decimal("0.000"),
                        "max_quantity": Decimal("2000.000"),
                        "base_rate": Decimal("265.0000"),
                        "created_by": user_id,
                        "updated_by": user_id,
                    })
                    PriceListItemRepository.create({
                        "company_id": company_id,
                        "price_list_id": pl_mill.id,
                        "item_type": PriceListItemType.YARN,
                        "yarn_count_id": count_30s.id,
                        "yarn_type": YarnCategory.GREY,
                        "min_quantity": Decimal("2001.000"),
                        "max_quantity": Decimal("10000.000"),
                        "base_rate": Decimal("258.0000"),
                        "created_by": user_id,
                        "updated_by": user_id,
                    })
                if count_40s:
                    PriceListItemRepository.create({
                        "company_id": company_id,
                        "price_list_id": pl_mill.id,
                        "item_type": PriceListItemType.YARN,
                        "yarn_count_id": count_40s.id,
                        "yarn_type": YarnCategory.GREY,
                        "min_quantity": Decimal("0.000"),
                        "base_rate": Decimal("298.0000"),
                        "created_by": user_id,
                        "updated_by": user_id,
                    })
            created_lists.append(pl_mill)

        # 3. General Yarn Sales Price List
        pl_gen_sales = PriceList.objects.filter(company_id=company_id, price_list_code="PL-SALES-GEN-2026", record_status="A").first()
        if not pl_gen_sales:
            pl_gen_sales = PriceListRepository.create({
                "company_id": company_id,
                "price_list_code": "PL-SALES-GEN-2026",
                "price_list_name": "Standard Commercial Yarn Sales Price List",
                "list_type": PriceListType.SALES,
                "scope": PriceListScope.GENERAL,
                "valid_from": start_date,
                "valid_to": end_date,
                "is_default": True,
                "description": "Standard market selling rates for commercial yarn sales.",
                "created_by": user_id,
                "updated_by": user_id,
            })
            if count_30s:
                PriceListItemRepository.create({
                    "company_id": company_id,
                    "price_list_id": pl_gen_sales.id,
                    "item_type": PriceListItemType.YARN,
                    "yarn_count_id": count_30s.id,
                    "yarn_type": YarnCategory.GREY,
                    "min_quantity": Decimal("0.000"),
                    "max_quantity": Decimal("1000.000"),
                    "base_rate": Decimal("295.0000"),
                    "created_by": user_id,
                    "updated_by": user_id,
                })
                PriceListItemRepository.create({
                    "company_id": company_id,
                    "price_list_id": pl_gen_sales.id,
                    "item_type": PriceListItemType.YARN,
                    "yarn_count_id": count_30s.id,
                    "yarn_type": YarnCategory.GREY,
                    "min_quantity": Decimal("1001.000"),
                    "max_quantity": Decimal("5000.000"),
                    "base_rate": Decimal("288.0000"),
                    "created_by": user_id,
                    "updated_by": user_id,
                })
            if count_40s:
                PriceListItemRepository.create({
                    "company_id": company_id,
                    "price_list_id": pl_gen_sales.id,
                    "item_type": PriceListItemType.YARN,
                    "yarn_count_id": count_40s.id,
                    "yarn_type": YarnCategory.GREY,
                    "min_quantity": Decimal("0.000"),
                    "base_rate": Decimal("335.0000"),
                    "created_by": user_id,
                    "updated_by": user_id,
                })
        created_lists.append(pl_gen_sales)

        # 4. Party-Specific Yarn Sales Price List (Customer Contract)
        if cust:
            pl_cust = PriceList.objects.filter(company_id=company_id, price_list_code="PL-SALES-CLASSIC-POLO", record_status="A").first()
            if not pl_cust:
                pl_cust = PriceListRepository.create({
                    "company_id": company_id,
                    "price_list_code": "PL-SALES-CLASSIC-POLO",
                    "price_list_name": f"{cust.name} - Annual Commercial Sales Contract",
                    "list_type": PriceListType.SALES,
                    "scope": PriceListScope.PARTY_SPECIFIC,
                    "party_id": cust.id,
                    "valid_from": start_date,
                    "valid_to": end_date,
                    "description": f"Contract selling rates for {cust.name}.",
                    "created_by": user_id,
                    "updated_by": user_id,
                })
                if count_30s:
                    PriceListItemRepository.create({
                        "company_id": company_id,
                        "price_list_id": pl_cust.id,
                        "item_type": PriceListItemType.YARN,
                        "yarn_count_id": count_30s.id,
                        "yarn_type": YarnCategory.GREY,
                        "min_quantity": Decimal("1000.000"),
                        "max_quantity": Decimal("5000.000"),
                        "base_rate": Decimal("282.0000"),
                        "created_by": user_id,
                        "updated_by": user_id,
                    })
                    PriceListItemRepository.create({
                        "company_id": company_id,
                        "price_list_id": pl_cust.id,
                        "item_type": PriceListItemType.YARN,
                        "yarn_count_id": count_30s.id,
                        "yarn_type": YarnCategory.DYED,
                        "min_quantity": Decimal("0.000"),
                        "base_rate": Decimal("345.0000"),
                        "created_by": user_id,
                        "updated_by": user_id,
                    })
                if count_40s:
                    PriceListItemRepository.create({
                        "company_id": company_id,
                        "price_list_id": pl_cust.id,
                        "item_type": PriceListItemType.YARN,
                        "yarn_count_id": count_40s.id,
                        "yarn_type": YarnCategory.GREY,
                        "min_quantity": Decimal("0.000"),
                        "base_rate": Decimal("320.0000"),
                        "created_by": user_id,
                        "updated_by": user_id,
                    })
            created_lists.append(pl_cust)

        # 5. General Knitting Job Work Price List
        from apps.process.models import parent_process_stage_table
        from apps.masters.models import FabricTypeMaster
        from core.constants import PartyTypes

        stage_knit = parent_process_stage_table.objects.filter(company_id=company_id, code__icontains="KNIT").first()
        stage_dye = parent_process_stage_table.objects.filter(company_id=company_id, code__icontains="DYE").first()
        ft_sj = FabricTypeMaster.objects.filter(company_id=company_id, name__icontains="Single Jersey").first()
        ft_rib = FabricTypeMaster.objects.filter(company_id=company_id, name__icontains="Rib").first()
        ft_interlock = FabricTypeMaster.objects.filter(company_id=company_id, name__icontains="Interlock").first()
        knitter = PartyMaster.objects.filter(company_id=company_id, party_type=PartyTypes.KNITTING_UNIT).first()
        if not knitter:
            knitter = PartyMaster.objects.filter(company_id=company_id, party_type=PartyTypes.JOB_WORKER).first()

        pl_knit_gen = PriceList.objects.filter(company_id=company_id, price_list_code="PL-JOB-KNIT-GEN-2026", record_status="A").first()
        if not pl_knit_gen and stage_knit:
            pl_knit_gen = PriceListRepository.create({
                "company_id": company_id,
                "price_list_code": "PL-JOB-KNIT-GEN-2026",
                "price_list_name": "Standard Knitting Conversion Price List 2026-27",
                "list_type": PriceListType.JOB_WORK,
                "scope": PriceListScope.GENERAL,
                "valid_from": start_date,
                "valid_to": end_date,
                "is_default": True,
                "description": "Standard market rates for circular knitting conversion per Kg.",
                "created_by": user_id,
                "updated_by": user_id,
            })
            # S.J Base
            PriceListJobRuleRepository.create({
                "company_id": company_id,
                "price_list_id": pl_knit_gen.id,
                "process_stage_id": stage_knit.id,
                "fabric_type_id": ft_sj.id if ft_sj else None,
                "yarn_count_id": count_30s.id if count_30s else None,
                "machine_gauge": "24GG",
                "dia_range": "24-34",
                "is_lycra_plated": False,
                "job_rate": Decimal("18.0000"),
                "allowed_loss_percent": Decimal("2.50"),
                "lycra_surcharge": Decimal("4.0000"),
                "min_quantity": Decimal("0.000"),
                "max_quantity": Decimal("5000.000"),
                "created_by": user_id,
                "updated_by": user_id,
            })
            # S.J High Volume Slab (> 5000 Kg)
            PriceListJobRuleRepository.create({
                "company_id": company_id,
                "price_list_id": pl_knit_gen.id,
                "process_stage_id": stage_knit.id,
                "fabric_type_id": ft_sj.id if ft_sj else None,
                "yarn_count_id": count_30s.id if count_30s else None,
                "machine_gauge": "24GG",
                "dia_range": "24-34",
                "job_rate": Decimal("16.5000"),
                "allowed_loss_percent": Decimal("2.00"),
                "lycra_surcharge": Decimal("3.5000"),
                "min_quantity": Decimal("5001.000"),
                "max_quantity": None,
                "created_by": user_id,
                "updated_by": user_id,
            })
            # Rib
            if ft_rib:
                PriceListJobRuleRepository.create({
                    "company_id": company_id,
                    "price_list_id": pl_knit_gen.id,
                    "process_stage_id": stage_knit.id,
                    "fabric_type_id": ft_rib.id,
                    "machine_gauge": "24GG",
                    "job_rate": Decimal("22.0000"),
                    "allowed_loss_percent": Decimal("3.00"),
                    "lycra_surcharge": Decimal("5.0000"),
                    "min_quantity": Decimal("0.000"),
                    "created_by": user_id,
                    "updated_by": user_id,
                })
            # Interlock
            if ft_interlock:
                PriceListJobRuleRepository.create({
                    "company_id": company_id,
                    "price_list_id": pl_knit_gen.id,
                    "process_stage_id": stage_knit.id,
                    "fabric_type_id": ft_interlock.id,
                    "machine_gauge": "28GG",
                    "job_rate": Decimal("25.0000"),
                    "allowed_loss_percent": Decimal("3.00"),
                    "min_quantity": Decimal("0.000"),
                    "created_by": user_id,
                    "updated_by": user_id,
                })
        if pl_knit_gen:
            created_lists.append(pl_knit_gen)

        # 6. Party-Specific Knitting Contract (Knitter Unit)
        if knitter and stage_knit:
            pl_knit_party = PriceList.objects.filter(company_id=company_id, price_list_code="PL-JOB-KNIT-ANNAI-2026", record_status="A").first()
            if not pl_knit_party:
                pl_knit_party = PriceListRepository.create({
                    "company_id": company_id,
                    "price_list_code": "PL-JOB-KNIT-ANNAI-2026",
                    "price_list_name": f"{knitter.name} - Annual Knitting Contract",
                    "list_type": PriceListType.JOB_WORK,
                    "scope": PriceListScope.PARTY_SPECIFIC,
                    "party_id": knitter.id,
                    "valid_from": start_date,
                    "valid_to": end_date,
                    "description": f"Contractual conversion rates agreed with {knitter.name}.",
                    "created_by": user_id,
                    "updated_by": user_id,
                })
                # Contract Single Jersey @ 16.00
                PriceListJobRuleRepository.create({
                    "company_id": company_id,
                    "price_list_id": pl_knit_party.id,
                    "process_stage_id": stage_knit.id,
                    "fabric_type_id": ft_sj.id if ft_sj else None,
                    "job_rate": Decimal("16.0000"),
                    "allowed_loss_percent": Decimal("2.00"),
                    "lycra_surcharge": Decimal("3.5000"),
                    "min_quantity": Decimal("0.000"),
                    "created_by": user_id,
                    "updated_by": user_id,
                })
                if ft_rib:
                    PriceListJobRuleRepository.create({
                        "company_id": company_id,
                        "price_list_id": pl_knit_party.id,
                        "process_stage_id": stage_knit.id,
                        "fabric_type_id": ft_rib.id,
                        "job_rate": Decimal("19.5000"),
                        "allowed_loss_percent": Decimal("2.50"),
                        "lycra_surcharge": Decimal("4.0000"),
                        "min_quantity": Decimal("0.000"),
                        "created_by": user_id,
                        "updated_by": user_id,
                    })
            created_lists.append(pl_knit_party)

        # 7. General Fabric Dyeing Job Work Price List
        pl_dye_gen = PriceList.objects.filter(company_id=company_id, price_list_code="PL-JOB-DYE-GEN-2026", record_status="A").first()
        if not pl_dye_gen and stage_dye:
            pl_dye_gen = PriceListRepository.create({
                "company_id": company_id,
                "price_list_code": "PL-JOB-DYE-GEN-2026",
                "price_list_name": "Standard Fabric Dyeing Conversion Price List 2026-27",
                "list_type": PriceListType.JOB_WORK,
                "scope": PriceListScope.GENERAL,
                "valid_from": start_date,
                "valid_to": end_date,
                "is_default": True,
                "description": "Standard soft-flow dyeing conversion charges categorized by shade depth.",
                "created_by": user_id,
                "updated_by": user_id,
            })
            dye_shades = [
                ("WHITE", Decimal("35.0000"), Decimal("3.00")),
                ("LIGHT", Decimal("45.0000"), Decimal("3.50")),
                ("MEDIUM", Decimal("55.0000"), Decimal("4.00")),
                ("DARK", Decimal("65.0000"), Decimal("4.50")),
                ("EXTRA_DARK", Decimal("78.0000"), Decimal("5.00")),
            ]
            for shade_cat, rate, loss in dye_shades:
                PriceListJobRuleRepository.create({
                    "company_id": company_id,
                    "price_list_id": pl_dye_gen.id,
                    "process_stage_id": stage_dye.id,
                    "shade_category": shade_cat,
                    "job_rate": rate,
                    "allowed_loss_percent": loss,
                    "special_finish_surcharge": Decimal("8.0000"),
                    "min_quantity": Decimal("0.000"),
                    "created_by": user_id,
                    "updated_by": user_id,
                })
        if pl_dye_gen:
            created_lists.append(pl_dye_gen)

        # 8. Seed sample pricing audit log entries if none exist
        if not PricingAudit.objects.filter(company_id=company_id).exists():
            # Audit 1: Standard Rate Confirmation for YARN_PO #1
            PricingAuditRepository.create({
                "company_id": company_id,
                "document_type": "YARN_PO",
                "document_id": 1,
                "line_item_id": 1,
                "resolved_price_list_id": pl_gen_pur.id if pl_gen_pur else None,
                "resolved_rule_id": 1,
                "system_rate": Decimal("275.0000"),
                "actual_rate": Decimal("275.0000"),
                "is_override": False,
                "override_reason": "Standard purchase price list rate confirmed",
                "approved_by": user_id,
                "created_by": user_id,
            })
            # Audit 2: Approved Spot Concession Override for YARN_PO #2
            PricingAuditRepository.create({
                "company_id": company_id,
                "document_type": "YARN_PO",
                "document_id": 2,
                "line_item_id": 1,
                "resolved_price_list_id": pl_gen_pur.id if pl_gen_pur else None,
                "resolved_rule_id": 1,
                "system_rate": Decimal("275.0000"),
                "actual_rate": Decimal("268.0000"),
                "is_override": True,
                "override_reason": "Managing Director approved spot bulk quantity concession",
                "approved_by": user_id or 1,
                "created_by": user_id,
            })
            # Audit 3: Mill Contract Supply for YARN_PO #3
            PricingAuditRepository.create({
                "company_id": company_id,
                "document_type": "YARN_PO",
                "document_id": 3,
                "line_item_id": 1,
                "resolved_price_list_id": None,
                "resolved_rule_id": None,
                "system_rate": Decimal("265.0000"),
                "actual_rate": Decimal("265.0000"),
                "is_override": False,
                "override_reason": "Contract procurement rate applied from SVT Mills contract",
                "approved_by": user_id,
                "created_by": user_id,
            })
            # Audit 4: Job Work Knitting Rate for PROCESS_PROGRAM #1
            PricingAuditRepository.create({
                "company_id": company_id,
                "document_type": "PROCESS_PROGRAM",
                "document_id": 1,
                "line_item_id": 1,
                "resolved_price_list_id": pl_knit_gen.id if pl_knit_gen else None,
                "resolved_rule_id": 1,
                "system_rate": Decimal("18.0000"),
                "actual_rate": Decimal("18.0000"),
                "is_override": False,
                "override_reason": "Single jersey knitting conversion standard rate applied",
                "approved_by": user_id,
                "created_by": user_id,
            })
            # Audit 5: Dyeing Surcharge Trial Override for PROCESS_PROGRAM #2
            PricingAuditRepository.create({
                "company_id": company_id,
                "document_type": "PROCESS_PROGRAM",
                "document_id": 2,
                "line_item_id": 1,
                "resolved_price_list_id": pl_dye_gen.id if pl_dye_gen else None,
                "resolved_rule_id": 4,
                "system_rate": Decimal("73.0000"),
                "actual_rate": Decimal("70.0000"),
                "is_override": True,
                "override_reason": "General Manager approved introductory bio-wash trial rebate (-Rs.3.00/Kg)",
                "approved_by": user_id or 1,
                "created_by": user_id,
            })

        return [pl for pl in created_lists if pl]


class PricingResolutionService:
    """
    Unified Rate Determination Engine.
    Implements deterministic multi-tier resolution for transactions (Yarn PO, Yarn Sales).
    """

    @classmethod
    def resolve_yarn_rate(
        cls,
        company_id: int,
        context_type: str,            # PURCHASE or SALES
        doc_date,                     # calendar date of transaction
        party_id: Optional[int] = None,
        yarn_count_id: Optional[int] = None,
        yarn_type: Optional[str] = None,
        color_shade_id: Optional[int] = None,
        quantity: Optional[Decimal] = None,
        item_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes resolution priority hierarchy for Yarn transactions:
        1. Active Party-Specific Price List (with matching volume slab)
        2. Active Party-Specific Price List (base line, without slab)
        3. Active General Base Price List (with matching volume slab)
        4. Active General Base Price List (base line, without slab)
        5. Unresolved (prompts manual rate entry)
        """
        qty = Decimal(str(quantity)) if quantity is not None else None

        # Tier 1 & 2: Party-Specific Resolution
        if party_id:
            party_lists = list(PriceListRepository.find_active_party_lists(
                company_id=company_id,
                list_type=context_type,
                party_id=party_id,
                doc_date=doc_date
            ))
            if party_lists:
                p_list_ids = [pl.id for pl in party_lists]

                # Attempt slab match first
                if qty is not None:
                    matched_items = list(PriceListItemRepository.find_matching_items(
                        company_id=company_id,
                        price_list_ids=p_list_ids,
                        item_type=PriceListItemType.YARN,
                        item_id=item_id,
                        yarn_count_id=yarn_count_id,
                        yarn_type=yarn_type,
                        color_shade_id=color_shade_id,
                        quantity=qty
                    ))
                    if matched_items:
                        best = matched_items[0]
                        pl = next(p for p in party_lists if p.id == best.price_list_id)
                        return cls._format_result(best, pl, source="PARTY_SPECIFIC", is_slab_applied=True)

                # Attempt match without slab (base rate)
                matched_items = list(PriceListItemRepository.find_matching_items(
                    company_id=company_id,
                    price_list_ids=p_list_ids,
                    item_type=PriceListItemType.YARN,
                    item_id=item_id,
                    yarn_count_id=yarn_count_id,
                    yarn_type=yarn_type,
                    color_shade_id=color_shade_id,
                    quantity=None
                ))
                if matched_items:
                    best = matched_items[0]
                    pl = next(p for p in party_lists if p.id == best.price_list_id)
                    return cls._format_result(best, pl, source="PARTY_SPECIFIC", is_slab_applied=False)

        # Tier 3 & 4: General Base Price List Resolution
        general_lists = list(PriceListRepository.find_active_general_lists(
            company_id=company_id,
            list_type=context_type,
            doc_date=doc_date
        ))
        if general_lists:
            g_list_ids = [gl.id for gl in general_lists]

            # Attempt slab match in general list
            if qty is not None:
                matched_items = list(PriceListItemRepository.find_matching_items(
                    company_id=company_id,
                    price_list_ids=g_list_ids,
                    item_type=PriceListItemType.YARN,
                    item_id=item_id,
                    yarn_count_id=yarn_count_id,
                    yarn_type=yarn_type,
                    color_shade_id=color_shade_id,
                    quantity=qty
                ))
                if matched_items:
                    best = matched_items[0]
                    pl = next(p for p in general_lists if p.id == best.price_list_id)
                    return cls._format_result(best, pl, source="GENERAL", is_slab_applied=True)

            # Attempt match without slab in general list
            matched_items = list(PriceListItemRepository.find_matching_items(
                company_id=company_id,
                price_list_ids=g_list_ids,
                item_type=PriceListItemType.YARN,
                item_id=item_id,
                yarn_count_id=yarn_count_id,
                yarn_type=yarn_type,
                color_shade_id=color_shade_id,
                quantity=None
            ))
            if matched_items:
                best = matched_items[0]
                pl = next(p for p in general_lists if p.id == best.price_list_id)
                return cls._format_result(best, pl, source="GENERAL", is_slab_applied=False)

        # Tier 5: Fallback / Unresolved
        return {
            "is_resolved": False,
            "resolved_rate": None,
            "base_rate": None,
            "discount_percent": "0.00",
            "net_rate": None,
            "pricing_source": "MANUAL",
            "price_list_id": None,
            "price_list_code": None,
            "rule_id": None,
            "is_slab_applied": False,
            "min_quantity": None,
            "max_quantity": None,
            "currency_code": "INR",
            "message": "No active matching price list found. Manual rate entry required."
        }

    @classmethod
    def record_override_audit(
        cls,
        company_id: int,
        document_type: str,
        document_id: int,
        system_rate: Decimal,
        actual_rate: Decimal,
        resolved_price_list_id: Optional[int] = None,
        resolved_rule_id: Optional[int] = None,
        override_reason: Optional[str] = None,
        approved_by: Optional[int] = None,
        created_by: Optional[int] = None,
        line_item_id: Optional[int] = None
    ) -> PricingAudit:
        """Records a pricing audit entry when actual_rate != system_rate or for verification."""
        is_override = (Decimal(str(system_rate or 0)) != Decimal(str(actual_rate or 0)))
        return PricingAuditRepository.create({
            "company_id": company_id,
            "document_type": document_type,
            "document_id": document_id,
            "line_item_id": line_item_id,
            "resolved_price_list_id": resolved_price_list_id,
            "resolved_rule_id": resolved_rule_id,
            "system_rate": system_rate,
            "actual_rate": actual_rate,
            "is_override": is_override,
            "override_reason": override_reason or ("Rate override" if is_override else "System rate confirmed"),
            "approved_by": approved_by,
            "created_by": created_by
        })

    @staticmethod
    def _format_result(item: PriceListItem, price_list: PriceList, source: str, is_slab_applied: bool) -> Dict[str, Any]:
        return {
            "is_resolved": True,
            "resolved_rate": str(item.net_rate),
            "base_rate": str(item.base_rate),
            "discount_percent": str(item.discount_percent),
            "net_rate": str(item.net_rate),
            "pricing_source": source,
            "price_list_id": price_list.id,
            "price_list_code": price_list.price_list_code,
            "price_list_name": price_list.price_list_name,
            "rule_id": item.id,
            "is_slab_applied": is_slab_applied,
            "min_quantity": str(item.min_quantity),
            "max_quantity": str(item.max_quantity) if item.max_quantity is not None else None,
            "currency_code": "INR",
            "is_manual_override_allowed": True
        }

    @classmethod
    def resolve_job_work_rate(
        cls,
        company_id: int,
        process_stage_id: int,
        doc_date=None,
        party_id: Optional[int] = None,
        fabric_type_id: Optional[int] = None,
        yarn_count_id: Optional[int] = None,
        machine_gauge: Optional[str] = None,
        dia_range: Optional[str] = None,
        is_lycra_plated: Optional[bool] = None,
        shade_category: Optional[str] = None,
        garment_style_category: Optional[str] = None,
        quantity: Optional[Decimal] = None,
        special_finish_requested: Optional[bool] = None,
        print_color_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Executes resolution priority hierarchy for Job Work subcontract conversion operations:
        1. Active Party-Specific Job Work Price List (with matching volume slab)
        2. Active Party-Specific Job Work Price List (base rule without slab)
        3. Active General Base Job Work Price List (with matching volume slab)
        4. Active General Base Job Work Price List (base rule without slab)
        5. Process Stage Master (mx_process_stage.standard_rate fallback)
        6. Unresolved (prompts manual rate entry)
        """
        if doc_date is None:
            doc_date = timezone.now().date()

        qty = Decimal(str(quantity)) if quantity is not None else None

        # Tier 1 & 2: Party-Specific Resolution
        if party_id:
            party_lists = list(PriceListRepository.find_active_party_lists(
                company_id=company_id,
                list_type=PriceListType.JOB_WORK,
                party_id=party_id,
                doc_date=doc_date
            ))
            if party_lists:
                p_list_ids = [pl.id for pl in party_lists]

                # Attempt slab match first
                if qty is not None:
                    matched_rules = list(PriceListJobRuleRepository.find_matching_rules(
                        company_id=company_id,
                        price_list_ids=p_list_ids,
                        process_stage_id=process_stage_id,
                        fabric_type_id=fabric_type_id,
                        yarn_count_id=yarn_count_id,
                        machine_gauge=machine_gauge,
                        is_lycra_plated=is_lycra_plated,
                        shade_category=shade_category,
                        garment_style_category=garment_style_category,
                        quantity=qty
                    ))
                    if matched_rules:
                        best = matched_rules[0]
                        pl = next(p for p in party_lists if p.id == best.price_list_id)
                        return cls._format_job_rule_result(
                            best, pl, source="PARTY_SPECIFIC", is_slab_applied=True,
                            is_lycra_plated=is_lycra_plated, special_finish_requested=special_finish_requested
                        )

                # Attempt match without slab (base rate)
                matched_rules = list(PriceListJobRuleRepository.find_matching_rules(
                    company_id=company_id,
                    price_list_ids=p_list_ids,
                    process_stage_id=process_stage_id,
                    fabric_type_id=fabric_type_id,
                    yarn_count_id=yarn_count_id,
                    machine_gauge=machine_gauge,
                    is_lycra_plated=is_lycra_plated,
                    shade_category=shade_category,
                    garment_style_category=garment_style_category,
                    quantity=None
                ))
                if matched_rules:
                    best = matched_rules[0]
                    pl = next(p for p in party_lists if p.id == best.price_list_id)
                    return cls._format_job_rule_result(
                        best, pl, source="PARTY_SPECIFIC", is_slab_applied=False,
                        is_lycra_plated=is_lycra_plated, special_finish_requested=special_finish_requested
                    )

        # Tier 3 & 4: General Base Price List Resolution
        general_lists = list(PriceListRepository.find_active_general_lists(
            company_id=company_id,
            list_type=PriceListType.JOB_WORK,
            doc_date=doc_date
        ))
        if general_lists:
            g_list_ids = [gl.id for gl in general_lists]

            # Attempt slab match in general list
            if qty is not None:
                matched_rules = list(PriceListJobRuleRepository.find_matching_rules(
                    company_id=company_id,
                    price_list_ids=g_list_ids,
                    process_stage_id=process_stage_id,
                    fabric_type_id=fabric_type_id,
                    yarn_count_id=yarn_count_id,
                    machine_gauge=machine_gauge,
                    is_lycra_plated=is_lycra_plated,
                    shade_category=shade_category,
                    garment_style_category=garment_style_category,
                    quantity=qty
                ))
                if matched_rules:
                    best = matched_rules[0]
                    pl = next(p for p in general_lists if p.id == best.price_list_id)
                    return cls._format_job_rule_result(
                        best, pl, source="GENERAL", is_slab_applied=True,
                        is_lycra_plated=is_lycra_plated, special_finish_requested=special_finish_requested
                    )

            # Attempt match without slab in general list
            matched_rules = list(PriceListJobRuleRepository.find_matching_rules(
                company_id=company_id,
                price_list_ids=g_list_ids,
                process_stage_id=process_stage_id,
                fabric_type_id=fabric_type_id,
                yarn_count_id=yarn_count_id,
                machine_gauge=machine_gauge,
                is_lycra_plated=is_lycra_plated,
                shade_category=shade_category,
                garment_style_category=garment_style_category,
                quantity=None
            ))
            if matched_rules:
                best = matched_rules[0]
                pl = next(p for p in general_lists if p.id == best.price_list_id)
                return cls._format_job_rule_result(
                    best, pl, source="GENERAL", is_slab_applied=False,
                    is_lycra_plated=is_lycra_plated, special_finish_requested=special_finish_requested
                )

        # Tier 5: Process Stage Master Standard Rate Fallback
        try:
            from apps.process.models import parent_process_stage_table
            stage = parent_process_stage_table.objects.filter(id=process_stage_id, company_id=company_id).first()
            if stage and stage.standard_rate and stage.standard_rate > Decimal("0.00"):
                rate_str = str(stage.standard_rate)
                loss_str = str(stage.standard_loss_percent)
                return {
                    "is_resolved": True,
                    "resolved_rate": rate_str,
                    "base_rate": rate_str,
                    "job_rate": rate_str,
                    "lycra_surcharge": "0.0000",
                    "special_finish_surcharge": "0.0000",
                    "total_rate": rate_str,
                    "allowed_loss_percent": loss_str,
                    "pricing_source": "STAGE_STANDARD",
                    "price_list_id": None,
                    "price_list_code": None,
                    "price_list_name": None,
                    "rule_id": None,
                    "uom_id": None,
                    "process_stage_id": stage.id,
                    "is_slab_applied": False,
                    "min_quantity": None,
                    "max_quantity": None,
                    "currency_code": "INR",
                    "is_manual_override_allowed": True,
                    "rate_breakdown": {
                        "base_job_rate": rate_str,
                        "lycra_surcharge": "0.0000",
                        "special_finish_surcharge": "0.0000",
                        "total_effective_rate": rate_str,
                        "allowed_loss_percent": loss_str
                    },
                    "message": f"Resolved from Stage Master standard rate for {stage.name}."
                }
        except Exception:
            pass

        # Tier 6: Unresolved / Manual entry required
        return {
            "is_resolved": False,
            "resolved_rate": None,
            "base_rate": None,
            "job_rate": None,
            "lycra_surcharge": "0.0000",
            "special_finish_surcharge": "0.0000",
            "total_rate": None,
            "allowed_loss_percent": "0.00",
            "pricing_source": "MANUAL",
            "price_list_id": None,
            "price_list_code": None,
            "price_list_name": None,
            "rule_id": None,
            "uom_id": None,
            "process_stage_id": process_stage_id,
            "is_slab_applied": False,
            "min_quantity": None,
            "max_quantity": None,
            "currency_code": "INR",
            "is_manual_override_allowed": True,
            "rate_breakdown": None,
            "message": "No active matching Job Work price list found. Manual subcontract rate entry required."
        }

    @staticmethod
    def _format_job_rule_result(
        rule: PriceListJobRule,
        price_list: PriceList,
        source: str,
        is_slab_applied: bool,
        is_lycra_plated: Optional[bool] = None,
        special_finish_requested: Optional[bool] = None
    ) -> Dict[str, Any]:
        base_rate = Decimal(str(rule.job_rate or 0))
        lycra_sc = Decimal(str(rule.lycra_surcharge or 0)) if is_lycra_plated else Decimal("0.0000")
        finish_sc = Decimal(str(rule.special_finish_surcharge or 0)) if special_finish_requested else Decimal("0.0000")
        total_rate = (base_rate + lycra_sc + finish_sc).quantize(Decimal("0.0001"))

        return {
            "is_resolved": True,
            "resolved_rate": str(total_rate),
            "base_rate": str(base_rate),
            "job_rate": str(base_rate),
            "lycra_surcharge": str(lycra_sc),
            "special_finish_surcharge": str(finish_sc),
            "total_rate": str(total_rate),
            "allowed_loss_percent": str(rule.allowed_loss_percent),
            "pricing_source": source,
            "price_list_id": price_list.id,
            "price_list_code": price_list.price_list_code,
            "price_list_name": price_list.price_list_name,
            "rule_id": rule.id,
            "uom_id": rule.uom_id,
            "process_stage_id": rule.process_stage_id,
            "is_slab_applied": is_slab_applied,
            "min_quantity": str(rule.min_quantity),
            "max_quantity": str(rule.max_quantity) if rule.max_quantity is not None else None,
            "currency_code": "INR",
            "is_manual_override_allowed": True,
            "rate_breakdown": {
                "base_job_rate": str(base_rate),
                "lycra_surcharge": str(lycra_sc),
                "special_finish_surcharge": str(finish_sc),
                "total_effective_rate": str(total_rate),
                "allowed_loss_percent": str(rule.allowed_loss_percent)
            }
        }
