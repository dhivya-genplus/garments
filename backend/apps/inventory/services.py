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
from apps.masters.models import PartyMaster, TaxMaster
from apps.purchase.models import parent_po_table, child_po_table
from apps.purchase.services import YarnPOService
from core.utils.tax_engine import TaxEngine


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

        # Yarn type & Color Shade determination & PO conflict check
        if inward_source == "DYEING_RETURN":
            yarn_type = YarnCategory.DYED  # Dyed yarn returned from processor
            color_shade_id = data.get("color_shade_id") or data.get("color_shade") or outward.color_shade_id
            if not color_shade_id:
                raise ValidationError("Color shade is required when receiving dyed yarn from dyeing.")
            blend_ratio = data.get("blend_ratio")
            ply_count = int(data.get("ply_count", 1) or 1)
            twists_per_inch = data.get("twists_per_inch")
            slub_pattern = data.get("slub_pattern")
            core_denier = data.get("core_denier")
            yarn_count_id = data.get("yarn_count_id") or data.get("yarn_count") or outward.yarn_count_id
            mill_id = data.get("mill_id") or data.get("mill") or outward.mill_id
            party_id = data.get("party_id") or data.get("party") or outward.destination_party_id
        elif po:
            passed_type = data.get("yarn_type")
            if passed_type and passed_type.upper() != po.yarn_type:
                raise ValidationError(
                    f"Yarn Inward type '{passed_type}' conflicts with PO #{po.po_number} type '{po.yarn_type}'."
                )
            yarn_type = po.yarn_type
            color_shade_id = data.get("color_shade_id") or data.get("color_shade") or po.color_shade_id
            blend_ratio = data.get("blend_ratio") or po.blend_ratio
            ply_count = int(data.get("ply_count") or (po.ply_count or 1))
            twists_per_inch = data.get("twists_per_inch") or po.twists_per_inch
            slub_pattern = data.get("slub_pattern") or po.slub_pattern
            core_denier = data.get("core_denier") or po.core_denier
            yarn_count_id = data.get("yarn_count_id") or data.get("yarn_count") or po.yarn_count_id
            mill_id = data.get("mill_id") or data.get("mill") or po.mill_id
            party_id = data.get("party_id") or data.get("party") or po.party_id
        else:
            yarn_type = data.get("yarn_type") or YarnCategory.GREY
            color_shade_id = data.get("color_shade_id") or data.get("color_shade")
            blend_ratio = data.get("blend_ratio")
            ply_count = int(data.get("ply_count", 1) or 1)
            twists_per_inch = data.get("twists_per_inch")
            slub_pattern = data.get("slub_pattern")
            core_denier = data.get("core_denier")
            yarn_count_id = data.get("yarn_count_id") or data.get("yarn_count")
            mill_id = data.get("mill_id") or data.get("mill")
            party_id = data.get("party_id") or data.get("party")

        # Type-specific conditional validations
        if yarn_type in [YarnCategory.DYED, YarnCategory.MELANGE] and not color_shade_id:
            raise ValidationError(f"Color shade is required for {yarn_type} Yarn Inward.")

        if yarn_type == YarnCategory.MELANGE and not blend_ratio:
            raise ValidationError("Melange shade ratio / fiber blend percentage (e.g. 85/15) is required for Melange Yarn Inward.")

        if yarn_type in [YarnCategory.BLENDED, YarnCategory.RECYCLED] and not blend_ratio:
            raise ValidationError(f"Fiber blend ratio (e.g. 65/35 PC) is required for {yarn_type} Yarn Inward.")

        if yarn_type == YarnCategory.WOUND and ply_count < 1:
            raise ValidationError("Ply count must be at least 1 for Wound / Twisted Yarn.")

        inward_number = data.get("inward_number") or cls.generate_inward_number(company_id)
        bag = int(data.get("bag", 0))
        per_bag = Decimal(str(data.get("per_bag", "45.360")))
        gross_wt = Decimal(str(data.get("gross_wt", "0.000")))
        tare_wt = Decimal(str(data.get("tare_wt", "0.000")))
        net_wt = Decimal(str(data.get("net_wt", "0.000")))
        if not net_wt:
            net_wt = (gross_wt - tare_wt) if (gross_wt and tare_wt) else (Decimal(str(bag)) * per_bag)

        rate = Decimal(str(data.get("rate") or (po.net_rate if po else "0.00")))
        subtotal = net_wt * rate
        amount = subtotal
        lot_no = data.get("lot_no", "GEN")
        warehouse_id = data.get("warehouse_id") or data.get("warehouse")

        # Resolve Financial Year
        comp_obj = Company.objects.filter(id=company_id).first()
        cfyear_id = data.get("cfyear_id") or data.get("cfyear") or (po.cfyear_id if po else (outward.cfyear_id if outward else None))
        if not cfyear_id:
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

        # Resolve Tax Master and Calculate GST Breakdown
        tax_id = data.get("tax_id") or data.get("tax")
        tax_obj = None
        if tax_id:
            tax_obj = TaxMaster.objects.filter(id=tax_id, is_deleted=False).first()
        elif "tax_percent" not in data:
            tax_obj = TaxMaster.objects.filter(company_id=company_id, is_default=True, is_deleted=False).first()

        supplier_party = PartyMaster.objects.filter(id=party_id).first() if party_id else None
        tax_res = TaxEngine.compute(
            subtotal=subtotal,
            tax=tax_obj,
            tax_percent=Decimal(str(data.get("tax_percent"))) if ("tax_percent" in data and not tax_obj) else None,
            company=comp_obj,
            party=supplier_party,
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
        total_amount = subtotal + tax_amount + dyeing_charges

        inward = parent_yarn_inward_table.objects.create(
            inward_number=inward_number,
            inward_date=data.get("inward_date") or timezone.now().date(),
            dc_number=data.get("dc_number", ""),
            dc_date=data.get("dc_date") or timezone.now().date(),
            vehicle_no=data.get("vehicle_no", ""),
            yarn_type=yarn_type,
            blend_ratio=blend_ratio,
            ply_count=ply_count,
            twists_per_inch=twists_per_inch,
            slub_pattern=slub_pattern,
            core_denier=core_denier,
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

        # 1. Update Live Stock atomically (stock is isolated by yarn_type!)
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
            po_lines_qs = child_po_table.objects.filter(tm_po=po)
            if inward.yarn_count_id:
                po_lines_qs = po_lines_qs.filter(yarn_count_id=inward.yarn_count_id)
            if inward.color_shade_id:
                shade_match = po_lines_qs.filter(color_shade_id=inward.color_shade_id).first()
                line_item = shade_match or po_lines_qs.first()
            else:
                line_item = po_lines_qs.first()

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
                    blend_ratio=item.get("blend_ratio") or inward.blend_ratio,
                    ply_count=int(item.get("ply_count") or inward.ply_count),
                    twists_per_inch=item.get("twists_per_inch") or inward.twists_per_inch,
                    slub_pattern=item.get("slub_pattern") or inward.slub_pattern,
                    core_denier=item.get("core_denier") or inward.core_denier,
                    lot_no=item.get("lot_no", lot_no),
                    bag=int(item.get("bag", 0)),
                    per_bag=Decimal(str(item.get("per_bag", per_bag))),
                    gross_wt=Decimal(str(item.get("gross_wt", "0.000"))),
                    tare_wt=Decimal(str(item.get("tare_wt", "0.000"))),
                    net_wt=Decimal(str(item.get("net_wt", "0.000"))),
                    rate=Decimal(str(item.get("rate", rate))),
                    amount=Decimal(str(item.get("amount", "0.000"))),
                    tax_percent=inward.tax_percent,
                    tax_amount=(Decimal(str(item.get("amount", "0.000"))) * inward.tax_percent / Decimal("100.00")).quantize(Decimal("0.001")),
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
                blend_ratio=inward.blend_ratio,
                ply_count=inward.ply_count,
                twists_per_inch=inward.twists_per_inch,
                slub_pattern=inward.slub_pattern,
                core_denier=inward.core_denier,
                lot_no=inward.lot_no,
                bag=inward.bag,
                per_bag=inward.per_bag,
                gross_wt=inward.gross_wt,
                tare_wt=inward.tare_wt,
                net_wt=inward.net_wt,
                rate=inward.rate,
                amount=inward.amount,
                tax_percent=inward.tax_percent,
                tax_amount=inward.tax_amount,
                status=1
            )

        # 5. Maintain Financial Party Ledger
        try:
            from apps.ledger.services import CurrencyLedgerService
            CurrencyLedgerService.post_inward_grn_voucher(inward, user=user)
        except Exception:
            pass

        # 6. Maintain Physical Stock Ledger with Party
        try:
            from apps.ledger.services import StockLedgerService
            from core.constants import StockMovementTypes
            StockLedgerService.record_movement(
                company_id=company_id,
                fy_id=cfyear_id or 1,
                movement_date=inward.inward_date,
                stage="YARN",
                warehouse_id=warehouse_id,
                movement_type=StockMovementTypes.INWARD,
                doc_type="INWARD_GRN",
                doc_number=inward.inward_number,
                item_name=f"{yarn_type} Yarn",
                lot_or_batch_no=lot_no or "GEN",
                in_units=bag,
                in_qty=net_wt,
                unit_rate=rate,
                party_id=inward.mill_id or inward.party_id,
                remarks=f"Inward from Mill/Supplier #{inward.mill_id}",
                check_balance=False,
                user=user,
            )
        except Exception:
            pass

        return inward

    @classmethod
    @transaction.atomic
    def cancel_inward(cls, inward_id: int, company_id: int, user=None) -> parent_yarn_inward_table:
        """Atomically reverse inward stock, restore PO/outward balances, and soft delete."""
        inward = parent_yarn_inward_table.objects.select_for_update().filter(id=inward_id, company_id=company_id, status=1).first()
        if not inward:
            raise ResourceNotFound(f"Yarn Inward with ID {inward_id} not found.")

        # Reverse financial voucher if posted
        try:
            from apps.ledger.models import tl_voucher
            from apps.ledger.services import CurrencyLedgerService
            v = tl_voucher.objects.filter(
                company_id=company_id,
                reference_type="INWARD_GRN",
                reference_no=inward.inward_number,
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
            po_lines_qs = child_po_table.objects.filter(tm_po=inward.po)
            if inward.yarn_count_id:
                po_lines_qs = po_lines_qs.filter(yarn_count_id=inward.yarn_count_id)
            if inward.color_shade_id:
                shade_match = po_lines_qs.filter(color_shade_id=inward.color_shade_id).first()
                line_item = shade_match or po_lines_qs.first()
            else:
                line_item = po_lines_qs.first()

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

        # 4. Maintain Physical Stock Ledger with Destination Party
        try:
            from apps.ledger.services import StockLedgerService
            from core.constants import StockMovementTypes
            StockLedgerService.record_movement(
                company_id=company_id,
                fy_id=cfyear_id or 1,
                movement_date=outward.outward_date,
                stage="YARN",
                warehouse_id=warehouse_id,
                movement_type=StockMovementTypes.OUTWARD,
                doc_type="OUTWARD_DC",
                doc_number=outward.outward_number,
                item_name=f"{outward.yarn_type} Yarn",
                lot_or_batch_no=outward.lot_no or "GEN",
                out_units=bag,
                out_qty=quantity,
                party_id=outward.destination_party_id,
                remarks=f"Outward DC to {outward.outward_type} unit #{outward.destination_party_id}",
                check_balance=False,
                user=user,
            )
        except Exception:
            pass

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

