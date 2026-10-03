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
        if not stock or stock.balance_quantity < quantity or (bag > 0 and stock.balance_bag < bag):
            avail = stock.balance_quantity if stock else Decimal("0.000")
            avail_bag = stock.balance_bag if stock else 0
            raise ValidationError(
                f"Insufficient stock for {yarn_type} Yarn (Count ID: {yarn_count_id}, Lot: {lot_no}). "
                f"Available: {avail} Kg ({avail_bag} bags), Requested: {quantity} Kg ({bag} bags)."
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
        if not stock or stock.balance_quantity < quantity or (bag > 0 and stock.balance_bag < bag):
            avail = stock.balance_quantity if stock else Decimal("0.000")
            avail_bag = stock.balance_bag if stock else 0
            raise ValidationError(
                f"Insufficient stock to complete Yarn Sales. "
                f"Available: {avail} Kg ({avail_bag} bags), Requested: {quantity} Kg ({bag} bags)."
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

    @classmethod
    @transaction.atomic
    def reverse_inward_stock(
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
        if not stock or stock.balance_quantity < quantity or (bag > 0 and stock.balance_bag < bag):
            avail = stock.balance_quantity if stock else Decimal("0.000")
            raise ValidationError(
                f"Cannot reverse Inward: stock has already been consumed. Available: {avail} Kg, Needed: {quantity} Kg."
            )
        stock.inward_bag = max(0, stock.inward_bag - bag)
        stock.inward_quantity = max(Decimal("0.000"), stock.inward_quantity - quantity)
        stock.recalculate_balance()
        stock.save()
        return stock

    @classmethod
    @transaction.atomic
    def reverse_outward_stock(
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
        stock.outward_bag = max(0, stock.outward_bag - bag)
        stock.outward_quantity = max(Decimal("0.000"), stock.outward_quantity - quantity)
        stock.recalculate_balance()
        stock.save()
        return stock

    @classmethod
    @transaction.atomic
    def reverse_sales_stock(
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
        stock.sales_bag = max(0, stock.sales_bag - bag)
        stock.sales_quantity = max(Decimal("0.000"), stock.sales_quantity - quantity)
        stock.recalculate_balance()
        stock.save()
        return stock

    @classmethod
    @transaction.atomic
    def reverse_sales_return_stock(
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
        if not stock or stock.balance_quantity < quantity or (bag > 0 and stock.balance_bag < bag):
            avail = stock.balance_quantity if stock else Decimal("0.000")
            raise ValidationError(
                f"Cannot reverse Sales Return: stock has already been consumed. Available: {avail} Kg, Needed: {quantity} Kg."
            )
        stock.sales_return_bag = max(0, stock.sales_return_bag - bag)
        stock.sales_return_quantity = max(Decimal("0.000"), stock.sales_return_quantity - quantity)
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
        outward_id = data.get("outward_id") or data.get("outward")
        po = None
        outward = None

        inward_source = data.get("inward_source")
        if outward_id:
            inward_source = "DYEING_RETURN"
            outward = parent_yarn_outward_table.objects.select_for_update().filter(id=outward_id, company_id=company_id).first()
            if not outward:
                raise ResourceNotFound(f"Yarn Outward #{outward_id} not found.")
            if outward.outward_type != YarnOutwardTypes.DYEING:
                raise ValidationError("Only 'Yarn Outward for Dyeing' can be received as Dyed Yarn Inward.")
            if outward.is_complete == 1:
                raise ValidationError(f"Outward #{outward.outward_number} is already fully received and completed.")
        elif po_id:
            inward_source = "PURCHASE_PO"
            po = parent_po_table.objects.select_for_update().filter(id=po_id, company_id=company_id).first()
            if not po:
                raise ResourceNotFound(f"Yarn Purchase Order #{po_id} not found.")
            if po.is_authorized != 1:
                raise ValidationError(f"Purchase Order #{po.po_number} is not authorized. Only authorized POs can be received.")
        else:
            inward_source = inward_source or "PURCHASE_PO"

        # Yarn type & Color Shade determination
        if inward_source == "DYEING_RETURN":
            yarn_type = YarnCategory.DYED  # Dyed yarn returned from processor
            color_shade_id = data.get("color_shade_id") or outward.color_shade_id
            if not color_shade_id:
                raise ValidationError("Color shade is required when receiving dyed yarn from dyeing.")
            yarn_count_id = data.get("yarn_count_id") or outward.yarn_count_id
            mill_id = data.get("mill_id") or outward.mill_id
            party_id = data.get("party_id") or outward.destination_party_id
        else:
            yarn_type = data.get("yarn_type") or (po.yarn_type if po else YarnCategory.GREY)
            color_shade_id = data.get("color_shade_id") or (po.color_shade_id if po else None)
            if yarn_type == YarnCategory.DYED and not color_shade_id:
                raise ValidationError("Color shade is required for Dyed Yarn Inward.")
            yarn_count_id = data.get("yarn_count_id") or (po.yarn_count_id if po else None)
            mill_id = data.get("mill_id") or (po.mill_id if po else None)
            party_id = data.get("party_id") or (po.party_id if po else None)

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

        # Resolve Financial Year
        cfyear_id = data.get("cfyear_id") or data.get("cfyear") or (po.cfyear_id if po else (outward.cfyear_id if outward else None))
        if not cfyear_id:
            comp_obj = Company.objects.filter(id=company_id).first()
            cf = comp_obj.current_financial_year if comp_obj else None
            cfyear_id = cf.id if cf else (FinancialYear.objects.filter(company_id=company_id).first().id if FinancialYear.objects.filter(company_id=company_id).exists() else None)

        # Process Loss calculation for dyeing return
        process_loss_wt = Decimal(str(data.get("process_loss_wt", "0.000")))
        dyeing_rate = Decimal(str(data.get("dyeing_rate", "0.00")))
        dyeing_charges = net_wt * dyeing_rate
        if inward_source == "DYEING_RETURN" and outward:
            if not process_loss_wt and (outward.remaining_quantity > net_wt):
                process_loss_wt = outward.remaining_quantity - net_wt
            loss_pct = (process_loss_wt / outward.quantity * Decimal("100.00")) if outward.quantity else Decimal("0.00")
        else:
            loss_pct = Decimal("0.00")

        inward = parent_yarn_inward_table.objects.create(
            inward_number=inward_number,
            inward_date=data.get("inward_date") or timezone.now().date(),
            dc_number=data.get("dc_number", ""),
            dc_date=data.get("dc_date") or timezone.now().date(),
            vehicle_no=data.get("vehicle_no", ""),
            yarn_type=yarn_type,
            inward_source=inward_source,
            po=po,
            outward=outward,
            company_id=company_id,
            cfyear_id=cfyear_id,
            party_id=party_id,
            mill_id=mill_id,
            warehouse_id=warehouse_id,
            yarn_count_id=yarn_count_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no,
            bag=bag,
            per_bag=per_bag,
            gross_wt=gross_wt,
            tare_wt=tare_wt,
            net_wt=net_wt,
            rate=rate,
            amount=amount,
            process_loss_wt=process_loss_wt,
            process_loss_percent=loss_pct,
            dyeing_rate=dyeing_rate,
            dyeing_charges=dyeing_charges,
            remarks=data.get("remarks", ""),
            is_authorized=1,
            status=1,
            created_by=user,
            updated_by=user,
        )

        # 1. Update Live Stock atomically (Dyed Yarn Stock gets credited!)
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

        # 2. Update PO Remaining Balances & Check Completion (for PO inward)
        if po:
            line_item = child_po_table.objects.filter(tm_po=po, yarn_count_id=inward.yarn_count_id).first()
            if line_item:
                line_item.remaining_bag = max(0, line_item.remaining_bag - bag)
                line_item.remaining_quantity = max(Decimal("0.000"), line_item.remaining_quantity - net_wt)
                line_item.remaining_amount = max(Decimal("0.000"), line_item.remaining_quantity * line_item.rate)
                line_item.save()

            YarnPOService.check_and_update_completion(po.id)

        # 3. Update Outward Process Tracking & Completion (for Dyeing return)
        if outward:
            outward.received_quantity += net_wt
            outward.remaining_quantity = max(Decimal("0.000"), outward.remaining_quantity - (net_wt + process_loss_wt))
            if outward.remaining_quantity <= Decimal("1.000"):
                outward.is_complete = 1
            outward.save()

        # 4. Create Line Items (Child Inward)
        if line_items_data:
            line_objs = [
                child_yarn_inward_table(
                    tm_inward=inward,
                    yarn_count_id=item.get("yarn_count_id") or inward.yarn_count_id,
                    color_shade_id=item.get("color_shade_id") or inward.color_shade_id,
                    lot_no=item.get("lot_no", lot_no),
                    bag=int(item.get("bag", 0)),
                    per_bag=Decimal(str(item.get("per_bag", per_bag))),
                    gross_wt=Decimal(str(item.get("gross_wt", "0.000"))),
                    tare_wt=Decimal(str(item.get("tare_wt", "0.000"))),
                    net_wt=Decimal(str(item.get("net_wt", "0.000"))),
                    rate=Decimal(str(item.get("rate", rate))),
                    amount=Decimal(str(item.get("amount", "0.000"))),
                    status=1
                )
                for item in line_items_data
            ]
            child_yarn_inward_table.objects.bulk_create(line_objs)
        elif inward.yarn_count_id and inward.net_wt:
            child_yarn_inward_table.objects.create(
                tm_inward=inward,
                yarn_count_id=inward.yarn_count_id,
                color_shade_id=inward.color_shade_id,
                lot_no=inward.lot_no,
                bag=inward.bag,
                per_bag=inward.per_bag,
                gross_wt=inward.gross_wt,
                tare_wt=inward.tare_wt,
                net_wt=inward.net_wt,
                rate=inward.rate,
                amount=inward.amount,
                status=1
            )

        return inward

    @classmethod
    @transaction.atomic
    def cancel_inward(cls, inward_id: int, company_id: int, user=None) -> parent_yarn_inward_table:
        """Atomically reverse inward stock, restore PO/outward balances, and soft delete."""
        inward = parent_yarn_inward_table.objects.select_for_update().filter(id=inward_id, company_id=company_id, status=1).first()
        if not inward:
            raise ResourceNotFound(f"Yarn Inward with ID {inward_id} not found.")

        # 1. Reverse live stock
        YarnStockService.reverse_inward_stock(
            company_id=company_id,
            warehouse_id=inward.warehouse_id,
            yarn_type=inward.yarn_type,
            yarn_count_id=inward.yarn_count_id,
            mill_id=inward.mill_id,
            color_shade_id=inward.color_shade_id,
            lot_no=inward.lot_no,
            bag=inward.bag,
            quantity=inward.net_wt
        )

        # 2. Restore PO balances if applicable
        if inward.po:
            line_item = child_po_table.objects.filter(tm_po=inward.po, yarn_count_id=inward.yarn_count_id).first()
            if line_item:
                line_item.remaining_bag += inward.bag
                line_item.remaining_quantity += inward.net_wt
                line_item.remaining_amount = line_item.remaining_quantity * line_item.rate
                line_item.save()
            inward.po.is_complete = 0
            inward.po.save(update_fields=["is_complete", "updated_on"])

        # 3. Restore Outward balance if dyeing return
        if inward.outward:
            inward.outward.received_quantity = max(Decimal("0.000"), inward.outward.received_quantity - inward.net_wt)
            inward.outward.remaining_quantity += (inward.net_wt + inward.process_loss_wt)
            inward.outward.is_complete = 0
            inward.outward.save()

        # 4. Soft delete
        inward.soft_delete(user=user)
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

        # 3. Create Child Line Items
        if line_items_data:
            line_objs = [
                child_yarn_outward_table(
                    tm_outward=outward,
                    yarn_count_id=item.get("yarn_count_id") or outward.yarn_count_id,
                    color_shade_id=item.get("color_shade_id") or outward.color_shade_id,
                    mill_id=item.get("mill_id") or outward.mill_id,
                    lot_no=item.get("lot_no", lot_no),
                    bag=int(item.get("bag", 0)),
                    quantity=Decimal(str(item.get("quantity", "0.000"))),
                    remarks=item.get("remarks", ""),
                    status=1
                )
                for item in line_items_data
            ]
            child_yarn_outward_table.objects.bulk_create(line_objs)
        elif outward.yarn_count_id and outward.quantity:
            child_yarn_outward_table.objects.create(
                tm_outward=outward,
                yarn_count_id=outward.yarn_count_id,
                color_shade_id=outward.color_shade_id,
                mill_id=outward.mill_id,
                lot_no=outward.lot_no,
                bag=outward.bag,
                quantity=outward.quantity,
                remarks=outward.remarks,
                status=1
            )

        return outward

    @classmethod
    @transaction.atomic
    def cancel_outward(cls, outward_id: int, company_id: int, user=None) -> parent_yarn_outward_table:
        """Atomically reverse outward stock and soft delete outward dispatch."""
        outward = parent_yarn_outward_table.objects.select_for_update().filter(id=outward_id, company_id=company_id, status=1).first()
        if not outward:
            raise ResourceNotFound(f"Yarn Outward with ID {outward_id} not found.")

        if outward.received_quantity > 0:
            raise ValidationError("Cannot cancel outward dispatch that already has incoming receipts.")

        # Reverse live stock
        YarnStockService.reverse_outward_stock(
            company_id=company_id,
            warehouse_id=outward.warehouse_id,
            yarn_type=outward.yarn_type,
            yarn_count_id=outward.yarn_count_id,
            mill_id=outward.mill_id,
            color_shade_id=outward.color_shade_id,
            lot_no=outward.lot_no,
            bag=outward.bag,
            quantity=outward.quantity
        )

        outward.soft_delete(user=user)
        return outward

