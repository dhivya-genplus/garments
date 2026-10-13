from __future__ import annotations
from decimal import Decimal
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from core.base_services import BaseService
from core.exceptions import ValidationError, ResourceNotFound, ConflictError
from core.constants import (
    KnittingProgramStatus,
    GreyFabricInwardSources,
    GreyFabricOutwardTypes,
)
from apps.knitting.models import (
    parent_knitting_program_table,
    child_knitting_program_yarn_table,
    grey_fabric_stock_table,
    parent_grey_fabric_inward_table,
    child_grey_fabric_inward_table,
    parent_grey_fabric_outward_table,
    child_grey_fabric_outward_table,
    parent_grey_po_table,
    child_grey_po_table,
    parent_grey_fabric_sales_table,
    child_grey_fabric_sales_table,
    parent_grey_fabric_sales_return_table,
    child_grey_fabric_sales_return_table,
)
from apps.authentication.models import Company, FinancialYear


def _normalize_fk(data: Dict[str, Any], fk_keys: List[str]):
    for key in fk_keys:
        if key in data and isinstance(data[key], (int, str)):
            val = data.pop(key)
            if val is not None and str(val).strip() != "":
                data[f"{key}_id"] = int(val)


class GreyFabricStockService(BaseService):
    """
    Central stock management service for Grey Fabric Rolls & Net Weight.
    Guarantees atomic inventory writes with row-level locks (select_for_update).
    """

    @classmethod
    @transaction.atomic
    def add_inward_stock(
        cls,
        company_id: int,
        warehouse_id: int,
        fabric_id: int,
        fabric_type_id: int,
        dia: str,
        gsm: int,
        gauge: str,
        lot_no: str,
        rolls: int,
        quantity: Decimal,
    ) -> grey_fabric_stock_table:
        stock, _ = grey_fabric_stock_table.objects.select_for_update().get_or_create(
            company_id=company_id,
            warehouse_id=warehouse_id,
            fabric_id=fabric_id,
            fabric_type_id=fabric_type_id,
            dia=dia or "GEN",
            gsm=gsm or 0,
            gauge=gauge or "",
            lot_no=lot_no or "GEN",
        )
        stock.inward_rolls += rolls
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
        fabric_id: int,
        fabric_type_id: int,
        dia: str,
        gsm: int,
        gauge: str,
        lot_no: str,
        rolls: int,
        quantity: Decimal,
    ) -> grey_fabric_stock_table:
        stock = (
            grey_fabric_stock_table.objects
            .select_for_update()
            .filter(
                company_id=company_id,
                warehouse_id=warehouse_id,
                fabric_id=fabric_id,
                fabric_type_id=fabric_type_id,
                dia=dia or "GEN",
                gsm=gsm or 0,
                gauge=gauge or "",
                lot_no=lot_no or "GEN",
            )
            .first()
        )
        if not stock or stock.balance_quantity < quantity or (rolls > 0 and stock.balance_rolls < rolls):
            avail_q = stock.balance_quantity if stock else Decimal("0.000")
            avail_r = stock.balance_rolls if stock else 0
            raise ValidationError(
                f"Insufficient Grey Fabric Stock for Fabric ID {fabric_id} (Dia: {dia}, GSM: {gsm}, Lot: {lot_no}). "
                f"Available: {avail_q} Kg ({avail_r} rolls), Requested: {quantity} Kg ({rolls} rolls)."
            )

        stock.outward_rolls += rolls
        stock.outward_quantity += quantity
        stock.recalculate_balance()
        stock.save()
        return stock

    @classmethod
    @transaction.atomic
    def revert_inward_stock(
        cls,
        company_id: int,
        warehouse_id: int,
        fabric_id: int,
        fabric_type_id: int,
        dia: str,
        gsm: int,
        gauge: str,
        lot_no: str,
        rolls: int,
        quantity: Decimal,
    ) -> grey_fabric_stock_table:
        stock = (
            grey_fabric_stock_table.objects
            .select_for_update()
            .filter(
                company_id=company_id,
                warehouse_id=warehouse_id,
                fabric_id=fabric_id,
                fabric_type_id=fabric_type_id,
                dia=dia or "GEN",
                gsm=gsm or 0,
                gauge=gauge or "",
                lot_no=lot_no or "GEN",
            )
            .first()
        )
        if not stock:
            raise ValidationError("Grey Fabric stock record not found for rollback.")

        if stock.balance_quantity < quantity or (rolls > 0 and stock.balance_rolls < rolls):
            raise ValidationError(
                f"Cannot cancel inward: stock already consumed. "
                f"Available: {stock.balance_quantity} Kg ({stock.balance_rolls} rolls), "
                f"Needs to revert: {quantity} Kg ({rolls} rolls)."
            )

        stock.inward_rolls -= rolls
        stock.inward_quantity -= quantity
        stock.recalculate_balance()
        stock.save()
        return stock

    @classmethod
    @transaction.atomic
    def revert_outward_stock(
        cls,
        company_id: int,
        warehouse_id: int,
        fabric_id: int,
        fabric_type_id: int,
        dia: str,
        gsm: int,
        gauge: str,
        lot_no: str,
        rolls: int,
        quantity: Decimal,
    ) -> grey_fabric_stock_table:
        stock = (
            grey_fabric_stock_table.objects
            .select_for_update()
            .filter(
                company_id=company_id,
                warehouse_id=warehouse_id,
                fabric_id=fabric_id,
                fabric_type_id=fabric_type_id,
                dia=dia or "GEN",
                gsm=gsm or 0,
                gauge=gauge or "",
                lot_no=lot_no or "GEN",
            )
            .first()
        )
        if not stock:
            raise ValidationError("Grey Fabric stock record not found for outward reversal.")

        stock.outward_rolls -= rolls
        stock.outward_quantity -= quantity
        stock.recalculate_balance()
        stock.save()
        return stock

    @classmethod
    @transaction.atomic
    def deduct_sales_stock(
        cls,
        company_id: int,
        warehouse_id: int,
        fabric_id: int,
        fabric_type_id: int,
        dia: str,
        gsm: int,
        gauge: str,
        lot_no: str,
        rolls: int,
        quantity: Decimal,
    ) -> grey_fabric_stock_table:
        stock = (
            grey_fabric_stock_table.objects
            .select_for_update()
            .filter(
                company_id=company_id,
                warehouse_id=warehouse_id,
                fabric_id=fabric_id,
                fabric_type_id=fabric_type_id,
                dia=dia or "GEN",
                gsm=gsm or 0,
                gauge=gauge or "",
                lot_no=lot_no or "GEN",
            )
            .first()
        )
        if not stock or stock.balance_quantity < quantity or (rolls > 0 and stock.balance_rolls < rolls):
            avail_q = stock.balance_quantity if stock else Decimal("0.000")
            avail_r = stock.balance_rolls if stock else 0
            raise ValidationError(
                f"Insufficient Grey Fabric Stock for sale of Fabric ID {fabric_id}. "
                f"Available: {avail_q} Kg ({avail_r} rolls), Requested: {quantity} Kg ({rolls} rolls)."
            )

        stock.sales_rolls += rolls
        stock.sales_quantity += quantity
        stock.recalculate_balance()
        stock.save()
        return stock

    @classmethod
    @transaction.atomic
    def revert_sales_stock(
        cls,
        company_id: int,
        warehouse_id: int,
        fabric_id: int,
        fabric_type_id: int,
        dia: str,
        gsm: int,
        gauge: str,
        lot_no: str,
        rolls: int,
        quantity: Decimal,
    ) -> grey_fabric_stock_table:
        stock = (
            grey_fabric_stock_table.objects
            .select_for_update()
            .filter(
                company_id=company_id,
                warehouse_id=warehouse_id,
                fabric_id=fabric_id,
                fabric_type_id=fabric_type_id,
                dia=dia or "GEN",
                gsm=gsm or 0,
                gauge=gauge or "",
                lot_no=lot_no or "GEN",
            )
            .first()
        )
        if not stock:
            raise ValidationError("Grey Fabric stock record not found for sales reversal.")

        stock.sales_rolls -= rolls
        stock.sales_quantity -= quantity
        stock.recalculate_balance()
        stock.save()
        return stock

    @classmethod
    @transaction.atomic
    def add_sales_return_stock(
        cls,
        company_id: int,
        warehouse_id: int,
        fabric_id: int,
        fabric_type_id: int,
        dia: str,
        gsm: int,
        gauge: str,
        lot_no: str,
        rolls: int,
        quantity: Decimal,
    ) -> grey_fabric_stock_table:
        stock, _ = grey_fabric_stock_table.objects.select_for_update().get_or_create(
            company_id=company_id,
            warehouse_id=warehouse_id,
            fabric_id=fabric_id,
            fabric_type_id=fabric_type_id,
            dia=dia or "GEN",
            gsm=gsm or 0,
            gauge=gauge or "",
            lot_no=lot_no or "GEN",
        )
        stock.sales_return_rolls += rolls
        stock.sales_return_quantity += quantity
        stock.recalculate_balance()
        stock.save()
        return stock

    @classmethod
    @transaction.atomic
    def revert_sales_return_stock(
        cls,
        company_id: int,
        warehouse_id: int,
        fabric_id: int,
        fabric_type_id: int,
        dia: str,
        gsm: int,
        gauge: str,
        lot_no: str,
        rolls: int,
        quantity: Decimal,
    ) -> grey_fabric_stock_table:
        stock = (
            grey_fabric_stock_table.objects
            .select_for_update()
            .filter(
                company_id=company_id,
                warehouse_id=warehouse_id,
                fabric_id=fabric_id,
                fabric_type_id=fabric_type_id,
                dia=dia or "GEN",
                gsm=gsm or 0,
                gauge=gauge or "",
                lot_no=lot_no or "GEN",
            )
            .first()
        )
        if not stock:
            raise ValidationError("Grey Fabric stock record not found for sales return rollback.")

        if stock.balance_quantity < quantity or (rolls > 0 and stock.balance_rolls < rolls):
            raise ValidationError(
                f"Cannot cancel sales return: stock has already been dispatched. "
                f"Available: {stock.balance_quantity} Kg ({stock.balance_rolls} rolls), "
                f"Needs to revert: {quantity} Kg ({rolls} rolls)."
            )

        stock.sales_return_rolls -= rolls
        stock.sales_return_quantity -= quantity
        stock.recalculate_balance()
        stock.save()
        return stock


class KnittingProgramService(BaseService):
    """
    Business logic for Knitting Programs (Job Cards).
    Handles requirement calculations, authorization, and progress tracking.
    """

    @classmethod
    def _generate_program_number(cls, company_id: int) -> str:
        date_str = timezone.now().strftime("%Y%m")
        prefix = f"KP-{date_str}-"
        last = (
            parent_knitting_program_table.objects
            .filter(company_id=company_id, program_number__startswith=prefix)
            .order_by("-program_number")
            .first()
        )
        if last:
            try:
                seq = int(last.program_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def create_program(cls, company_id: int, fy_id: int, data: Dict[str, Any], user) -> parent_knitting_program_table:
        yarn_lines_data = data.pop("yarn_lines", [])

        if not data.get("program_number"):
            data["program_number"] = cls._generate_program_number(company_id)

        _normalize_fk(data, ["knitter", "warehouse", "fabric", "fabric_type"])
        data["company_id"] = company_id
        data["cfyear_id"] = fy_id
        data["created_by"] = user
        data["updated_by"] = user
        data["status"] = KnittingProgramStatus.DRAFT

        program = parent_knitting_program_table(**data)
        program.clean()
        program.save()

        # Save yarn requirement lines
        for y_data in yarn_lines_data:
            _normalize_fk(y_data, ["yarn_count", "color_shade"])
            child_knitting_program_yarn_table.objects.create(
                tm_program=program,
                yarn_count_id=y_data["yarn_count_id"],
                color_shade_id=y_data.get("color_shade_id"),
                yarn_type=y_data.get("yarn_type", "GREY"),
                blend_ratio_percent=Decimal(str(y_data.get("blend_ratio_percent", "100.00"))),
                planned_quantity=Decimal(str(y_data.get("planned_quantity", "0.000"))),
            )

        return program

    @classmethod
    @transaction.atomic
    def authorize_program(cls, program_id: int, company_id: int, user) -> parent_knitting_program_table:
        program = (
            parent_knitting_program_table.objects
            .select_for_update()
            .filter(id=program_id, company_id=company_id)
            .exclude(status=KnittingProgramStatus.CANCELLED)
            .first()
        )
        if not program:
            raise ResourceNotFound(f"Knitting Program {program_id} not found.")

        if program.status == KnittingProgramStatus.AUTHORIZED:
            raise ConflictError("Knitting Program is already authorized.")

        program.status = KnittingProgramStatus.AUTHORIZED
        program.updated_by = user
        program.save(update_fields=["status", "updated_by", "updated_on"])
        return program

    @classmethod
    @transaction.atomic
    def unauthorize_program(cls, program_id: int, company_id: int, user) -> parent_knitting_program_table:
        program = (
            parent_knitting_program_table.objects
            .select_for_update()
            .filter(id=program_id, company_id=company_id)
            .first()
        )
        if not program:
            raise ResourceNotFound(f"Knitting Program {program_id} not found.")

        if program.received_fabric_quantity > 0 or program.issued_yarn_quantity > 0:
            raise ValidationError("Cannot unauthorize program: production or yarn dispatches already initiated.")

        program.status = KnittingProgramStatus.DRAFT
        program.updated_by = user
        program.save(update_fields=["status", "updated_by", "updated_on"])
        return program

    @classmethod
    def get_program_summary(cls, program_id: int, company_id: int) -> Dict[str, Any]:
        program = (
            parent_knitting_program_table.objects
            .prefetch_related("yarn_lines")
            .filter(id=program_id, company_id=company_id)
            .first()
        )
        if not program:
            raise ResourceNotFound(f"Knitting Program {program_id} not found.")

        pending_fabric = max(Decimal("0.000"), program.planned_fabric_quantity - program.received_fabric_quantity)
        pending_yarn = max(Decimal("0.000"), program.total_yarn_required - program.issued_yarn_quantity)

        return {
            "program_id": program.id,
            "program_number": program.program_number,
            "status": program.get_status_display(),
            "knitter": program.knitter.name,
            "fabric": program.fabric.fabric_name,
            "planned_rolls": program.planned_rolls,
            "planned_fabric_quantity": str(program.planned_fabric_quantity),
            "received_fabric_quantity": str(program.received_fabric_quantity),
            "pending_fabric_quantity": str(pending_fabric),
            "total_yarn_required": str(program.total_yarn_required),
            "issued_yarn_quantity": str(program.issued_yarn_quantity),
            "pending_yarn_quantity": str(pending_yarn),
            "expected_loss_percent": str(program.expected_loss_percent),
            "knitting_rate": str(program.knitting_rate),
            "total_knitting_amount": str(program.total_knitting_amount),
        }


class GreyFabricInwardService(BaseService):
    """
    Inward receipt service for Grey Fabric.
    Atomically updates Grey Fabric stock, updates Knitting Program progress,
    and calculates knitting loss and job charges.
    """

    @classmethod
    def _generate_inward_number(cls, company_id: int) -> str:
        date_str = timezone.now().strftime("%Y%m")
        prefix = f"GFIN-{date_str}-"
        last = (
            parent_grey_fabric_inward_table.objects
            .filter(company_id=company_id, inward_number__startswith=prefix)
            .order_by("-inward_number")
            .first()
        )
        if last:
            try:
                seq = int(last.inward_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def post_inward(cls, company_id: int, fy_id: int, data: Dict[str, Any], user) -> parent_grey_fabric_inward_table:
        line_items_data = data.pop("line_items", [])

        if not data.get("inward_number"):
            data["inward_number"] = cls._generate_inward_number(company_id)

        _normalize_fk(data, ["knitting_program", "party", "warehouse", "fabric", "fabric_type"])
        data["company_id"] = company_id
        data["cfyear_id"] = fy_id
        data["created_by"] = user
        data["updated_by"] = user
        data["is_authorized"] = 1
        data["status"] = 1

        inward = parent_grey_fabric_inward_table(**data)
        inward.clean()
        inward.save()

        # Save rolls lines
        rolls_count = len(line_items_data)
        for l_data in line_items_data:
            child_grey_fabric_inward_table.objects.create(
                tm_inward=inward,
                roll_no=l_data.get("roll_no", ""),
                gross_wt=Decimal(str(l_data.get("gross_wt", "0.000"))),
                tare_wt=Decimal(str(l_data.get("tare_wt", "0.000"))),
                net_wt=Decimal(str(l_data.get("net_wt", "0.000"))),
                remarks=l_data.get("remarks", ""),
            )

        if rolls_count > 0 and inward.total_rolls == 0:
            inward.total_rolls = rolls_count
            inward.save(update_fields=["total_rolls"])

        # Update Knitting Program if linked
        if inward.knitting_program_id:
            program = (
                parent_knitting_program_table.objects
                .select_for_update()
                .filter(id=inward.knitting_program_id, company_id=company_id)
                .first()
            )
            if program:
                program.received_fabric_quantity += inward.net_wt
                if program.received_fabric_quantity >= program.planned_fabric_quantity:
                    program.status = KnittingProgramStatus.COMPLETED
                else:
                    program.status = KnittingProgramStatus.IN_PROGRESS
                program.save(update_fields=["received_fabric_quantity", "status", "updated_on"])

        # Atomically credit Grey Fabric stock ledger
        GreyFabricStockService.add_inward_stock(
            company_id=company_id,
            warehouse_id=inward.warehouse_id,
            fabric_id=inward.fabric_id,
            fabric_type_id=inward.fabric_type_id,
            dia=inward.dia,
            gsm=inward.gsm,
            gauge=inward.gauge,
            lot_no=inward.lot_no,
            rolls=inward.total_rolls,
            quantity=inward.net_wt,
        )

        return inward

    @classmethod
    @transaction.atomic
    def cancel_inward(cls, inward_id: int, company_id: int, user) -> parent_grey_fabric_inward_table:
        inward = (
            parent_grey_fabric_inward_table.objects
            .select_for_update()
            .filter(id=inward_id, company_id=company_id, status=1)
            .first()
        )
        if not inward:
            raise ResourceNotFound(f"Active Grey Fabric Inward {inward_id} not found.")

        # Revert Grey Fabric Stock
        GreyFabricStockService.revert_inward_stock(
            company_id=company_id,
            warehouse_id=inward.warehouse_id,
            fabric_id=inward.fabric_id,
            fabric_type_id=inward.fabric_type_id,
            dia=inward.dia,
            gsm=inward.gsm,
            gauge=inward.gauge,
            lot_no=inward.lot_no,
            rolls=inward.total_rolls,
            quantity=inward.net_wt,
        )

        # Restore Knitting Program if linked
        if inward.knitting_program_id:
            program = (
                parent_knitting_program_table.objects
                .select_for_update()
                .filter(id=inward.knitting_program_id, company_id=company_id)
                .first()
            )
            if program:
                program.received_fabric_quantity = max(Decimal("0.000"), program.received_fabric_quantity - inward.net_wt)
                if program.received_fabric_quantity == Decimal("0.000"):
                    program.status = KnittingProgramStatus.AUTHORIZED
                else:
                    program.status = KnittingProgramStatus.IN_PROGRESS
                program.save(update_fields=["received_fabric_quantity", "status", "updated_on"])

        inward.soft_delete(user)
        return inward


class GreyFabricOutwardService(BaseService):
    """
    Outward delivery challan service for Grey Fabric.
    Deducts stock atomically when dispatching to Dyeing units or returning to knitter.
    """

    @classmethod
    def _generate_outward_number(cls, company_id: int) -> str:
        date_str = timezone.now().strftime("%Y%m")
        prefix = f"GFOUT-{date_str}-"
        last = (
            parent_grey_fabric_outward_table.objects
            .filter(company_id=company_id, outward_number__startswith=prefix)
            .order_by("-outward_number")
            .first()
        )
        if last:
            try:
                seq = int(last.outward_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def post_outward(cls, company_id: int, fy_id: int, data: Dict[str, Any], user) -> parent_grey_fabric_outward_table:
        line_items_data = data.pop("line_items", [])

        if not data.get("outward_number"):
            data["outward_number"] = cls._generate_outward_number(company_id)

        _normalize_fk(data, ["warehouse", "destination_party", "fabric", "fabric_type"])
        data["company_id"] = company_id
        data["cfyear_id"] = fy_id
        data["created_by"] = user
        data["updated_by"] = user
        data["is_authorized"] = 1
        data["status"] = 1

        outward = parent_grey_fabric_outward_table(**data)
        outward.clean()

        # Atomically deduct stock first (will raise ValidationError if balance is insufficient)
        GreyFabricStockService.deduct_outward_stock(
            company_id=company_id,
            warehouse_id=outward.warehouse_id,
            fabric_id=outward.fabric_id,
            fabric_type_id=outward.fabric_type_id,
            dia=outward.dia,
            gsm=outward.gsm,
            gauge=outward.gauge,
            lot_no=outward.lot_no,
            rolls=outward.rolls,
            quantity=outward.quantity,
        )

        outward.save()

        # Save rolls lines
        for l_data in line_items_data:
            child_grey_fabric_outward_table.objects.create(
                tm_outward=outward,
                roll_no=l_data.get("roll_no", ""),
                gross_wt=Decimal(str(l_data.get("gross_wt", "0.000"))),
                net_wt=Decimal(str(l_data.get("net_wt", "0.000"))),
                remarks=l_data.get("remarks", ""),
            )

        return outward

    @classmethod
    @transaction.atomic
    def cancel_outward(cls, outward_id: int, company_id: int, user) -> parent_grey_fabric_outward_table:
        outward = (
            parent_grey_fabric_outward_table.objects
            .select_for_update()
            .filter(id=outward_id, company_id=company_id, status=1)
            .first()
        )
        if not outward:
            raise ResourceNotFound(f"Active Grey Fabric Outward {outward_id} not found.")

        # Re-credit stock back to godown
        GreyFabricStockService.revert_outward_stock(
            company_id=company_id,
            warehouse_id=outward.warehouse_id,
            fabric_id=outward.fabric_id,
            fabric_type_id=outward.fabric_type_id,
            dia=outward.dia,
            gsm=outward.gsm,
            gauge=outward.gauge,
            lot_no=outward.lot_no,
            rolls=outward.rolls,
            quantity=outward.quantity,
        )

        outward.soft_delete(user)
        return outward


class GreyPOService(BaseService):
    """
    Purchase Order service for Grey Fabric directly bought from Traders/Mills.
    """

    @classmethod
    def _generate_po_number(cls, company_id: int) -> str:
        date_str = timezone.now().strftime("%Y%m")
        prefix = f"GFPO-{date_str}-"
        last = (
            parent_grey_po_table.objects
            .filter(company_id=company_id, po_number__startswith=prefix)
            .order_by("-po_number")
            .first()
        )
        if last:
            try:
                seq = int(last.po_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def create_po(cls, company_id: int, fy_id: int, data: Dict[str, Any], user) -> parent_grey_po_table:
        line_items_data = data.pop("line_items", [])

        if not data.get("po_number"):
            data["po_number"] = cls._generate_po_number(company_id)

        _normalize_fk(data, ["party", "warehouse"])
        data["company_id"] = company_id
        data["cfyear_id"] = fy_id
        data["created_by"] = user
        data["updated_by"] = user
        data["is_authorized"] = 0
        data["status"] = 1

        po = parent_grey_po_table(**data)
        po.save()

        subtotal = Decimal("0.000")
        total_rolls = 0
        total_qty = Decimal("0.000")

        for l_data in line_items_data:
            item = child_grey_po_table(
                tm_po=po,
                fabric_id=l_data["fabric_id"],
                fabric_type_id=l_data["fabric_type_id"],
                dia=l_data.get("dia", ""),
                gsm=l_data.get("gsm", 0),
                gauge=l_data.get("gauge", ""),
                rolls=l_data.get("rolls", 0),
                quantity=Decimal(str(l_data.get("quantity", "0.000"))),
                rate=Decimal(str(l_data.get("rate", "0.00"))),
            )
            item.clean()
            item.save()
            subtotal += item.amount
            total_rolls += item.rolls
            total_qty += item.quantity

        po.subtotal = subtotal
        po.total_rolls = total_rolls
        po.total_quantity = total_qty
        tax_pct = Decimal(str(po.tax_percent or 0)) / Decimal("100.00")
        po.tax_amount = (subtotal * tax_pct).quantize(Decimal("0.001"))
        po.total_amount = po.subtotal + po.tax_amount
        po.save()

        return po

    @classmethod
    @transaction.atomic
    def authorize_po(cls, po_id: int, company_id: int, user) -> parent_grey_po_table:
        po = (
            parent_grey_po_table.objects
            .select_for_update()
            .filter(id=po_id, company_id=company_id, status=1)
            .first()
        )
        if not po:
            raise ResourceNotFound(f"Grey Fabric PO {po_id} not found.")

        po.is_authorized = 1
        po.updated_by = user
        po.save(update_fields=["is_authorized", "updated_by", "updated_on"])
        return po


class GreyFabricSalesService(BaseService):
    """
    Commercial sales invoice service for Grey Fabric.
    Deducts stock atomically upon invoice creation.
    """

    @classmethod
    def _generate_invoice_number(cls, company_id: int) -> str:
        date_str = timezone.now().strftime("%Y%m")
        prefix = f"GFSAL-{date_str}-"
        last = (
            parent_grey_fabric_sales_table.objects
            .filter(company_id=company_id, invoice_number__startswith=prefix)
            .order_by("-invoice_number")
            .first()
        )
        if last:
            try:
                seq = int(last.invoice_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def create_sales_invoice(cls, company_id: int, fy_id: int, data: Dict[str, Any], user) -> parent_grey_fabric_sales_table:
        line_items_data = data.pop("line_items", [])
        data.pop("amount", None)

        if not data.get("invoice_number"):
            data["invoice_number"] = cls._generate_invoice_number(company_id)

        _normalize_fk(data, ["customer", "warehouse", "fabric", "fabric_type"])
        data["company_id"] = company_id
        data["cfyear_id"] = fy_id
        data["created_by"] = user
        data["updated_by"] = user
        data["is_authorized"] = 1
        data["status"] = 1

        sales = parent_grey_fabric_sales_table(**data)
        sales.clean()

        # Atomically deduct Grey Fabric stock (raises ValidationError if insufficient)
        GreyFabricStockService.deduct_sales_stock(
            company_id=company_id,
            warehouse_id=sales.warehouse_id,
            fabric_id=sales.fabric_id,
            fabric_type_id=sales.fabric_type_id,
            dia=sales.dia,
            gsm=sales.gsm,
            gauge=sales.gauge,
            lot_no=sales.lot_no,
            rolls=sales.rolls,
            quantity=sales.quantity,
        )

        sales.save()

        # Save line items
        for l_data in line_items_data:
            child_grey_fabric_sales_table.objects.create(
                tm_sales=sales,
                roll_no=l_data.get("roll_no", ""),
                gross_wt=Decimal(str(l_data.get("gross_wt", "0.000"))),
                net_wt=Decimal(str(l_data.get("net_wt", "0.000"))),
                rate=Decimal(str(l_data.get("rate", "0.00"))),
                amount=Decimal(str(l_data.get("amount", "0.000"))),
                remarks=l_data.get("remarks", ""),
            )

        return sales

    @classmethod
    @transaction.atomic
    def cancel_sales_invoice(cls, sales_id: int, company_id: int, user) -> parent_grey_fabric_sales_table:
        sales = (
            parent_grey_fabric_sales_table.objects
            .select_for_update()
            .filter(id=sales_id, company_id=company_id, status=1)
            .first()
        )
        if not sales:
            raise ResourceNotFound(f"Active Grey Fabric Sales Invoice {sales_id} not found.")

        # Re-credit stock back to godown
        GreyFabricStockService.revert_sales_stock(
            company_id=company_id,
            warehouse_id=sales.warehouse_id,
            fabric_id=sales.fabric_id,
            fabric_type_id=sales.fabric_type_id,
            dia=sales.dia,
            gsm=sales.gsm,
            gauge=sales.gauge,
            lot_no=sales.lot_no,
            rolls=sales.rolls,
            quantity=sales.quantity,
        )

        sales.soft_delete(user)
        return sales


class GreyFabricSalesReturnService(BaseService):
    """
    Sales return credit service for Grey Fabric.
    Re-credits stock atomically upon return acceptance.
    """

    @classmethod
    def _generate_return_number(cls, company_id: int) -> str:
        date_str = timezone.now().strftime("%Y%m")
        prefix = f"GFSRET-{date_str}-"
        last = (
            parent_grey_fabric_sales_return_table.objects
            .filter(company_id=company_id, return_number__startswith=prefix)
            .order_by("-return_number")
            .first()
        )
        if last:
            try:
                seq = int(last.return_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def create_sales_return(cls, company_id: int, fy_id: int, data: Dict[str, Any], user) -> parent_grey_fabric_sales_return_table:
        line_items_data = data.pop("line_items", [])
        data.pop("amount", None)
        if "reason" in data and "return_reason" not in data:
            data["return_reason"] = data.pop("reason")

        if not data.get("return_number"):
            data["return_number"] = cls._generate_return_number(company_id)

        _normalize_fk(data, ["sales_invoice", "customer", "warehouse", "fabric", "fabric_type"])
        data["company_id"] = company_id
        data["cfyear_id"] = fy_id
        data["created_by"] = user
        data["updated_by"] = user
        data["is_authorized"] = 1
        data["status"] = 1

        ret = parent_grey_fabric_sales_return_table(**data)
        ret.clean()
        ret.save()

        # Re-credit stock in godown
        GreyFabricStockService.add_sales_return_stock(
            company_id=company_id,
            warehouse_id=ret.warehouse_id,
            fabric_id=ret.fabric_id,
            fabric_type_id=ret.fabric_type_id,
            dia=ret.dia,
            gsm=ret.gsm,
            gauge=ret.gauge,
            lot_no=ret.lot_no,
            rolls=ret.rolls,
            quantity=ret.quantity,
        )

        # Save line items
        for l_data in line_items_data:
            child_grey_fabric_sales_return_table.objects.create(
                tm_return=ret,
                roll_no=l_data.get("roll_no", ""),
                gross_wt=Decimal(str(l_data.get("gross_wt", "0.000"))),
                net_wt=Decimal(str(l_data.get("net_wt", "0.000"))),
                rate=Decimal(str(l_data.get("rate", "0.00"))),
                amount=Decimal(str(l_data.get("amount", "0.000"))),
                remarks=l_data.get("remarks", ""),
            )

        return ret

    @classmethod
    @transaction.atomic
    def cancel_sales_return(cls, return_id: int, company_id: int, user) -> parent_grey_fabric_sales_return_table:
        ret = (
            parent_grey_fabric_sales_return_table.objects
            .select_for_update()
            .filter(id=return_id, company_id=company_id, status=1)
            .first()
        )
        if not ret:
            raise ResourceNotFound(f"Active Grey Fabric Sales Return {return_id} not found.")

        # Revert returned stock from godown
        GreyFabricStockService.revert_sales_return_stock(
            company_id=company_id,
            warehouse_id=ret.warehouse_id,
            fabric_id=ret.fabric_id,
            fabric_type_id=ret.fabric_type_id,
            dia=ret.dia,
            gsm=ret.gsm,
            gauge=ret.gauge,
            lot_no=ret.lot_no,
            rolls=ret.rolls,
            quantity=ret.quantity,
        )

        ret.soft_delete(user)
        return ret

