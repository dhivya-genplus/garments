from __future__ import annotations
from typing import Optional
from decimal import Decimal
from django.db.models import QuerySet
from apps.inventory.models import (
    yarn_stock_table, parent_yarn_inward_table, child_yarn_inward_table,
    parent_yarn_outward_table, child_yarn_outward_table
)


class YarnStockRepository:
    @staticmethod
    def get_or_create(
        company_id: int,
        warehouse_id: int,
        yarn_type: str,
        yarn_count_id: int,
        mill_id: int,
        color_shade_id: Optional[int],
        lot_no: str
    ) -> yarn_stock_table:
        stock, _ = yarn_stock_table.objects.get_or_create(
            company_id=company_id,
            warehouse_id=warehouse_id,
            yarn_type=yarn_type,
            yarn_count_id=yarn_count_id,
            mill_id=mill_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no or "GEN"
        )
        return stock

    @staticmethod
    def list_available_stock(
        company_id: int,
        warehouse_id: Optional[int] = None,
        yarn_type: Optional[str] = None,
        yarn_count_id: Optional[int] = None
    ) -> QuerySet[yarn_stock_table]:
        qs = (
            yarn_stock_table.objects
            .select_related("warehouse", "yarn_count", "mill", "color_shade")
            .filter(company_id=company_id, balance_quantity__gt=Decimal("0.000"))
        )
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        if yarn_type:
            qs = qs.filter(yarn_type=yarn_type)
        if yarn_count_id:
            qs = qs.filter(yarn_count_id=yarn_count_id)
        return qs.order_by("yarn_type", "yarn_count__count", "lot_no")


class YarnInwardRepository:
    @staticmethod
    def get_by_id(inward_id: int) -> Optional[parent_yarn_inward_table]:
        return (
            parent_yarn_inward_table.objects
            .select_related("company", "cfyear", "party", "mill", "warehouse", "yarn_count", "color_shade", "po")
            .prefetch_related("line_items")
            .filter(id=inward_id, status=1)
            .first()
        )

    @staticmethod
    def list_by_company(company_id: int, yarn_type: Optional[str] = None) -> QuerySet[parent_yarn_inward_table]:
        qs = (
            parent_yarn_inward_table.objects
            .select_related("party", "mill", "warehouse", "yarn_count", "color_shade", "po")
            .filter(company_id=company_id, status=1)
        )
        if yarn_type:
            qs = qs.filter(yarn_type=yarn_type)
        return qs.order_by("-inward_date", "-id")


class YarnOutwardRepository:
    @staticmethod
    def get_by_id(outward_id: int) -> Optional[parent_yarn_outward_table]:
        return (
            parent_yarn_outward_table.objects
            .select_related("company", "cfyear", "warehouse", "destination_party", "yarn_count", "mill", "color_shade")
            .prefetch_related("line_items")
            .filter(id=outward_id, status=1)
            .first()
        )

    @staticmethod
    def list_by_company(
        company_id: int,
        outward_type: Optional[str] = None,
        yarn_type: Optional[str] = None
    ) -> QuerySet[parent_yarn_outward_table]:
        qs = (
            parent_yarn_outward_table.objects
            .select_related("warehouse", "destination_party", "yarn_count", "mill", "color_shade")
            .filter(company_id=company_id, status=1)
        )
        if outward_type:
            qs = qs.filter(outward_type=outward_type)
        if yarn_type:
            qs = qs.filter(yarn_type=yarn_type)
        return qs.order_by("-outward_date", "-id")
