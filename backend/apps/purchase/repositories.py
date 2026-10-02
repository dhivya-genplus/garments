from __future__ import annotations
from typing import Optional, List
from django.db.models import QuerySet
from apps.purchase.models import parent_po_table, child_po_table, yarn_po_delivery_table


class YarnPORepository:
    @staticmethod
    def get_by_id(po_id: int) -> Optional[parent_po_table]:
        return (
            parent_po_table.objects
            .select_related("company", "cfyear", "party", "mill", "yarn_count", "color_shade", "authorized_by")
            .prefetch_related("line_items", "deliveries")
            .filter(id=po_id, status=1)
            .first()
        )

    @staticmethod
    def get_by_po_number(po_number: str, company_id: int) -> Optional[parent_po_table]:
        return (
            parent_po_table.objects
            .select_related("company", "cfyear", "party", "mill", "yarn_count", "color_shade")
            .filter(po_number=po_number, company_id=company_id, status=1)
            .first()
        )

    @staticmethod
    def list_by_company(
        company_id: int,
        yarn_type: Optional[str] = None,
        party_id: Optional[int] = None,
        mill_id: Optional[int] = None,
        is_authorized: Optional[int] = None,
        is_complete: Optional[int] = None
    ) -> QuerySet[parent_po_table]:
        qs = (
            parent_po_table.objects
            .select_related("company", "cfyear", "party", "mill", "yarn_count", "color_shade")
            .filter(company_id=company_id, status=1)
        )
        if yarn_type:
            qs = qs.filter(yarn_type=yarn_type)
        if party_id:
            qs = qs.filter(party_id=party_id)
        if mill_id:
            qs = qs.filter(mill_id=mill_id)
        if is_authorized is not None:
            qs = qs.filter(is_authorized=is_authorized)
        if is_complete is not None:
            qs = qs.filter(is_complete=is_complete)
        return qs.order_by("-po_date", "-id")

    @staticmethod
    def create(data: dict) -> parent_po_table:
        return parent_po_table.objects.create(**data)

    @staticmethod
    def update(instance: parent_po_table, data: dict) -> parent_po_table:
        for field, value in data.items():
            setattr(instance, field, value)
        instance.save()
        return instance


class YarnPOLineItemRepository:
    @staticmethod
    def list_by_po(po_id: int) -> QuerySet[child_po_table]:
        return (
            child_po_table.objects
            .select_related("yarn_count", "color_shade")
            .filter(tm_po_id=po_id, status=1)
            .order_by("id")
        )

    @staticmethod
    def bulk_create(items: list[child_po_table]) -> list[child_po_table]:
        return child_po_table.objects.bulk_create(items)


class YarnPODeliveryRepository:
    @staticmethod
    def list_by_po(po_id: int) -> QuerySet[yarn_po_delivery_table]:
        return (
            yarn_po_delivery_table.objects
            .select_related("yarn_count", "party")
            .filter(tm_po_id=po_id, status=1)
            .order_by("delivery_date", "id")
        )

    @staticmethod
    def bulk_create(items: list[yarn_po_delivery_table]) -> list[yarn_po_delivery_table]:
        return yarn_po_delivery_table.objects.bulk_create(items)
