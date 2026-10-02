from __future__ import annotations
from typing import Optional
from django.db.models import QuerySet
from apps.sales.models import (
    parent_yarn_sales_table, child_yarn_sales_table,
    parent_yarn_sales_return_table, child_yarn_sales_return_table
)


class YarnSalesRepository:
    @staticmethod
    def get_by_id(sales_id: int) -> Optional[parent_yarn_sales_table]:
        return (
            parent_yarn_sales_table.objects
            .select_related("company", "cfyear", "warehouse", "customer", "yarn_count", "mill", "color_shade")
            .prefetch_related("line_items")
            .filter(id=sales_id, status=1)
            .first()
        )

    @staticmethod
    def list_by_company(company_id: int, yarn_type: Optional[str] = None) -> QuerySet[parent_yarn_sales_table]:
        qs = (
            parent_yarn_sales_table.objects
            .select_related("customer", "yarn_count", "mill", "color_shade", "warehouse")
            .filter(company_id=company_id, status=1)
        )
        if yarn_type:
            qs = qs.filter(yarn_type=yarn_type)
        return qs.order_by("-invoice_date", "-id")


class YarnSalesReturnRepository:
    @staticmethod
    def get_by_id(return_id: int) -> Optional[parent_yarn_sales_return_table]:
        return (
            parent_yarn_sales_return_table.objects
            .select_related("company", "cfyear", "warehouse", "customer", "yarn_count", "mill", "color_shade", "sales_invoice")
            .prefetch_related("line_items")
            .filter(id=return_id, status=1)
            .first()
        )

    @staticmethod
    def list_by_company(company_id: int, yarn_type: Optional[str] = None) -> QuerySet[parent_yarn_sales_return_table]:
        qs = (
            parent_yarn_sales_return_table.objects
            .select_related("customer", "yarn_count", "mill", "color_shade", "warehouse", "sales_invoice")
            .filter(company_id=company_id, status=1)
        )
        if yarn_type:
            qs = qs.filter(yarn_type=yarn_type)
        return qs.order_by("-return_date", "-id")
