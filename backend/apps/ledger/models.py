from decimal import Decimal
from django.db import models
from django.conf import settings
from core.base_models import UppercaseModel
from apps.authentication.models import Company, FinancialYear
from apps.masters.models import PartyMaster, WarehouseMaster
from core.constants import StockMovementTypes, VoucherTypes


class tl_stock_movement(UppercaseModel):
    """
    Physical Stock Ledger Movement: tl_stock_movement
    Immutable historical audit log of every stock transaction (Inward, Outward, Sales, Return)
    across all stages: YARN, GREY_FABRIC, DYED_FABRIC, CUT_PANELS, GARMENTS.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="stock_movements")
    cfyear = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name="stock_movements")
    movement_date = models.DateField(db_index=True, help_text="Stored YMD, Display DMY")
    
    stage = models.CharField(max_length=50, db_index=True, help_text="YARN, GREY_FABRIC, DYED_FABRIC, CUT_PANELS, GARMENTS")
    warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="stock_movements")
    movement_type = models.CharField(max_length=30, choices=StockMovementTypes.CHOICES, db_index=True)
    
    doc_type = models.CharField(max_length=50, help_text="INWARD_GRN, OUTWARD_DC, SALES_INVOICE, SALES_RETURN, SUPPLIER_RETURN")
    doc_number = models.CharField(max_length=50, db_index=True, help_text="Reference document serial")
    
    item_name = models.CharField(max_length=200, help_text="Material name / Count / Fabric name")
    lot_or_batch_no = models.CharField(max_length=60, db_index=True, default="GEN", help_text="Lot / Batch / Roll reference")
    
    # Inward Movements (+)
    in_units = models.IntegerField(default=0, help_text="Bags / Rolls / Pieces IN")
    in_qty = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Weight (Kg) or Count IN")
    
    # Outward Movements (-)
    out_units = models.IntegerField(default=0, help_text="Bags / Rolls / Pieces OUT")
    out_qty = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Weight (Kg) or Count OUT")
    
    # Running Stock Balance after this movement
    balance_units = models.IntegerField(default=0, help_text="Running units on hand")
    balance_qty = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Running quantity (Kg) on hand")
    
    unit_rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"), help_text="Valuation rate per unit")
    total_value = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"), help_text="balance_qty * unit_rate")
    
    party = models.ForeignKey(PartyMaster, on_delete=models.SET_NULL, null=True, blank=True, related_name="stock_movements")
    remarks = models.CharField(max_length=255, blank=True)
    status = models.IntegerField(default=1)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_stock_movements")
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "tl_stock_movement"
        verbose_name = "Stock Ledger Movement"
        verbose_name_plural = "Stock Ledger Movements"
        ordering = ["-movement_date", "-id"]
        indexes = [
            models.Index(fields=["company", "stage", "movement_date"]),
            models.Index(fields=["company", "warehouse", "lot_or_batch_no"]),
            models.Index(fields=["doc_type", "doc_number"]),
        ]

    def __str__(self):
        return f"[{self.stage}] {self.doc_number} ({self.movement_type}) | In: {self.in_qty} | Out: {self.out_qty} | Bal: {self.balance_qty}"


class tm_stage_stock(UppercaseModel):
    """
    Live On-Hand Physical Stock: tm_stage_stock
    Fast-lookup live snapshot per stage + warehouse + item + lot.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="stage_stocks")
    warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="stage_stocks")
    stage = models.CharField(max_length=50, db_index=True, help_text="YARN, GREY_FABRIC, DYED_FABRIC, CUT_PANELS, GARMENTS")
    item_name = models.CharField(max_length=200, db_index=True)
    lot_or_batch_no = models.CharField(max_length=60, db_index=True, default="GEN")
    
    dia = models.CharField(max_length=50, blank=True)
    gsm = models.PositiveIntegerField(default=0)
    
    inward_units = models.IntegerField(default=0)
    inward_qty = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    
    outward_units = models.IntegerField(default=0)
    outward_qty = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    
    balance_units = models.IntegerField(default=0)
    balance_qty = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    
    status = models.IntegerField(default=1)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_stage_stock"
        verbose_name = "Live Stage Stock on Hand"
        verbose_name_plural = "Live Stage Stocks on Hand"
        unique_together = ("company", "warehouse", "stage", "item_name", "lot_or_batch_no")
        indexes = [
            models.Index(fields=["company", "stage", "balance_qty"]),
        ]

    def __str__(self):
        return f"[{self.stage}] {self.item_name} (Lot: {self.lot_or_batch_no}) => {self.balance_qty} Kg ({self.balance_units} units)"

    def recalculate_balance(self):
        self.balance_units = self.inward_units - self.outward_units
        self.balance_qty = self.inward_qty - self.outward_qty


class tl_voucher(UppercaseModel):
    """
    Currency General Ledger Header: tl_voucher
    Double-entry accounting journal voucher recording monetary debit and credit.
    """
    voucher_number = models.CharField(max_length=50, unique=True, db_index=True)
    voucher_date = models.DateField(db_index=True, help_text="Stored YMD, Display DMY")
    voucher_type = models.CharField(max_length=30, choices=VoucherTypes.CHOICES, db_index=True)
    stage = models.CharField(max_length=50, blank=True, help_text="Associated stage: YARN, KNITTING, DYEING, CUTTING")

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="vouchers")
    cfyear = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name="vouchers")
    party = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="vouchers")

    reference_type = models.CharField(max_length=50, blank=True, help_text="INWARD_GRN, TAX_INVOICE, CREDIT_NOTE")
    reference_no = models.CharField(max_length=50, blank=True, help_text="Source doc number")
    reference_id = models.PositiveIntegerField(null=True, blank=True, help_text="Source document PK")

    narration = models.CharField(max_length=500, blank=True)
    total_debit = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    total_credit = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))

    is_posted = models.BooleanField(default=True, db_index=True)
    is_reversed = models.BooleanField(default=False)
    reversed_by = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="reversal_of")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_vouchers")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_vouchers")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tl_voucher"
        verbose_name = "Currency General Ledger Voucher"
        verbose_name_plural = "Currency General Ledger Vouchers"
        ordering = ["-voucher_date", "-id"]
        indexes = [
            models.Index(fields=["company", "voucher_date", "is_posted"]),
            models.Index(fields=["reference_type", "reference_no"]),
            models.Index(fields=["company", "stage"]),
        ]

    def __str__(self):
        return f"{self.voucher_number} [{self.voucher_type}] - INR {self.total_debit} (Balanced: {self.total_debit == self.total_credit})"


class tl_voucher_line(UppercaseModel):
    """
    Currency General Ledger Lines: tl_voucher_line
    Individual Debit and Credit entries.
    Invariant: Sum of all debits = Sum of all credits for any voucher.
    """
    voucher = models.ForeignKey(tl_voucher, on_delete=models.CASCADE, related_name="lines", db_column="voucher_id")
    account_code = models.CharField(max_length=30, db_index=True, help_text="Chart of accounts code, e.g. 1001, 2001, 5001")
    account_name = models.CharField(max_length=150, help_text="e.g. Stock Asset, Knitter Payable, Sales Revenue")
    party = models.ForeignKey(PartyMaster, on_delete=models.SET_NULL, null=True, blank=True, related_name="voucher_lines")

    debit = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"), help_text="Debit (Dr) INR")
    credit = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"), help_text="Credit (Cr) INR")
    narration = models.CharField(max_length=255, blank=True)
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tl_voucher_line"
        verbose_name = "Currency Voucher Line"
        verbose_name_plural = "Currency Voucher Lines"
        indexes = [
            models.Index(fields=["account_code", "voucher"]),
            models.Index(fields=["party", "account_code"]),
        ]

    def __str__(self):
        return f"{self.account_name} ({self.account_code}) | Dr: {self.debit} | Cr: {self.credit}"
