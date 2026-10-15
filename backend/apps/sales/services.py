from __future__ import annotations
from decimal import Decimal
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from core.base_services import BaseService
from core.exceptions import ValidationError, ResourceNotFound
from core.constants import YarnCategory
from apps.authentication.models import Company, FinancialYear
from apps.masters.models import PartyMaster, TaxMaster
from apps.sales.models import (
    parent_yarn_sales_table, child_yarn_sales_table,
    parent_yarn_sales_return_table, child_yarn_sales_return_table
)
from apps.inventory.services import YarnStockService
from core.utils.tax_engine import TaxEngine
from core.formats import FormatService


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

        # 2. Commercial calculations with Tax Engine
        customer_id = data.get("customer_id") or data.get("customer")
        customer = PartyMaster.objects.filter(id=customer_id).first() if customer_id else None
        rate = Decimal(str(data.get("rate", "0.00")))
        subtotal = quantity * rate

        # Resolve Tax Master
        tax_id = data.get("tax_id") or data.get("tax")
        tax_obj = None
        if tax_id:
            tax_obj = TaxMaster.objects.filter(id=tax_id, is_deleted=False).first()
        elif "tax_percent" not in data:
            tax_obj = TaxMaster.objects.filter(company_id=company_id, is_default=True, is_deleted=False).first()
            if not tax_obj:
                tax_obj = TaxMaster.objects.filter(company_id=company_id, tax_code="GST_5", is_deleted=False).first()

        comp_obj = Company.objects.filter(id=company_id).first()
        tax_res = TaxEngine.compute(
            subtotal=subtotal,
            tax=tax_obj,
            tax_percent=Decimal(str(data.get("tax_percent", "5.00"))) if ("tax_percent" in data and not tax_obj) else None,
            company=comp_obj,
            party=customer,
            place_of_supply=data.get("place_of_supply")
        )

        tax_percent = tax_res["tax_percent"]
        tax_amount = tax_res["tax_amount"]
        cgst_percent = tax_res["cgst_percent"]
        cgst_amount = tax_res["cgst_amount"]
        sgst_percent = tax_res["sgst_percent"]
        sgst_amount = tax_res["sgst_amount"]
        igst_percent = tax_res["igst_percent"]
        igst_amount = tax_res["igst_amount"]
        total_amount = tax_res["total_amount"]

        invoice_number = data.get("invoice_number") or cls.generate_invoice_number(company_id)
        cfyear_id = data.get("cfyear_id") or data.get("cfyear")
        if not cfyear_id:
            cf = comp_obj.current_financial_year if comp_obj else None
            cfyear_id = cf.id if cf else (FinancialYear.objects.filter(company_id=company_id).first().id if FinancialYear.objects.filter(company_id=company_id).exists() else None)

        sales = parent_yarn_sales_table.objects.create(
            invoice_number=invoice_number,
            invoice_date=FormatService.parse_date(data.get("invoice_date")) or timezone.now().date(),
            yarn_type=yarn_type,
            company_id=company_id,
            cfyear_id=cfyear_id,
            warehouse_id=warehouse_id,
            customer_id=customer_id,
            yarn_count_id=yarn_count_id,
            mill_id=mill_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no,
            bag=bag,
            per_bag=per_bag,
            quantity=quantity,
            rate=rate,
            subtotal=subtotal,
            tax=tax_obj,
            tax_percent=tax_percent,
            tax_amount=tax_amount,
            cgst_percent=cgst_percent,
            cgst_amount=cgst_amount,
            sgst_percent=sgst_percent,
            sgst_amount=sgst_amount,
            igst_percent=igst_percent,
            igst_amount=igst_amount,
            total_amount=total_amount,
            payment_terms=data.get("payment_terms", ""),
            remarks=data.get("remarks", ""),
            is_authorized=1,
            status=1,
            created_by=user,
            updated_by=user,
        )

        # 3. Create Child Line Items
        if line_items_data:
            line_objs = [
                child_yarn_sales_table(
                    tm_sales=sales,
                    yarn_count_id=item.get("yarn_count_id") or sales.yarn_count_id,
                    color_shade_id=item.get("color_shade_id") or sales.color_shade_id,
                    mill_id=item.get("mill_id") or sales.mill_id,
                    lot_no=item.get("lot_no", lot_no),
                    bag=int(item.get("bag", 0)),
                    per_bag=Decimal(str(item.get("per_bag", per_bag))),
                    quantity=Decimal(str(item.get("quantity", "0.000"))),
                    rate=Decimal(str(item.get("rate", rate))),
                    amount=Decimal(str(item.get("amount", "0.000"))),
                    status=1
                )
                for item in line_items_data
            ]
            child_yarn_sales_table.objects.bulk_create(line_objs)
        elif sales.yarn_count_id and sales.quantity:
            child_yarn_sales_table.objects.create(
                tm_sales=sales,
                yarn_count_id=sales.yarn_count_id,
                color_shade_id=sales.color_shade_id,
                mill_id=sales.mill_id,
                lot_no=sales.lot_no,
                bag=sales.bag,
                per_bag=sales.per_bag,
                quantity=sales.quantity,
                rate=sales.rate,
                amount=sales.subtotal,
                status=1
            )

        # 4. Maintain Financial Party Ledger
        try:
            from apps.ledger.services import CurrencyLedgerService
            CurrencyLedgerService.post_sales_invoice_voucher(sales, user=user)
        except Exception:
            pass

        # 5. Maintain Physical Stock Ledger with Customer Party
        try:
            from apps.ledger.services import StockLedgerService
            from core.constants import StockMovementTypes
            StockLedgerService.record_movement(
                company_id=company_id,
                fy_id=cfyear_id or 1,
                movement_date=sales.invoice_date,
                stage="YARN",
                warehouse_id=warehouse_id,
                movement_type=StockMovementTypes.SALES,
                doc_type="SALES_INVOICE",
                doc_number=sales.invoice_number,
                item_name=f"{sales.yarn_type} Yarn",
                lot_or_batch_no=lot_no or "GEN",
                out_units=bag,
                out_qty=quantity,
                unit_rate=rate,
                party_id=sales.customer_id,
                remarks=f"Commercial Sales to Customer #{sales.customer_id}",
                check_balance=False,
                user=user,
            )
        except Exception:
            pass

        return sales

    @classmethod
    @transaction.atomic
    def cancel_sales(cls, sales_id: int, company_id: int, user=None) -> parent_yarn_sales_table:
        """Atomically reverse sold stock and soft delete invoice."""
        sales = parent_yarn_sales_table.objects.select_for_update().filter(id=sales_id, company_id=company_id, status=1).first()
        if not sales:
            raise ResourceNotFound(f"Yarn Sales Invoice #{sales_id} not found.")

        # Check if sales returns exist against this invoice
        if sales.returns.filter(status=1).exists():
            raise ValidationError("Cannot cancel invoice because active sales return records exist against it.")

        # Reverse financial voucher if posted
        try:
            from apps.ledger.models import tl_voucher
            from apps.ledger.services import CurrencyLedgerService
            v = tl_voucher.objects.filter(
                company_id=company_id,
                reference_type="SALES_INVOICE",
                reference_no=sales.invoice_number,
                is_posted=True,
                is_reversed=False,
            ).first()
            if v:
                CurrencyLedgerService.reverse_voucher(
                    voucher_id=v.id,
                    company_id=company_id,
                    reversal_date=timezone.now().date(),
                    user=user,
                )
        except Exception:
            pass

        # Reverse live stock
        YarnStockService.reverse_sales_stock(
            company_id=company_id,
            warehouse_id=sales.warehouse_id,
            yarn_type=sales.yarn_type,
            yarn_count_id=sales.yarn_count_id,
            mill_id=sales.mill_id,
            color_shade_id=sales.color_shade_id,
            lot_no=sales.lot_no,
            bag=sales.bag,
            quantity=sales.quantity
        )

        sales.soft_delete(user=user)
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

        sales_invoice_id = data.get("sales_invoice_id") or data.get("sales_invoice")
        parent_invoice = parent_yarn_sales_table.objects.filter(id=sales_invoice_id).first() if sales_invoice_id else None

        subtotal = quantity * rate
        amount = subtotal

        # Resolve Tax Master (inherit from sales invoice if linked)
        tax_id = data.get("tax_id") or data.get("tax") or (parent_invoice.tax_id if parent_invoice else None)
        tax_obj = None
        if tax_id:
            tax_obj = TaxMaster.objects.filter(id=tax_id, is_deleted=False).first()
        elif parent_invoice and parent_invoice.tax:
            tax_obj = parent_invoice.tax
        elif "tax_percent" not in data:
            tax_obj = TaxMaster.objects.filter(company_id=company_id, is_default=True, is_deleted=False).first()
            if not tax_obj:
                tax_obj = TaxMaster.objects.filter(company_id=company_id, tax_code="GST_5", is_deleted=False).first()

        customer_id = data.get("customer_id") or data.get("customer") or (parent_invoice.customer_id if parent_invoice else None)
        customer = PartyMaster.objects.filter(id=customer_id).first() if customer_id else None
        comp_obj = Company.objects.filter(id=company_id).first()

        tax_res = TaxEngine.compute(
            subtotal=subtotal,
            tax=tax_obj,
            tax_percent=Decimal(str(data.get("tax_percent", parent_invoice.tax_percent if parent_invoice else "5.00"))) if not tax_obj else None,
            company=comp_obj,
            party=customer,
            place_of_supply=data.get("place_of_supply")
        )

        tax_percent = tax_res["tax_percent"]
        tax_amount = tax_res["tax_amount"]
        cgst_percent = tax_res["cgst_percent"]
        cgst_amount = tax_res["cgst_amount"]
        sgst_percent = tax_res["sgst_percent"]
        sgst_amount = tax_res["sgst_amount"]
        igst_percent = tax_res["igst_percent"]
        igst_amount = tax_res["igst_amount"]
        total_amount = tax_res["total_amount"]

        sales_return = parent_yarn_sales_return_table.objects.create(
            return_number=return_number,
            return_date=data.get("return_date") or timezone.now().date(),
            sales_invoice_id=sales_invoice_id,
            company_id=company_id,
            cfyear_id=cfyear_id,
            warehouse_id=warehouse_id,
            customer_id=customer_id,
            yarn_type=yarn_type,
            yarn_count_id=yarn_count_id,
            mill_id=mill_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no,
            bag=bag,
            quantity=quantity,
            rate=rate,
            amount=amount,
            subtotal=subtotal,
            tax=tax_obj,
            tax_percent=tax_percent,
            tax_amount=tax_amount,
            cgst_percent=cgst_percent,
            cgst_amount=cgst_amount,
            sgst_percent=sgst_percent,
            sgst_amount=sgst_amount,
            igst_percent=igst_percent,
            igst_amount=igst_amount,
            total_amount=total_amount,
            return_reason=data.get("return_reason", "Customer Return"),
            is_authorized=1,
            status=1,
            created_by=user,
            updated_by=user,
        )

        # 2. Create Child Line Items
        if line_items_data:
            line_objs = [
                child_yarn_sales_return_table(
                    tm_sales_return=sales_return,
                    yarn_count_id=item.get("yarn_count_id") or sales_return.yarn_count_id,
                    color_shade_id=item.get("color_shade_id") or sales_return.color_shade_id,
                    mill_id=item.get("mill_id") or sales_return.mill_id,
                    lot_no=item.get("lot_no", lot_no),
                    bag=int(item.get("bag", 0)),
                    quantity=Decimal(str(item.get("quantity", "0.000"))),
                    rate=Decimal(str(item.get("rate", rate))),
                    amount=Decimal(str(item.get("amount", "0.000"))),
                    status=1
                )
                for item in line_items_data
            ]
            child_yarn_sales_return_table.objects.bulk_create(line_objs)
        elif sales_return.yarn_count_id and sales_return.quantity:
            child_yarn_sales_return_table.objects.create(
                tm_sales_return=sales_return,
                yarn_count_id=sales_return.yarn_count_id,
                color_shade_id=sales_return.color_shade_id,
                mill_id=sales_return.mill_id,
                lot_no=sales_return.lot_no,
                bag=sales_return.bag,
                quantity=sales_return.quantity,
                rate=sales_return.rate,
                amount=sales_return.amount,
                status=1
            )

        # 3. Maintain Physical Stock Ledger with Customer Party
        try:
            from apps.ledger.services import StockLedgerService
            from core.constants import StockMovementTypes
            StockLedgerService.record_movement(
                company_id=company_id,
                fy_id=cfyear_id or 1,
                movement_date=sales_return.return_date,
                stage="YARN",
                warehouse_id=warehouse_id,
                movement_type=StockMovementTypes.SALES_RETURN,
                doc_type="SALES_RETURN",
                doc_number=sales_return.return_number,
                item_name=f"{sales_return.yarn_type} Yarn",
                lot_or_batch_no=lot_no or "GEN",
                in_units=bag,
                in_qty=quantity,
                unit_rate=rate,
                party_id=sales_return.customer_id,
                remarks=f"Customer Sales Return from Customer #{sales_return.customer_id}",
                check_balance=False,
                user=user,
            )
        except Exception:
            pass

        # 4. Maintain Financial Party Ledger (Customer Credit Note)
        try:
            from apps.ledger.services import CurrencyLedgerService
            CurrencyLedgerService.post_sales_return_voucher(sales_return, user=user)
        except Exception:
            pass

        return sales_return

    @classmethod
    @transaction.atomic
    def cancel_sales_return(cls, return_id: int, company_id: int, user=None) -> parent_yarn_sales_return_table:
        """Atomically reverse returned stock, reverse credit note voucher, and soft delete return."""
        sales_return = parent_yarn_sales_return_table.objects.select_for_update().filter(id=return_id, company_id=company_id, status=1).first()
        if not sales_return:
            raise ResourceNotFound(f"Yarn Sales Return #{return_id} not found.")

        # Reverse live stock
        YarnStockService.reverse_sales_return_stock(
            company_id=company_id,
            warehouse_id=sales_return.warehouse_id,
            yarn_type=sales_return.yarn_type,
            yarn_count_id=sales_return.yarn_count_id,
            mill_id=sales_return.mill_id,
            color_shade_id=sales_return.color_shade_id,
            lot_no=sales_return.lot_no,
            bag=sales_return.bag,
            quantity=sales_return.quantity
        )

        # Reverse financial voucher if posted
        try:
            from apps.ledger.models import tl_voucher
            from apps.ledger.services import CurrencyLedgerService
            v = tl_voucher.objects.filter(
                company_id=company_id,
                reference_type="SALES_RETURN",
                reference_id=sales_return.id,
                is_posted=True,
                is_reversed=False,
            ).first()
            if v:
                CurrencyLedgerService.reverse_voucher(
                    voucher_id=v.id,
                    reversal_date=timezone.now().date(),
                    user=user,
                )
        except Exception:
            pass

        sales_return.soft_delete(user=user)
        return sales_return

