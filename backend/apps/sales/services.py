from __future__ import annotations
from decimal import Decimal
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from core.base_services import BaseService
from core.exceptions import ValidationError, ResourceNotFound
from core.constants import YarnCategory
from apps.authentication.models import Company, FinancialYear
from apps.sales.models import (
    parent_yarn_sales_table, child_yarn_sales_table,
    parent_yarn_sales_return_table, child_yarn_sales_return_table
)
from apps.inventory.services import YarnStockService


class YarnSalesService(BaseService):
    """
    Handles Yarn Sales orders & invoices:
    Decrements live stock atomically and records commercial receivables.
    """

    @staticmethod
    def generate_invoice_number(company_id: int) -> str:
        now = timezone.now()
        prefix = f"YSAL-{now.strftime('%Y%m')}-"
        last = (
            parent_yarn_sales_table.objects
            .filter(company_id=company_id, invoice_number__startswith=prefix)
            .order_by("-invoice_number")
            .first()
        )
        seq = (int(last.invoice_number.split("-")[-1]) + 1) if last else 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def create_sales(
        cls,
        company_id: int,
        data: Dict[str, Any],
        line_items_data: Optional[List[Dict[str, Any]]] = None,
        user=None
    ) -> parent_yarn_sales_table:
        yarn_type = data.get("yarn_type", YarnCategory.GREY)
        color_shade_id = data.get("color_shade_id")
        if yarn_type == YarnCategory.DYED and not color_shade_id:
            raise ValidationError("Color shade is required for Dyed Yarn Sales.")

        bag = int(data.get("bag", 0))
        per_bag = Decimal(str(data.get("per_bag", "45.360")))
        quantity = Decimal(str(data.get("quantity") or (Decimal(str(bag)) * per_bag)))
        lot_no = data.get("lot_no", "GEN")
        warehouse_id = data.get("warehouse_id") or data.get("warehouse")
        yarn_count_id = data.get("yarn_count_id") or data.get("yarn_count")
        mill_id = data.get("mill_id") or data.get("mill")

        # 1. Deduct Stock Atomically (Checks availability)
        YarnStockService.deduct_sales_stock(
            company_id=company_id,
            warehouse_id=warehouse_id,
            yarn_type=yarn_type,
            yarn_count_id=yarn_count_id,
            mill_id=mill_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no,
            bag=bag,
            quantity=quantity
        )

        # 2. Commercial calculations
        rate = Decimal(str(data.get("rate", "0.00")))
        subtotal = quantity * rate
        tax_percent = Decimal(str(data.get("tax_percent", "5.00")))
        tax_amount = subtotal * (tax_percent / Decimal("100.00"))
        total_amount = subtotal + tax_amount

        invoice_number = data.get("invoice_number") or cls.generate_invoice_number(company_id)
        cfyear_id = data.get("cfyear_id") or data.get("cfyear")
        if not cfyear_id:
            comp_obj = Company.objects.filter(id=company_id).first()
            cf = comp_obj.current_financial_year if comp_obj else None
            cfyear_id = cf.id if cf else (FinancialYear.objects.filter(company_id=company_id).first().id if FinancialYear.objects.filter(company_id=company_id).exists() else None)

        sales = parent_yarn_sales_table.objects.create(
            invoice_number=invoice_number,
            invoice_date=data.get("invoice_date") or timezone.now().date(),
            yarn_type=yarn_type,
            company_id=company_id,
            cfyear_id=cfyear_id,
            warehouse_id=warehouse_id,
            customer_id=data.get("customer_id") or data.get("customer"),
            yarn_count_id=yarn_count_id,
            mill_id=mill_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no,
            bag=bag,
            per_bag=per_bag,
            quantity=quantity,
            rate=rate,
            subtotal=subtotal,
            tax_percent=tax_percent,
            tax_amount=tax_amount,
            total_amount=total_amount,
            payment_terms=data.get("payment_terms", ""),
            remarks=data.get("remarks", ""),
            is_authorized=1,
            status=1,
            created_by=user,
            updated_by=user,
        )

        return sales


class YarnSalesReturnService(BaseService):
    """
    Handles Yarn Sales Return:
    Re-adds customer returned yarn into live stock atomically.
    """

    @staticmethod
    def generate_return_number(company_id: int) -> str:
        now = timezone.now()
        prefix = f"YSRET-{now.strftime('%Y%m')}-"
        last = (
            parent_yarn_sales_return_table.objects
            .filter(company_id=company_id, return_number__startswith=prefix)
            .order_by("-return_number")
            .first()
        )
        seq = (int(last.return_number.split("-")[-1]) + 1) if last else 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def create_sales_return(
        cls,
        company_id: int,
        data: Dict[str, Any],
        line_items_data: Optional[List[Dict[str, Any]]] = None,
        user=None
    ) -> parent_yarn_sales_return_table:
        yarn_type = data.get("yarn_type", YarnCategory.GREY)
        color_shade_id = data.get("color_shade_id")
        bag = int(data.get("bag", 0))
        quantity = Decimal(str(data.get("quantity", "0.000")))
        rate = Decimal(str(data.get("rate", "0.00")))
        amount = quantity * rate
        lot_no = data.get("lot_no", "GEN")
        warehouse_id = data.get("warehouse_id") or data.get("warehouse")
        yarn_count_id = data.get("yarn_count_id") or data.get("yarn_count")
        mill_id = data.get("mill_id") or data.get("mill")

        # 1. Add back into Live Stock atomically
        YarnStockService.add_sales_return_stock(
            company_id=company_id,
            warehouse_id=warehouse_id,
            yarn_type=yarn_type,
            yarn_count_id=yarn_count_id,
            mill_id=mill_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no,
            bag=bag,
            quantity=quantity
        )

        return_number = data.get("return_number") or cls.generate_return_number(company_id)
        cfyear_id = data.get("cfyear_id") or data.get("cfyear")
        if not cfyear_id:
            comp_obj = Company.objects.filter(id=company_id).first()
            cf = comp_obj.current_financial_year if comp_obj else None
            cfyear_id = cf.id if cf else (FinancialYear.objects.filter(company_id=company_id).first().id if FinancialYear.objects.filter(company_id=company_id).exists() else None)

        sales_return = parent_yarn_sales_return_table.objects.create(
            return_number=return_number,
            return_date=data.get("return_date") or timezone.now().date(),
            sales_invoice_id=data.get("sales_invoice_id") or data.get("sales_invoice"),
            company_id=company_id,
            cfyear_id=cfyear_id,
            warehouse_id=warehouse_id,
            customer_id=data.get("customer_id") or data.get("customer"),
            yarn_type=yarn_type,
            yarn_count_id=yarn_count_id,
            mill_id=mill_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no,
            bag=bag,
            quantity=quantity,
            rate=rate,
            amount=amount,
            return_reason=data.get("return_reason", "Customer Return"),
            is_authorized=1,
            status=1,
            created_by=user,
            updated_by=user,
        )

        return sales_return
