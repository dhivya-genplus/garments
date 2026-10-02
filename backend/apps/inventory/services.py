from __future__ import annotations
from decimal import Decimal
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from core.base_services import BaseService
from core.exceptions import ValidationError, ResourceNotFound, ConflictError
from core.constants import YarnCategory, YarnOutwardTypes
from apps.inventory.models import (
    yarn_stock_table, parent_yarn_inward_table, child_yarn_inward_table,
    parent_yarn_outward_table, child_yarn_outward_table
)
from apps.authentication.models import Company, FinancialYear
from apps.purchase.models import parent_po_table, child_po_table
from apps.purchase.services import YarnPOService


class YarnStockService(BaseService):
    """
    Central stock management service for Grey and Dyed yarn.
    Guarantees atomic inventory writes with row-level locks (select_for_update).
    """

    @classmethod
    @transaction.atomic
    def add_inward_stock(
        cls,
        company_id: int,
        warehouse_id: int,
        yarn_type: str,
        yarn_count_id: int,
        mill_id: int,
        color_shade_id: Optional[int],
        lot_no: str,
        bag: int,
        quantity: Decimal
    ) -> yarn_stock_table:
        stock, _ = yarn_stock_table.objects.select_for_update().get_or_create(
            company_id=company_id,
            warehouse_id=warehouse_id,
            yarn_type=yarn_type,
            yarn_count_id=yarn_count_id,
            mill_id=mill_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no or "GEN"
        )
        stock.inward_bag += bag
        stock.inward_quantity += quantity
        stock.recalculate_balance()
        stock.save()
        return stock

    @classmethod
    @transaction.atomic
    def deduct_outward_stock(
        cls,
        company_id: int,
        warehouse_id: int,
        yarn_type: str,
        yarn_count_id: int,
        mill_id: int,
        color_shade_id: Optional[int],
        lot_no: str,
        bag: int,
        quantity: Decimal
    ) -> yarn_stock_table:
        stock = (
            yarn_stock_table.objects
            .select_for_update()
            .filter(
                company_id=company_id,
                warehouse_id=warehouse_id,
                yarn_type=yarn_type,
                yarn_count_id=yarn_count_id,
                mill_id=mill_id,
                color_shade_id=color_shade_id,
                lot_no=lot_no or "GEN"
            )
            .first()
        )
        if not stock or stock.balance_quantity < quantity:
            avail = stock.balance_quantity if stock else Decimal("0.000")
            raise ValidationError(
                f"Insufficient stock for {yarn_type} Yarn (Count ID: {yarn_count_id}, Lot: {lot_no}). "
                f"Available: {avail} Kg, Requested: {quantity} Kg."
            )

        stock.outward_bag += bag
        stock.outward_quantity += quantity
        stock.recalculate_balance()
        stock.save()
        return stock

    @classmethod
    @transaction.atomic
    def deduct_sales_stock(
        cls,
        company_id: int,
        warehouse_id: int,
        yarn_type: str,
        yarn_count_id: int,
        mill_id: int,
        color_shade_id: Optional[int],
        lot_no: str,
        bag: int,
        quantity: Decimal
    ) -> yarn_stock_table:
        stock = (
            yarn_stock_table.objects
            .select_for_update()
            .filter(
                company_id=company_id,
                warehouse_id=warehouse_id,
                yarn_type=yarn_type,
                yarn_count_id=yarn_count_id,
                mill_id=mill_id,
                color_shade_id=color_shade_id,
                lot_no=lot_no or "GEN"
            )
            .first()
        )
        if not stock or stock.balance_quantity < quantity:
            avail = stock.balance_quantity if stock else Decimal("0.000")
            raise ValidationError(
                f"Insufficient stock to complete Yarn Sales. Available: {avail} Kg, Requested: {quantity} Kg."
            )

        stock.sales_bag += bag
        stock.sales_quantity += quantity
        stock.recalculate_balance()
        stock.save()
        return stock

    @classmethod
    @transaction.atomic
    def add_sales_return_stock(
        cls,
        company_id: int,
        warehouse_id: int,
        yarn_type: str,
        yarn_count_id: int,
        mill_id: int,
        color_shade_id: Optional[int],
        lot_no: str,
        bag: int,
        quantity: Decimal
    ) -> yarn_stock_table:
        stock, _ = yarn_stock_table.objects.select_for_update().get_or_create(
            company_id=company_id,
            warehouse_id=warehouse_id,
            yarn_type=yarn_type,
            yarn_count_id=yarn_count_id,
            mill_id=mill_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no or "GEN"
        )
        stock.sales_return_bag += bag
        stock.sales_return_quantity += quantity
        stock.recalculate_balance()
        stock.save()
        return stock


class YarnInwardService(BaseService):
    """Handles Yarn Inward GRN from PO, updating pending PO balances & live stock."""

    @staticmethod
    def generate_inward_number(company_id: int) -> str:
        now = timezone.now()
        prefix = f"YIN-{now.strftime('%Y%m')}-"
        last = (
            parent_yarn_inward_table.objects
            .filter(company_id=company_id, inward_number__startswith=prefix)
            .order_by("-inward_number")
            .first()
        )
        seq = (int(last.inward_number.split("-")[-1]) + 1) if last else 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def create_inward(
        cls,
        company_id: int,
        data: Dict[str, Any],
        line_items_data: Optional[List[Dict[str, Any]]] = None,
        user=None
    ) -> parent_yarn_inward_table:
        po_id = data.get("po_id") or data.get("po")
        po = None
        if po_id:
            po = parent_po_table.objects.select_for_update().filter(id=po_id, company_id=company_id).first()
            if not po:
                raise ResourceNotFound(f"Yarn Purchase Order #{po_id} not found.")
            if po.is_authorized != 1:
                raise ValidationError(f"Purchase Order #{po.po_number} is not authorized. Only authorized POs can be received.")

        yarn_type = data.get("yarn_type") or (po.yarn_type if po else YarnCategory.GREY)
        color_shade_id = data.get("color_shade_id") or (po.color_shade_id if po else None)
        if yarn_type == YarnCategory.DYED and not color_shade_id:
            raise ValidationError("Color shade is required for Dyed Yarn Inward.")

        inward_number = data.get("inward_number") or cls.generate_inward_number(company_id)
        bag = int(data.get("bag", 0))
        per_bag = Decimal(str(data.get("per_bag", "45.360")))
        gross_wt = Decimal(str(data.get("gross_wt", "0.000")))
        tare_wt = Decimal(str(data.get("tare_wt", "0.000")))
        net_wt = Decimal(str(data.get("net_wt", "0.000")))
        if not net_wt:
            net_wt = (gross_wt - tare_wt) if (gross_wt and tare_wt) else (Decimal(str(bag)) * per_bag)

        rate = Decimal(str(data.get("rate") or (po.net_rate if po else "0.00")))
        amount = net_wt * rate
        lot_no = data.get("lot_no", "GEN")
        warehouse_id = data.get("warehouse_id") or data.get("warehouse")

        inward = parent_yarn_inward_table.objects.create(
            inward_number=inward_number,
            inward_date=data.get("inward_date") or timezone.now().date(),
            dc_number=data.get("dc_number", ""),
            dc_date=data.get("dc_date") or timezone.now().date(),
            vehicle_no=data.get("vehicle_no", ""),
            yarn_type=yarn_type,
            po=po,
            company_id=company_id,
            cfyear_id=data.get("cfyear_id") or (po.cfyear_id if po else None),
            party_id=data.get("party_id") or (po.party_id if po else None),
            mill_id=data.get("mill_id") or (po.mill_id if po else None),
            warehouse_id=warehouse_id,
            yarn_count_id=data.get("yarn_count_id") or (po.yarn_count_id if po else None),
            color_shade_id=color_shade_id,
            lot_no=lot_no,
            bag=bag,
            per_bag=per_bag,
            gross_wt=gross_wt,
            tare_wt=tare_wt,
            net_wt=net_wt,
            rate=rate,
            amount=amount,
            remarks=data.get("remarks", ""),
            is_authorized=1,
            status=1,
            created_by=user,
            updated_by=user,
        )

        # 1. Update Live Stock atomically
        YarnStockService.add_inward_stock(
            company_id=company_id,
            warehouse_id=warehouse_id,
            yarn_type=yarn_type,
            yarn_count_id=inward.yarn_count_id,
            mill_id=inward.mill_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no,
            bag=bag,
            quantity=net_wt
        )

        # 2. Update PO Remaining Balances & Check Completion
        if po:
            line_item = child_po_table.objects.filter(tm_po=po, yarn_count_id=inward.yarn_count_id).first()
            if line_item:
                line_item.remaining_bag = max(0, line_item.remaining_bag - bag)
                line_item.remaining_quantity = max(Decimal("0.000"), line_item.remaining_quantity - net_wt)
                line_item.remaining_amount = max(Decimal("0.000"), line_item.remaining_quantity * line_item.rate)
                line_item.save()

            YarnPOService.check_and_update_completion(po.id)

        return inward


class YarnOutwardService(BaseService):
    """
    Handles Yarn Outward dispatch:
      - KNITTING (Outward for Knitting Program)
      - DYEING (Grey Yarn Outward for Dyeing)
      - PURCHASE_RETURN (Yarn Return to Mill/Trader)
    """

    @staticmethod
    def generate_outward_number(company_id: int, outward_type: str) -> str:
        now = timezone.now()
        prefix_code = "YKNT" if outward_type == YarnOutwardTypes.KNITTING else ("YDYE" if outward_type == YarnOutwardTypes.DYEING else "YRET")
        prefix = f"{prefix_code}-{now.strftime('%Y%m')}-"
        last = (
            parent_yarn_outward_table.objects
            .filter(company_id=company_id, outward_number__startswith=prefix)
            .order_by("-outward_number")
            .first()
        )
        seq = (int(last.outward_number.split("-")[-1]) + 1) if last else 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def create_outward(
        cls,
        company_id: int,
        data: Dict[str, Any],
        line_items_data: Optional[List[Dict[str, Any]]] = None,
        user=None
    ) -> parent_yarn_outward_table:
        outward_type = data.get("outward_type", YarnOutwardTypes.KNITTING)
        yarn_type = data.get("yarn_type", YarnCategory.GREY)
        color_shade_id = data.get("color_shade_id")
        bag = int(data.get("bag", 0))
        quantity = Decimal(str(data.get("quantity", "0.000")))
        lot_no = data.get("lot_no", "GEN")
        warehouse_id = data.get("warehouse_id") or data.get("warehouse")
        yarn_count_id = data.get("yarn_count_id") or data.get("yarn_count")
        mill_id = data.get("mill_id") or data.get("mill")

        # 1. Deduct Stock Atomically (Validates that stock >= quantity)
        YarnStockService.deduct_outward_stock(
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

        # 2. Create Outward Header
        outward_number = data.get("outward_number") or cls.generate_outward_number(company_id, outward_type)
        cfyear_id = data.get("cfyear_id") or data.get("cfyear")
        if not cfyear_id:
            comp_obj = Company.objects.filter(id=company_id).first()
            cf = comp_obj.current_financial_year if comp_obj else None
            cfyear_id = cf.id if cf else (FinancialYear.objects.filter(company_id=company_id).first().id if FinancialYear.objects.filter(company_id=company_id).exists() else None)

        outward = parent_yarn_outward_table.objects.create(
            outward_number=outward_number,
            outward_date=data.get("outward_date") or timezone.now().date(),
            outward_type=outward_type,
            company_id=company_id,
            cfyear_id=cfyear_id,
            warehouse_id=warehouse_id,
            destination_party_id=data.get("destination_party_id") or data.get("destination_party"),
            yarn_type=yarn_type,
            yarn_count_id=yarn_count_id,
            mill_id=mill_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no,
            bag=bag,
            quantity=quantity,
            vehicle_no=data.get("vehicle_no", ""),
            driver_name=data.get("driver_name", ""),
            remarks=data.get("remarks", ""),
            is_authorized=1,
            status=1,
            created_by=user,
            updated_by=user,
        )

        return outward
