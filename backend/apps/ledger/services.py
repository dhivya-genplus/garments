from decimal import Decimal
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from core.base_services import BaseService
from core.exceptions import ValidationError, ResourceNotFound, ConflictError
from core.constants import StockMovementTypes, VoucherTypes
from core.formats import FormatService
from apps.ledger.models import (
    tl_stock_movement,
    tm_stage_stock,
    tl_voucher,
    tl_voucher_line,
)


class StockLedgerService(BaseService):
    """
    Physical Stock Ledger Engine:
    Maintains running stock (Units & Weight/Qty) for any stage:
    YARN, GREY_FABRIC, DYED_FABRIC, CUT_PANELS, GARMENTS.
    """

    @classmethod
    @transaction.atomic
    def record_movement(
        cls,
        company_id: int,
        fy_id: int,
        movement_date,
        stage: str,
        warehouse_id: int,
        movement_type: str,
        doc_type: str,
        doc_number: str,
        item_name: str,
        lot_or_batch_no: str,
        in_units: int = 0,
        in_qty: Decimal = Decimal("0.000"),
        out_units: int = 0,
        out_qty: Decimal = Decimal("0.000"),
        dia: str = "",
        gsm: int = 0,
        unit_rate: Decimal = Decimal("0.00"),
        party_id: Optional[int] = None,
        remarks: str = "",
        check_balance: bool = True,
        user=None,
    ) -> tl_stock_movement:
        date_obj = FormatService.parse_date(movement_date) or timezone.now().date()
        in_qty = Decimal(str(in_qty))
        out_qty = Decimal(str(out_qty))
        unit_rate = Decimal(str(unit_rate))

        # 1. Update or create live snapshot row in tm_stage_stock with atomic lock
        stock, _ = tm_stage_stock.objects.select_for_update().get_or_create(
            company_id=company_id,
            warehouse_id=warehouse_id,
            stage=stage.upper(),
            item_name=item_name,
            lot_or_batch_no=lot_or_batch_no or "GEN",
            defaults={"dia": dia, "gsm": gsm},
        )

        # 2. Check for negative stock on outward
        if check_balance and out_qty > 0 and stock.balance_qty < out_qty:
            raise ValidationError(
                f"Insufficient stock for {item_name} (Lot: {lot_or_batch_no}) in {stage}. "
                f"Available: {stock.balance_qty} Kg ({stock.balance_units} units). "
                f"Requested to issue: {out_qty} Kg ({out_units} units)."
            )

        # 3. Update balances
        stock.inward_units += in_units
        stock.inward_qty += in_qty
        stock.outward_units += out_units
        stock.outward_qty += out_qty
        stock.recalculate_balance()
        stock.save()

        # 4. Append immutable historical movement row
        total_val = (stock.balance_qty * unit_rate).quantize(Decimal("0.01")) if unit_rate > 0 else Decimal("0.00")
        movement = tl_stock_movement.objects.create(
            company_id=company_id,
            cfyear_id=fy_id,
            movement_date=date_obj,
            stage=stage.upper(),
            warehouse_id=warehouse_id,
            movement_type=movement_type,
            doc_type=doc_type,
            doc_number=doc_number,
            item_name=item_name,
            lot_or_batch_no=lot_or_batch_no or "GEN",
            in_units=in_units,
            in_qty=in_qty,
            out_units=out_units,
            out_qty=out_qty,
            balance_units=stock.balance_units,
            balance_qty=stock.balance_qty,
            unit_rate=unit_rate,
            total_value=total_val,
            party_id=party_id,
            remarks=remarks,
            created_by=user,
        )

        return movement

    @classmethod
    def get_live_stock(cls, company_id: int, stage: Optional[str] = None, warehouse_id: Optional[int] = None):
        qs = tm_stage_stock.objects.filter(company_id=company_id)
        if stage:
            qs = qs.filter(stage=stage.upper())
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        return qs.order_by("stage", "item_name")

    @classmethod
    def get_party_stock_summary(
        cls,
        company_id: int,
        party_id: int,
        stage: Optional[str] = None,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Calculates party-wise stock summary and running movements.
        Tracks physical stock in/out against Mills, Knitters, Dyers, Customers.
        """
        from apps.masters.models import PartyMaster

        party = PartyMaster.objects.filter(id=party_id, company_id=company_id, is_deleted=False).first()
        if not party:
            raise ResourceNotFound(f"Party #{party_id} not found.")

        parsed_from = FormatService.parse_date(from_date) if from_date else None
        parsed_to = FormatService.parse_date(to_date) if to_date else None

        qs = (
            tl_stock_movement.objects
            .select_related("warehouse", "party")
            .filter(company_id=company_id, party_id=party_id)
            .order_by("movement_date", "id")
        )

        if stage:
            qs = qs.filter(stage=stage.upper())
        if parsed_from:
            qs = qs.filter(movement_date__gte=parsed_from)
        if parsed_to:
            qs = qs.filter(movement_date__lte=parsed_to)

        total_in_units = 0
        total_in_qty = Decimal("0.000")
        total_out_units = 0
        total_out_qty = Decimal("0.000")

        movements_list = []
        for m in qs:
            total_in_units += m.in_units
            total_in_qty += m.in_qty
            total_out_units += m.out_units
            total_out_qty += m.out_qty

            tx_against = f"{m.doc_type} #{m.doc_number}"
            movements_list.append({
                "id": m.id,
                "movement_date": m.movement_date.strftime("%d/%m/%Y"),
                "stage": m.stage,
                "warehouse": m.warehouse_id,
                "warehouse_name": m.warehouse.name if m.warehouse else "",
                "movement_type": m.movement_type,
                "doc_type": m.doc_type,
                "doc_number": m.doc_number,
                "transaction_against": tx_against,
                "item_name": m.item_name,
                "lot_or_batch_no": m.lot_or_batch_no,
                "in_units": m.in_units,
                "in_qty": str(m.in_qty),
                "out_units": m.out_units,
                "out_qty": str(m.out_qty),
                "balance_qty": str(m.balance_qty),
                "unit_rate": str(m.unit_rate),
                "remarks": m.remarks or "",
            })

        net_qty = total_in_qty - total_out_qty
        net_units = total_in_units - total_out_units

        return {
            "party": {
                "id": party.id,
                "code": party.code,
                "name": party.name,
                "party_type": party.party_type,
                "party_type_display": party.get_party_type_display(),
            },
            "stage_filter": stage.upper() if stage else "ALL",
            "date_range": {
                "from_date": from_date or "All Time",
                "to_date": to_date or "Present",
            },
            "total_inward_units": total_in_units,
            "total_inward_qty": str(total_in_qty.quantize(Decimal("0.001"))),
            "total_outward_units": total_out_units,
            "total_outward_qty": str(total_out_qty.quantize(Decimal("0.001"))),
            "net_units": net_units,
            "net_quantity": str(net_qty.quantize(Decimal("0.001"))),
            "movement_count": len(movements_list),
            "movements": movements_list,
        }


class CurrencyLedgerService(BaseService):
    """
    Financial Currency Ledger Engine (Double-Entry Bookkeeping):
    Posts balanced vouchers (Sum Debit == Sum Credit), maintains party accounts,
    and supports atomic reversals.
    """

    @classmethod
    def _generate_voucher_number(cls, company_id: int, voucher_type: str = "JV") -> str:
        date_str = timezone.now().strftime("%Y%m")
        prefix = f"{voucher_type[:2].upper()}-{date_str}-"
        last = (
            tl_voucher.objects
            .filter(company_id=company_id, voucher_number__startswith=prefix)
            .order_by("-voucher_number")
            .first()
        )
        if last:
            try:
                seq = int(last.voucher_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def post_voucher(
        cls,
        company_id: int,
        fy_id: int,
        voucher_date,
        voucher_type: str,
        stage: str,
        lines: List[Dict[str, Any]],
        party_id: Optional[int] = None,
        reference_type: str = "",
        reference_no: str = "",
        reference_id: Optional[int] = None,
        narration: str = "",
        user=None,
    ) -> tl_voucher:
        """
        Creates an immutable, posted double-entry voucher.
        lines = [
            {"account_code": "5001", "account_name": "Knitting Charges Expense", "debit": 18000.00, "credit": 0.00},
            {"account_code": "2001", "account_name": "Knitter Payable", "party_id": 1, "debit": 0.00, "credit": 18000.00},
        ]
        """
        date_obj = FormatService.parse_date(voucher_date) or timezone.now().date()

        # 1. Enforce Double-Entry Balance Invariant: Sum(Debit) == Sum(Credit)
        total_dr = sum(Decimal(str(l.get("debit", 0))) for l in lines)
        total_cr = sum(Decimal(str(l.get("credit", 0))) for l in lines)

        if total_dr != total_cr:
            raise ValidationError(
                f"Ledger Imbalance: Total Debit (INR {total_dr}) does not equal Total Credit (INR {total_cr}). "
                f"Every financial voucher must be strictly balanced."
            )

        if total_dr <= Decimal("0.00"):
            raise ValidationError("Voucher total amount must be strictly greater than zero.")

        # 2. Create Voucher Header
        voucher_no = cls._generate_voucher_number(company_id, voucher_type)
        voucher = tl_voucher.objects.create(
            voucher_number=voucher_no,
            voucher_date=date_obj,
            voucher_type=voucher_type,
            stage=stage.upper() if stage else "",
            company_id=company_id,
            cfyear_id=fy_id,
            party_id=party_id,
            reference_type=reference_type,
            reference_no=reference_no,
            reference_id=reference_id,
            narration=narration,
            total_debit=total_dr,
            total_credit=total_cr,
            is_posted=True,
            created_by=user,
            updated_by=user,
        )

        # 3. Create Voucher Lines
        line_objs = []
        for line in lines:
            line_objs.append(
                tl_voucher_line(
                    voucher=voucher,
                    account_code=line["account_code"],
                    account_name=line["account_name"],
                    party_id=line.get("party_id"),
                    debit=Decimal(str(line.get("debit", 0))),
                    credit=Decimal(str(line.get("credit", 0))),
                    narration=line.get("narration", narration),
                )
            )
        tl_voucher_line.objects.bulk_create(line_objs)

        return voucher

    @classmethod
    @transaction.atomic
    def reverse_voucher(cls, voucher_id: int, company_id: int, reversal_date, user=None) -> tl_voucher:
        """
        Reverses a posted voucher by creating a contra voucher swapping debits and credits.
        Original voucher is marked is_reversed=True and never deleted.
        """
        original = (
            tl_voucher.objects
            .select_for_update()
            .prefetch_related("lines")
            .filter(id=voucher_id, company_id=company_id)
            .first()
        )
        if not original:
            raise ResourceNotFound(f"Voucher {voucher_id} not found.")

        if original.is_reversed:
            raise ConflictError(f"Voucher {original.voucher_number} is already reversed.")

        # Build contra lines (Debit -> Credit, Credit -> Debit)
        contra_lines = []
        for l in original.lines.all():
            contra_lines.append({
                "account_code": l.account_code,
                "account_name": l.account_name,
                "party_id": l.party_id,
                "debit": l.credit,
                "credit": l.debit,
                "narration": f"Reversal of {original.voucher_number}: {l.narration}",
            })

        reversal = cls.post_voucher(
            company_id=company_id,
            fy_id=original.cfyear_id,
            voucher_date=reversal_date,
            voucher_type=VoucherTypes.JOURNAL,
            stage=original.stage,
            lines=contra_lines,
            party_id=original.party_id,
            reference_type="REVERSAL",
            reference_no=original.voucher_number,
            reference_id=original.id,
            narration=f"Reversal contra for {original.voucher_number}",
            user=user,
        )

        original.is_reversed = True
        original.reversed_by = reversal
        original.save(update_fields=["is_reversed", "reversed_by", "updated_on"])

        return reversal

    @classmethod
    def get_party_ledger_statement(
        cls,
        company_id: int,
        party_id: int,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        reference_no: Optional[str] = None,
        voucher_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Computes running debit/credit statement for any party.
        Incorporates PartyMaster opening balance and optional date range (from_date, to_date),
        plus transaction reference filters (reference_no, voucher_type).
        """
        from apps.masters.models import PartyMaster
        from core.constants import PartyTypes

        party = PartyMaster.objects.filter(id=party_id, company_id=company_id, is_deleted=False).first()
        if not party:
            raise ResourceNotFound(f"Party #{party_id} not found.")

        parsed_from = FormatService.parse_date(from_date) if from_date else None
        parsed_to = FormatService.parse_date(to_date) if to_date else None

        # 1. Base opening balance from Party Master
        raw_ob = party.opening_balance or Decimal("0.00")
        if party.party_type == PartyTypes.CUSTOMER:
            opening_balance = raw_ob
        else:
            opening_balance = -raw_ob

        # 2. If from_date is specified, accumulate all posted movements prior to from_date into opening balance
        if parsed_from:
            prior_lines = (
                tl_voucher_line.objects
                .filter(
                    voucher__company_id=company_id,
                    party_id=party_id,
                    voucher__is_posted=True,
                    voucher__voucher_date__lt=parsed_from,
                )
            )
            for pl in prior_lines:
                opening_balance += (pl.debit - pl.credit)

        # 3. Fetch period transactions
        lines_qs = (
            tl_voucher_line.objects
            .select_related("voucher")
            .filter(
                voucher__company_id=company_id,
                party_id=party_id,
                voucher__is_posted=True,
            )
            .order_by("voucher__voucher_date", "voucher__id", "id")
        )

        if parsed_from:
            lines_qs = lines_qs.filter(voucher__voucher_date__gte=parsed_from)
        if parsed_to:
            lines_qs = lines_qs.filter(voucher__voucher_date__lte=parsed_to)
        if reference_no:
            lines_qs = lines_qs.filter(voucher__reference_no__icontains=reference_no)
        if voucher_type:
            lines_qs = lines_qs.filter(voucher__voucher_type__iexact=voucher_type)

        statement = []
        running_balance = opening_balance
        total_dr = Decimal("0.00")
        total_cr = Decimal("0.00")

        for l in lines_qs:
            total_dr += l.debit
            total_cr += l.credit
            # Positive = Receivable (Dr balance), Negative = Payable (Cr balance)
            running_balance += (l.debit - l.credit)

            tx_against = ""
            if l.voucher.reference_type and l.voucher.reference_no:
                tx_against = f"{l.voucher.reference_type} #{l.voucher.reference_no}"
            elif l.voucher.reference_no:
                tx_against = l.voucher.reference_no
            elif l.voucher.reference_type:
                tx_against = l.voucher.reference_type
            else:
                tx_against = l.voucher.voucher_type

            statement.append({
                "voucher_id": l.voucher.id,
                "voucher_number": l.voucher.voucher_number,
                "voucher_date": l.voucher.voucher_date.strftime("%d/%m/%Y"),
                "voucher_type": l.voucher.voucher_type,
                "transaction_against": tx_against,
                "reference_type": l.voucher.reference_type or "",
                "reference_no": l.voucher.reference_no or "",
                "reference_id": l.voucher.reference_id,
                "account": l.account_name,
                "particulars": l.narration or l.voucher.narration or l.account_name,
                "debit": str(l.debit.quantize(Decimal("0.01"))),
                "credit": str(l.credit.quantize(Decimal("0.01"))),
                "running_balance": str(running_balance.quantize(Decimal("0.01"))),
                "balance_type": "RECEIVABLE (Dr)" if running_balance > 0 else ("PAYABLE (Cr)" if running_balance < 0 else "NIL"),
                "narration": l.narration or l.voucher.narration or "",
            })

        closing_balance = running_balance
        return {
            "party": {
                "id": party.id,
                "code": party.code,
                "name": party.name,
                "party_type": party.party_type,
                "party_type_display": party.get_party_type_display(),
                "gst_number": party.gst_number,
                "phone": party.phone,
                "credit_days": party.credit_days,
                "credit_limit": str(party.credit_limit),
                "city": party.city,
                "state": party.state,
            },
            "period": {
                "from_date": parsed_from.strftime("%d/%m/%Y") if parsed_from else None,
                "to_date": parsed_to.strftime("%d/%m/%Y") if parsed_to else None,
            },
            "filter": {
                "reference_no": reference_no or None,
                "voucher_type": voucher_type or None,
            },
            "opening_balance": str(opening_balance.quantize(Decimal("0.01"))),
            "opening_balance_type": "RECEIVABLE (Dr)" if opening_balance > 0 else ("PAYABLE (Cr)" if opening_balance < 0 else "NIL"),
            "total_debit": str(total_dr.quantize(Decimal("0.01"))),
            "total_credit": str(total_cr.quantize(Decimal("0.01"))),
            "net_balance": str(closing_balance.quantize(Decimal("0.01"))),
            "closing_balance": str(closing_balance.quantize(Decimal("0.01"))),
            "balance_type": "RECEIVABLE" if closing_balance >= 0 else "PAYABLE",
            "closing_balance_type": "RECEIVABLE (Dr)" if closing_balance > 0 else ("PAYABLE (Cr)" if closing_balance < 0 else "NIL"),
            "transaction_count": len(statement),
            "transactions": statement,
        }

    @classmethod
    @transaction.atomic
    def record_party_payment(
        cls,
        company_id: int,
        fy_id: int,
        party_id: int,
        amount: Decimal,
        payment_date=None,
        payment_mode: str = "BANK",
        reference_no: str = "",
        against_doc_type: str = "",
        against_doc_number: str = "",
        bank_or_cash_account_code: str = "1001",
        bank_or_cash_account_name: str = "Bank Account",
        narration: str = "",
        user=None,
    ) -> tl_voucher:
        """
        Record a payment voucher to a party (Mill, Supplier, Knitter, Dyer).
        Tracks payment against invoice/bill or reference transaction.
        Debit: Party Account (reduces payable liability)
        Credit: Cash / Bank Account (reduces asset)
        """
        from apps.masters.models import PartyMaster

        party = PartyMaster.objects.filter(id=party_id, company_id=company_id, is_deleted=False).first()
        if not party:
            raise ResourceNotFound(f"Party #{party_id} not found.")

        amt = Decimal(str(amount)).quantize(Decimal("0.01"))
        if amt <= Decimal("0.00"):
            raise ValidationError("Payment amount must be greater than zero.")

        p_date = payment_date or timezone.now().date()
        party_acc = f"{party.name} ({party.get_party_type_display()})"
        
        if against_doc_number:
            ref_type = against_doc_type or "INWARD_GRN"
            ref_num = against_doc_number
            narr = narration or (f"Payment against {against_doc_number} via {payment_mode} (Ref: {reference_no})" if reference_no else f"Payment against {against_doc_number} via {payment_mode}")
        else:
            ref_type = payment_mode
            ref_num = reference_no
            narr = narration or f"Payment to {party.name} via {payment_mode}"

        lines = [
            {
                "account_code": "2001",
                "account_name": party_acc,
                "party_id": party.id,
                "debit": amt,
                "credit": Decimal("0.00"),
                "narration": narr,
            },
            {
                "account_code": bank_or_cash_account_code,
                "account_name": bank_or_cash_account_name,
                "party_id": None,
                "debit": Decimal("0.00"),
                "credit": amt,
                "narration": f"Payment disbursed via {payment_mode}",
            },
        ]

        return cls.post_voucher(
            company_id=company_id,
            fy_id=fy_id,
            voucher_date=p_date,
            voucher_type=VoucherTypes.PAYMENT,
            stage="",
            lines=lines,
            party_id=party.id,
            reference_type=ref_type,
            reference_no=ref_num,
            narration=narr,
            user=user,
        )

    @classmethod
    @transaction.atomic
    def record_party_receipt(
        cls,
        company_id: int,
        fy_id: int,
        party_id: int,
        amount: Decimal,
        receipt_date=None,
        payment_mode: str = "BANK",
        reference_no: str = "",
        against_doc_type: str = "",
        against_doc_number: str = "",
        bank_or_cash_account_code: str = "1001",
        bank_or_cash_account_name: str = "Bank Account",
        narration: str = "",
        user=None,
    ) -> tl_voucher:
        """
        Record a payment receipt voucher from a party (Customer).
        Tracks receipt against sales invoice or reference transaction.
        Debit: Cash / Bank Account (increases asset)
        Credit: Customer Account (reduces receivable)
        """
        from apps.masters.models import PartyMaster

        party = PartyMaster.objects.filter(id=party_id, company_id=company_id, is_deleted=False).first()
        if not party:
            raise ResourceNotFound(f"Party #{party_id} not found.")

        amt = Decimal(str(amount)).quantize(Decimal("0.01"))
        if amt <= Decimal("0.00"):
            raise ValidationError("Receipt amount must be greater than zero.")

        r_date = receipt_date or timezone.now().date()
        party_acc = f"{party.name} (Customer Receivable)"

        if against_doc_number:
            ref_type = against_doc_type or "TAX_INVOICE"
            ref_num = against_doc_number
            narr = narration or (f"Receipt against {against_doc_number} via {payment_mode} (Ref: {reference_no})" if reference_no else f"Receipt against {against_doc_number} via {payment_mode}")
        else:
            ref_type = payment_mode
            ref_num = reference_no
            narr = narration or f"Receipt from {party.name} via {payment_mode}"

        lines = [
            {
                "account_code": bank_or_cash_account_code,
                "account_name": bank_or_cash_account_name,
                "party_id": None,
                "debit": amt,
                "credit": Decimal("0.00"),
                "narration": f"Receipt collected via {payment_mode}",
            },
            {
                "account_code": "1005",
                "account_name": party_acc,
                "party_id": party.id,
                "debit": Decimal("0.00"),
                "credit": amt,
                "narration": narr,
            },
        ]

        return cls.post_voucher(
            company_id=company_id,
            fy_id=fy_id,
            voucher_date=r_date,
            voucher_type=VoucherTypes.RECEIPT,
            stage="",
            lines=lines,
            party_id=party.id,
            reference_type=ref_type,
            reference_no=ref_num,
            narration=narr,
            user=user,
        )

    @classmethod
    @transaction.atomic
    def post_sales_invoice_voucher(cls, sales, user=None) -> tl_voucher:
        """
        Automatically posts a balanced Sales Invoice voucher against the customer.
        Debit: Customer Receivable (total_amount)
        Credit: Sales Revenue (subtotal)
        Credit: Output GST Tax (tax_amount)
        """
        from apps.authentication.models import FinancialYear

        total_amount = Decimal(str(sales.total_amount)).quantize(Decimal("0.01"))
        subtotal = Decimal(str(sales.subtotal)).quantize(Decimal("0.01"))
        tax_amount = Decimal(str(sales.tax_amount)).quantize(Decimal("0.01"))

        if total_amount <= Decimal("0.00"):
            return None

        fy_id = sales.cfyear_id or getattr(sales.company.current_financial_year, "id", None)
        if not fy_id:
            fy = FinancialYear.objects.filter(company_id=sales.company_id).first()
            fy_id = fy.id if fy else None

        customer = sales.customer
        customer_name = customer.name if customer else "Customer"

        lines = [
            {
                "account_code": "1005",
                "account_name": f"{customer_name} (Customer Receivable)",
                "party_id": sales.customer_id,
                "debit": total_amount,
                "credit": Decimal("0.00"),
                "narration": f"Yarn Sales Invoice #{sales.invoice_number}",
            },
            {
                "account_code": "4001",
                "account_name": "Yarn Sales Revenue",
                "party_id": None,
                "debit": Decimal("0.00"),
                "credit": subtotal,
                "narration": f"Yarn Sales Invoice #{sales.invoice_number} Subtotal",
            },
        ]

        if tax_amount > Decimal("0.00"):
            lines.append({
                "account_code": "2005",
                "account_name": "GST Output Tax Payable",
                "party_id": None,
                "debit": Decimal("0.00"),
                "credit": tax_amount,
                "narration": f"GST on Yarn Sales #{sales.invoice_number}",
            })

        return cls.post_voucher(
            company_id=sales.company_id,
            fy_id=fy_id,
            voucher_date=sales.invoice_date,
            voucher_type=VoucherTypes.SALES,
            stage="YARN",
            lines=lines,
            party_id=sales.customer_id,
            reference_type="SALES_INVOICE",
            reference_no=sales.invoice_number,
            reference_id=sales.id,
            narration=f"Yarn Sales Invoice #{sales.invoice_number} to {customer_name}",
            user=user,
        )

    @classmethod
    @transaction.atomic
    def post_sales_return_voucher(cls, sales_return, user=None) -> tl_voucher:
        """
        Automatically posts a balanced Sales Return (Credit Note) voucher against the customer.
        Debit: Yarn Sales Return (subtotal)
        Debit: GST Output Tax Credit Note (tax_amount)
        Credit: Customer Receivable (total_amount) -> Reduces customer receivable
        """
        from apps.authentication.models import FinancialYear

        subtotal = Decimal(str(sales_return.subtotal or sales_return.amount or 0)).quantize(Decimal("0.01"))
        tax_amount = Decimal(str(sales_return.tax_amount or 0)).quantize(Decimal("0.01"))
        total_amount = subtotal + tax_amount

        if total_amount <= Decimal("0.00"):
            return None

        fy_id = sales_return.cfyear_id or getattr(sales_return.company.current_financial_year, "id", None)
        if not fy_id:
            fy = FinancialYear.objects.filter(company_id=sales_return.company_id).first()
            fy_id = fy.id if fy else None

        customer = sales_return.customer
        customer_name = customer.name if customer else "Customer"

        lines = [
            {
                "account_code": "4002",
                "account_name": "Yarn Sales Return",
                "party_id": None,
                "debit": subtotal,
                "credit": Decimal("0.00"),
                "narration": f"Yarn Sales Return #{sales_return.return_number} Material",
            },
        ]

        if tax_amount > Decimal("0.00"):
            lines.append({
                "account_code": "2005",
                "account_name": "GST Output Tax Credit Note",
                "party_id": None,
                "debit": tax_amount,
                "credit": Decimal("0.00"),
                "narration": f"GST on Sales Return #{sales_return.return_number}",
            })

        lines.append({
            "account_code": "1005",
            "account_name": f"{customer_name} (Customer Receivable)",
            "party_id": sales_return.customer_id,
            "debit": Decimal("0.00"),
            "credit": total_amount,
            "narration": f"Sales Return #{sales_return.return_number} Credit to {customer_name}",
        })

        ref_no = sales_return.return_number
        if sales_return.sales_invoice:
            ref_no = f"{sales_return.return_number} (Agst {sales_return.sales_invoice.invoice_number})"

        return cls.post_voucher(
            company_id=sales_return.company_id,
            fy_id=fy_id,
            voucher_date=sales_return.return_date,
            voucher_type=VoucherTypes.JOURNAL,
            stage="YARN",
            lines=lines,
            party_id=sales_return.customer_id,
            reference_type="SALES_RETURN",
            reference_no=ref_no,
            reference_id=sales_return.id,
            narration=f"Yarn Sales Return #{sales_return.return_number} from {customer_name}",
            user=user,
        )

    @classmethod
    @transaction.atomic
    def post_inward_grn_voucher(cls, inward, user=None) -> tl_voucher:
        """
        Automatically posts a balanced Purchase/GRN voucher against the supplier/mill.
        Debit: Yarn Inventory Asset (subtotal)
        Debit: Input GST Tax (tax_amount)
        Credit: Supplier / Mill Payable (total_amount)
        """
        from apps.authentication.models import FinancialYear

        total_amount = Decimal(str(getattr(inward, "total_amount", 0) or 0)).quantize(Decimal("0.01"))
        subtotal = Decimal(str(getattr(inward, "subtotal", 0) or total_amount)).quantize(Decimal("0.01"))
        tax_amount = Decimal(str(getattr(inward, "tax_amount", 0) or 0)).quantize(Decimal("0.01"))

        if total_amount <= Decimal("0.00"):
            # Calculate from gross/net if applicable
            net_wt = Decimal(str(inward.net_weight or 0))
            rate = Decimal(str(inward.rate_per_kg or 0))
            subtotal = (net_wt * rate).quantize(Decimal("0.01"))
            tax_amount = (subtotal * Decimal("0.05")).quantize(Decimal("0.01"))
            total_amount = subtotal + tax_amount

        if total_amount <= Decimal("0.00"):
            return None

        fy_id = getattr(inward, "cfyear_id", None) or getattr(inward.company.current_financial_year, "id", None)
        if not fy_id:
            fy = FinancialYear.objects.filter(company_id=inward.company_id).first()
            fy_id = fy.id if fy else None

        party = getattr(inward, "party", None) or getattr(inward, "mill", None)
        party_name = party.name if party else "Supplier"
        party_id = party.id if party else None

        lines = [
            {
                "account_code": "1003",
                "account_name": "Yarn Stock Inventory Asset",
                "party_id": None,
                "debit": subtotal,
                "credit": Decimal("0.00"),
                "narration": f"Yarn Inward GRN #{inward.inward_number} Material",
            },
        ]

        if tax_amount > Decimal("0.00"):
            lines.append({
                "account_code": "1006",
                "account_name": "GST Input Tax Credit Asset",
                "party_id": None,
                "debit": tax_amount,
                "credit": Decimal("0.00"),
                "narration": f"GST on Yarn Inward #{inward.inward_number}",
            })

        lines.append({
            "account_code": "2001",
            "account_name": f"{party_name} (Supplier Payable)",
            "party_id": party_id,
            "debit": Decimal("0.00"),
            "credit": total_amount,
            "narration": f"Yarn Inward GRN #{inward.inward_number} Bill Payable",
        })

        return cls.post_voucher(
            company_id=inward.company_id,
            fy_id=fy_id,
            voucher_date=inward.inward_date,
            voucher_type=VoucherTypes.PURCHASE,
            stage="YARN",
            lines=lines,
            party_id=party_id,
            reference_type="INWARD_GRN",
            reference_no=inward.inward_number,
            reference_id=inward.id,
            narration=f"Yarn Inward GRN #{inward.inward_number} from {party_name}",
            user=user,
        )
