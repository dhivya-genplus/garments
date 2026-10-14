from __future__ import annotations
from decimal import Decimal
from typing import Optional, List
from django.db.models import QuerySet, Q, F
from apps.pricing.models import PriceList, PriceListItem, PriceListJobRule, PricingAudit
from core.constants import PriceListType, PriceListScope, PriceListItemType


class PriceListRepository:
    @staticmethod
    def get_by_id(price_list_id: int, company_id: int) -> Optional[PriceList]:
        return PriceList.objects.filter(id=price_list_id, company_id=company_id, record_status="A").first()

    @staticmethod
    def list_by_company(
        company_id: int,
        list_type: Optional[str] = None,
        scope: Optional[str] = None,
        party_id: Optional[int] = None
    ) -> QuerySet[PriceList]:
        qs = PriceList.objects.filter(company_id=company_id, record_status="A")
        if list_type:
            qs = qs.filter(list_type=list_type)
        if scope:
            qs = qs.filter(scope=scope)
        if party_id is not None:
            qs = qs.filter(party_id=party_id)
        return qs.order_by("-valid_from", "-id")

    @staticmethod
    def find_active_party_lists(
        company_id: int,
        list_type: str,
        party_id: int,
        doc_date
    ) -> QuerySet[PriceList]:
        """Finds party-specific price lists active on doc_date."""
        return PriceList.objects.filter(
            company_id=company_id,
            list_type=list_type,
            scope=PriceListScope.PARTY_SPECIFIC,
            party_id=party_id,
            valid_from__lte=doc_date,
            valid_to__gte=doc_date,
            record_status="A"
        ).order_by("-id")

    @staticmethod
    def find_active_general_lists(
        company_id: int,
        list_type: str,
        doc_date
    ) -> QuerySet[PriceList]:
        """Finds general base price lists active on doc_date."""
        return PriceList.objects.filter(
            company_id=company_id,
            list_type=list_type,
            scope=PriceListScope.GENERAL,
            valid_from__lte=doc_date,
            valid_to__gte=doc_date,
            record_status="A"
        ).order_by("-is_default", "-id")

    @staticmethod
    def create(data: dict) -> PriceList:
        return PriceList.objects.create(**data)

    @staticmethod
    def update(price_list: PriceList, data: dict) -> PriceList:
        for attr, value in data.items():
            setattr(price_list, attr, value)
        price_list.save()
        return price_list


class PriceListItemRepository:
    @staticmethod
    def get_by_id(item_id: int, company_id: int) -> Optional[PriceListItem]:
        return PriceListItem.objects.filter(id=item_id, company_id=company_id, record_status="A").first()

    @staticmethod
    def list_by_price_list(price_list_id: int, company_id: int) -> QuerySet[PriceListItem]:
        return PriceListItem.objects.filter(
            price_list_id=price_list_id,
            company_id=company_id,
            record_status="A"
        ).order_by("item_type", "yarn_count_id", "min_quantity")

    @staticmethod
    def find_matching_items(
        company_id: int,
        price_list_ids: List[int],
        item_type: str = PriceListItemType.YARN,
        item_id: Optional[int] = None,
        yarn_count_id: Optional[int] = None,
        yarn_type: Optional[str] = None,
        color_shade_id: Optional[int] = None,
        quantity: Optional[Decimal] = None
    ) -> QuerySet[PriceListItem]:
        """
        Finds matching line items within the given candidate price lists.
        Filters by technical specs and optional quantity slabs.
        """
        qs = PriceListItem.objects.filter(
            company_id=company_id,
            price_list_id__in=price_list_ids,
            item_type=item_type,
            record_status="A"
        )
        if item_id is not None:
            qs = qs.filter(Q(item_id=item_id) | Q(item_id__isnull=True))

        if yarn_count_id is not None:
            qs = qs.filter(Q(yarn_count_id=yarn_count_id) | Q(yarn_count_id__isnull=True))

        if yarn_type is not None:
            qs = qs.filter(Q(yarn_type=yarn_type) | Q(yarn_type__isnull=True) | Q(yarn_type=""))

        if color_shade_id is not None:
            qs = qs.filter(Q(color_shade_id=color_shade_id) | Q(color_shade_id__isnull=True))

        if quantity is not None:
            qty = Decimal(str(quantity))
            qs = qs.filter(
                min_quantity__lte=qty
            ).filter(
                Q(max_quantity__gte=qty) | Q(max_quantity__isnull=True)
            )

        return qs.order_by("-min_quantity", "-id")

    @staticmethod
    def create(data: dict) -> PriceListItem:
        return PriceListItem.objects.create(**data)

    @staticmethod
    def update(item: PriceListItem, data: dict) -> PriceListItem:
        for attr, value in data.items():
            setattr(item, attr, value)
        item.save()
        return item


class PriceListJobRuleRepository:
    @staticmethod
    def get_by_id(rule_id: int, company_id: int) -> Optional[PriceListJobRule]:
        return PriceListJobRule.objects.filter(id=rule_id, company_id=company_id, record_status="A").first()

    @staticmethod
    def list_by_price_list(price_list_id: int, company_id: int) -> QuerySet[PriceListJobRule]:
        return PriceListJobRule.objects.filter(
            price_list_id=price_list_id,
            company_id=company_id,
            record_status="A"
        ).order_by("process_stage_id", "min_quantity")

    @staticmethod
    def find_matching_rules(
        company_id: int,
        price_list_ids: List[int],
        process_stage_id: int,
        fabric_type_id: Optional[int] = None,
        yarn_count_id: Optional[int] = None,
        machine_gauge: Optional[str] = None,
        is_lycra_plated: Optional[bool] = None,
        shade_category: Optional[str] = None,
        garment_style_category: Optional[str] = None,
        quantity: Optional[Decimal] = None
    ) -> QuerySet[PriceListJobRule]:
        qs = PriceListJobRule.objects.filter(
            company_id=company_id,
            price_list_id__in=price_list_ids,
            process_stage_id=process_stage_id,
            record_status="A"
        )
        if fabric_type_id is not None:
            qs = qs.filter(Q(fabric_type_id=fabric_type_id) | Q(fabric_type_id__isnull=True))

        if yarn_count_id is not None:
            qs = qs.filter(Q(yarn_count_id=yarn_count_id) | Q(yarn_count_id__isnull=True))

        if machine_gauge is not None:
            qs = qs.filter(Q(machine_gauge__iexact=machine_gauge) | Q(machine_gauge__isnull=True) | Q(machine_gauge=""))

        if is_lycra_plated is not None:
            qs = qs.filter(Q(is_lycra_plated=is_lycra_plated) | Q(is_lycra_plated__isnull=True))

        if shade_category is not None:
            qs = qs.filter(Q(shade_category__iexact=shade_category) | Q(shade_category__isnull=True) | Q(shade_category=""))

        if garment_style_category is not None:
            qs = qs.filter(Q(garment_style_category__iexact=garment_style_category) | Q(garment_style_category__isnull=True) | Q(garment_style_category=""))

        if quantity is not None:
            qty = Decimal(str(quantity))
            qs = qs.filter(
                min_quantity__lte=qty
            ).filter(
                Q(max_quantity__gte=qty) | Q(max_quantity__isnull=True)
            )

        return qs.order_by(
            F("fabric_type_id").desc(nulls_last=True),
            F("yarn_count_id").desc(nulls_last=True),
            F("shade_category").desc(nulls_last=True),
            "-min_quantity",
            "-id"
        )

    @staticmethod
    def create(data: dict) -> PriceListJobRule:
        return PriceListJobRule.objects.create(**data)

    @staticmethod
    def update(rule: PriceListJobRule, data: dict) -> PriceListJobRule:
        for attr, value in data.items():
            setattr(rule, attr, value)
        rule.save()
        return rule


class PricingAuditRepository:
    @staticmethod
    def create(data: dict) -> PricingAudit:
        return PricingAudit.objects.create(**data)

    @staticmethod
    def list_by_document(company_id: int, document_type: str, document_id: int) -> QuerySet[PricingAudit]:
        return PricingAudit.objects.filter(
            company_id=company_id,
            document_type=document_type,
            document_id=document_id
        ).order_by("-created_at")

    @staticmethod
    def list_by_company(
        company_id: int,
        document_type: Optional[str] = None,
        document_id: Optional[int] = None,
        is_override: Optional[bool] = None
    ) -> QuerySet[PricingAudit]:
        qs = PricingAudit.objects.filter(company_id=company_id)
        if document_type:
            qs = qs.filter(document_type=document_type)
        if document_id is not None:
            qs = qs.filter(document_id=document_id)
        if is_override is not None:
            qs = qs.filter(is_override=is_override)
        return qs.order_by("-created_at")
