from __future__ import annotations
from decimal import Decimal
from django.db import models
from django.conf import settings
from core.base_models import UppercaseModel
from core.constants import (
    YarnCategory,
    KnittingProgramStatus,
    GreyFabricInwardSources,
    GreyFabricOutwardTypes,
)
from apps.authentication.models import Company, FinancialYear
from apps.masters.models import (
    PartyMaster,
    YarnCountMaster,
    ColorShadeMaster,
    FabricMaster,
    FabricTypeMaster,
    WarehouseMaster,
)


class parent_knitting_program_table(UppercaseModel):
    """
    Knitting Program / Job Card: tm_knitting_program
    Plans fabric manufacturing job-work: specifies target fabric specifications
    (Dia, Gauge, GSM, Loop length), required yarn composition, planned loss %,
    and tracks actual issued yarn vs received fabric.
    """
    program_number = models.CharField(max_length=30, unique=True, db_index=True)
    program_date = models.DateField(db_index=True)
    delivery_date = models.DateField(null=True, blank=True)

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="knitting_programs")
    cfyear = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name="knitting_programs")
    knitter = models.ForeignKey(
        PartyMaster,
        on_delete=models.PROTECT,
        related_name="knitting_programs",
        help_text="Knitting Job Work Unit"
    )
    warehouse = models.ForeignKey(
        WarehouseMaster,
        on_delete=models.PROTECT,
        related_name="knitting_programs",
        help_text="Designated receiving warehouse"
    )

    fabric = models.ForeignKey(FabricMaster, on_delete=models.PROTECT, related_name="knitting_programs")
    fabric_type = models.ForeignKey(FabricTypeMaster, on_delete=models.PROTECT, related_name="knitting_programs")

    dia = models.CharField(max_length=50, blank=True, help_text="Diameter / Width in inches (e.g. 24, 30)")
    gauge = models.CharField(max_length=50, blank=True, help_text="Machine Gauge (e.g. 24GG, 28GG)")
    gsm = models.PositiveIntegerField(default=0, help_text="Grams per Square Meter")
    loop_length = models.CharField(max_length=50, blank=True, help_text="Loop length / Stitch length (e.g. 2.70)")

    planned_rolls = models.IntegerField(default=0, help_text="Planned roll count")
    planned_fabric_quantity = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Target finished fabric output (Kg)"
    )
    expected_loss_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("2.00"),
        help_text="Expected knitting process loss %"
    )
    total_yarn_required = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Total calculated required yarn (Kg) including loss"
    )

    issued_yarn_quantity = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Actual dispatched yarn to knitter (Kg)"
    )
    received_fabric_quantity = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Actual net fabric received from knitter (Kg)"
    )

    knitting_rate = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Knitting job work rate per Kg"
    )
    total_knitting_amount = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Estimated total job work amount"
    )

    status = models.IntegerField(
        choices=KnittingProgramStatus.CHOICES,
        default=KnittingProgramStatus.DRAFT,
        db_index=True
    )
    remarks = models.CharField(max_length=255, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_knitting_programs")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_knitting_programs")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_knitting_program"
        verbose_name = "Knitting Program"
        verbose_name_plural = "Knitting Programs"
        ordering = ["-program_date", "-id"]

    def __str__(self):
        return f"{self.program_number} - {self.fabric.fabric_name} ({self.planned_fabric_quantity} Kg)"

    def clean(self):
        if self.planned_fabric_quantity is not None and self.planned_fabric_quantity != "":
            planned_qty = Decimal(str(self.planned_fabric_quantity))
            loss_pct = Decimal(str(self.expected_loss_percent or 0))
            if loss_pct < Decimal("100.00"):
                multiplier = Decimal("1.000") + (loss_pct / Decimal("100.00"))
                self.total_yarn_required = (planned_qty * multiplier).quantize(Decimal("0.001"))
            else:
                self.total_yarn_required = planned_qty
            if self.knitting_rate:
                self.total_knitting_amount = (planned_qty * Decimal(str(self.knitting_rate))).quantize(Decimal("0.001"))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        self.status = KnittingProgramStatus.CANCELLED
        self.updated_by = user
        self.save(update_fields=["status", "updated_by", "updated_on"])
        self.yarn_lines.all().update(status=0)


class child_knitting_program_yarn_table(UppercaseModel):
    """
    Yarn Requirement Lines: tx_knitting_program_yarn
    Itemizes specific counts, shades, blend ratios, and planned weights
    required for the knitting program.
    """
    tm_program = models.ForeignKey(
        parent_knitting_program_table,
        on_delete=models.CASCADE,
        related_name="yarn_lines",
        db_column="tm_program_id"
    )
    yarn_count = models.ForeignKey(YarnCountMaster, on_delete=models.PROTECT, related_name="knitting_yarn_lines")
    color_shade = models.ForeignKey(ColorShadeMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="knitting_yarn_lines")
    yarn_type = models.CharField(max_length=20, choices=YarnCategory.CHOICES, default=YarnCategory.GREY)
    blend_ratio_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("100.00"), help_text="Blend / Feeder %")
    planned_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Yarn required (Kg)")
    issued_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Yarn issued so far (Kg)")
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_knitting_program_yarn"
        verbose_name = "Knitting Program Yarn Requirement"
        verbose_name_plural = "Knitting Program Yarn Requirements"

    def __str__(self):
        return f"{self.yarn_count.count} - {self.blend_ratio_percent}% ({self.planned_quantity} Kg)"


class grey_fabric_stock_table(models.Model):
    """
    Live Grey Fabric Stock Ledger: tm_grey_fabric_stock
    Tracks rolls and net weight balances per company, warehouse, fabric SKU,
    dia, gsm, gauge, and lot/batch number.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="grey_fabric_stocks")
    warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="grey_fabric_stocks")
    fabric = models.ForeignKey(FabricMaster, on_delete=models.PROTECT, related_name="grey_fabric_stocks")
    fabric_type = models.ForeignKey(FabricTypeMaster, on_delete=models.PROTECT, related_name="grey_fabric_stocks")

    dia = models.CharField(max_length=50, default="GEN", db_index=True)
    gsm = models.PositiveIntegerField(default=0, db_index=True)
    gauge = models.CharField(max_length=50, blank=True)
    lot_no = models.CharField(max_length=50, default="GEN", db_index=True)

    # Inward (from Knitting GRN or Grey PO)
    inward_rolls = models.IntegerField(default=0)
    inward_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    # Outward (dispatched to Dyeing or returned to knitter)
    outward_rolls = models.IntegerField(default=0)
    outward_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    # Commercial Sales
    sales_rolls = models.IntegerField(default=0)
    sales_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    # Sales Return
    sales_return_rolls = models.IntegerField(default=0)
    sales_return_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    # Live Balance
    balance_rolls = models.IntegerField(default=0, db_index=True)
    balance_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), db_index=True)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_grey_fabric_stock"
        verbose_name = "Grey Fabric Stock"
        verbose_name_plural = "Grey Fabric Stocks"
        unique_together = ("company", "warehouse", "fabric", "dia", "gsm", "gauge", "lot_no")
        indexes = [
            models.Index(fields=["company", "fabric", "dia", "gsm"]),
            models.Index(fields=["balance_quantity", "balance_rolls"]),
        ]

    def __str__(self):
        return f"{self.fabric.fabric_name} | Dia: {self.dia} GSM: {self.gsm} | Bal: {self.balance_rolls} Rolls, {self.balance_quantity} Kg"

    def recalculate_balance(self):
        """Recompute current balance: Inward - Outward - Sales + Sales Return"""
        self.balance_rolls = (self.inward_rolls + self.sales_return_rolls) - (self.outward_rolls + self.sales_rolls)
        self.balance_quantity = (self.inward_quantity + self.sales_return_quantity) - (self.outward_quantity + self.sales_quantity)


class parent_grey_fabric_inward_table(UppercaseModel):
    """
    Grey Fabric Inward (GRN): tm_grey_fabric_inward
    Captures inward receipt of knitted rolls from Knitter (Job Work)
    or direct procurement from Trader (Grey Fabric PO).
    Increments Grey Fabric Stock atomically.
    """
    inward_number = models.CharField(max_length=30, unique=True, db_index=True)
    inward_date = models.DateField(db_index=True)
    dc_number = models.CharField(max_length=50, help_text="Delivery Challan / Invoice No from Knitter/Trader")
    dc_date = models.DateField()
    vehicle_no = models.CharField(max_length=30, blank=True)

    inward_source = models.CharField(
        max_length=20,
        choices=GreyFabricInwardSources.CHOICES,
        default=GreyFabricInwardSources.KNITTING,
        db_index=True
    )
    knitting_program = models.ForeignKey(
        parent_knitting_program_table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inwards",
        db_column="knitting_program_id",
        help_text="Associated Knitting Program"
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="grey_fabric_inwards")
    cfyear = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name="grey_fabric_inwards")
    party = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="grey_fabric_inwards", help_text="Knitter or Trader")
    warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="grey_fabric_inwards")

    fabric = models.ForeignKey(FabricMaster, on_delete=models.PROTECT, related_name="grey_fabric_inwards")
    fabric_type = models.ForeignKey(FabricTypeMaster, on_delete=models.PROTECT, related_name="grey_fabric_inwards")

    dia = models.CharField(max_length=50, blank=True)
    gsm = models.PositiveIntegerField(default=0)
    gauge = models.CharField(max_length=50, blank=True)
    lot_no = models.CharField(max_length=50, default="GEN", db_index=True)

    total_rolls = models.IntegerField(default=0)
    gross_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    tare_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    net_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Net Weight in Kg")

    # Knitting Process Loss & Job Work Charges
    yarn_consumed_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Input yarn weight consumed")
    process_loss_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Knitting process loss in Kg")
    process_loss_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), help_text="Knitting process loss %")

    knitting_rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"), help_text="Knitting job work rate per Kg")
    knitting_charges = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Total job work charges")

    remarks = models.CharField(max_length=200, blank=True)
    is_authorized = models.IntegerField(default=1, help_text="1 = Authorized & stock posted, 0 = Draft")
    status = models.IntegerField(default=1)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_grey_fabric_inwards")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_grey_fabric_inwards")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_grey_fabric_inward"
        verbose_name = "Grey Fabric Inward"
        verbose_name_plural = "Grey Fabric Inwards"
        ordering = ["-inward_date", "-id"]

    def __str__(self):
        return f"{self.inward_number} - {self.party.name} ({self.total_rolls} Rolls, {self.net_wt} Kg)"

    def clean(self):
        gross = Decimal(str(self.gross_wt or 0))
        tare = Decimal(str(self.tare_wt or 0))
        if gross and tare and not self.net_wt:
            self.net_wt = gross - tare
        consumed = Decimal(str(self.yarn_consumed_wt or 0))
        net = Decimal(str(self.net_wt or 0))
        if consumed and net:
            if consumed >= net:
                self.process_loss_wt = consumed - net
                self.process_loss_percent = ((self.process_loss_wt / consumed) * Decimal("100.00")).quantize(Decimal("0.01"))
        if net and self.knitting_rate and not self.knitting_charges:
            self.knitting_charges = (net * Decimal(str(self.knitting_rate))).quantize(Decimal("0.001"))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        self.status = 0
        self.updated_by = user
        self.save(update_fields=["status", "updated_by", "updated_on"])
        self.line_items.all().update(status=0)


class child_grey_fabric_inward_table(UppercaseModel):
    """
    Rolls / Pieces received under Grey Fabric Inward: tx_grey_fabric_inward
    """
    tm_inward = models.ForeignKey(
        parent_grey_fabric_inward_table,
        on_delete=models.CASCADE,
        related_name="line_items",
        db_column="tm_inward_id"
    )
    roll_no = models.CharField(max_length=50, blank=True)
    gross_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    tare_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    net_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    remarks = models.CharField(max_length=150, blank=True)
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_grey_fabric_inward"
        verbose_name = "Grey Fabric Inward Roll Item"
        verbose_name_plural = "Grey Fabric Inward Roll Items"

    def clean(self):
        if self.gross_wt and self.tare_wt and not self.net_wt:
            self.net_wt = self.gross_wt - self.tare_wt

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class parent_grey_fabric_outward_table(UppercaseModel):
    """
    Grey Fabric Outward: tm_grey_fabric_outward
    Dispatches grey fabric rolls from Godown:
      1. DYEING: Dispatched to Dyeing / Processing Unit for coloration & finishing.
      2. RETURN: Dispatched back to Knitter / Trader for defect or rejection.
    Deducts stock atomically upon authorization.
    """
    outward_number = models.CharField(max_length=30, unique=True, db_index=True)
    outward_date = models.DateField(db_index=True)
    outward_type = models.CharField(
        max_length=30,
        choices=GreyFabricOutwardTypes.CHOICES,
        default=GreyFabricOutwardTypes.DYEING,
        db_index=True
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="grey_fabric_outwards")
    cfyear = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name="grey_fabric_outwards")
    warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="grey_fabric_outwards")
    destination_party = models.ForeignKey(
        PartyMaster,
        on_delete=models.PROTECT,
        related_name="grey_fabric_outward_destinations",
        help_text="Dyeing Unit / Knitter for Return"
    )

    fabric = models.ForeignKey(FabricMaster, on_delete=models.PROTECT, related_name="grey_fabric_outwards")
    fabric_type = models.ForeignKey(FabricTypeMaster, on_delete=models.PROTECT, related_name="grey_fabric_outwards")

    dia = models.CharField(max_length=50, blank=True)
    gsm = models.PositiveIntegerField(default=0)
    gauge = models.CharField(max_length=50, blank=True)
    lot_no = models.CharField(max_length=50, default="GEN")

    rolls = models.IntegerField(default=0, help_text="Total Outward Rolls")
    quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Total Outward Net Weight (Kg)")
    received_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Received weight from dyeing (Kg)")
    remaining_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Pending weight at dyeing processor (Kg)")
    is_complete = models.IntegerField(default=0, help_text="0 = In-progress at processor, 1 = Fully received / completed")

    vehicle_no = models.CharField(max_length=30, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    remarks = models.CharField(max_length=200, blank=True)
    is_authorized = models.IntegerField(default=1)
    status = models.IntegerField(default=1)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_grey_fabric_outwards")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_grey_fabric_outwards")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_grey_fabric_outward"
        verbose_name = "Grey Fabric Outward"
        verbose_name_plural = "Grey Fabric Outwards"
        ordering = ["-outward_date", "-id"]

    def __str__(self):
        return f"{self.outward_number} [{self.get_outward_type_display()}] -> {self.destination_party.name} ({self.rolls} Rolls, {self.quantity} Kg)"

    def clean(self):
        if not self.pk and not self.remaining_quantity:
            self.remaining_quantity = self.quantity

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        self.status = 0
        self.updated_by = user
        self.save(update_fields=["status", "updated_by", "updated_on"])
        self.line_items.all().update(status=0)


class child_grey_fabric_outward_table(UppercaseModel):
    """
    Rolls itemized in Grey Fabric Outward DC: tx_grey_fabric_outward
    """
    tm_outward = models.ForeignKey(
        parent_grey_fabric_outward_table,
        on_delete=models.CASCADE,
        related_name="line_items",
        db_column="tm_outward_id"
    )
    roll_no = models.CharField(max_length=50, blank=True)
    gross_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    net_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    remarks = models.CharField(max_length=150, blank=True)
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_grey_fabric_outward"
        verbose_name = "Grey Fabric Outward Roll Item"
        verbose_name_plural = "Grey Fabric Outward Roll Items"


class parent_grey_po_table(UppercaseModel):
    """
    Grey Fabric Purchase Order: tm_grey_po
    For procurement of Grey Fabric directly from a Trader or Fabric Mill.
    """
    po_number = models.CharField(max_length=30, unique=True, db_index=True)
    po_date = models.DateField(db_index=True)
    delivery_date = models.DateField(null=True, blank=True)

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="grey_pos")
    cfyear = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name="grey_pos")
    party = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="grey_pos", help_text="Trader / Fabric Supplier")
    warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="grey_pos")

    total_rolls = models.IntegerField(default=0)
    total_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Total Weight (Kg)")
    subtotal = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("5.00"))
    tax_amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    total_amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    is_authorized = models.IntegerField(default=0, help_text="0 = Draft, 1 = Authorized")
    status = models.IntegerField(default=1)
    remarks = models.CharField(max_length=255, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_grey_pos")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_grey_pos")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_grey_po"
        verbose_name = "Grey Fabric Purchase Order"
        verbose_name_plural = "Grey Fabric Purchase Orders"
        ordering = ["-po_date", "-id"]

    def __str__(self):
        return f"{self.po_number} - {self.party.name} ({self.total_quantity} Kg)"

    def soft_delete(self, user=None):
        self.status = 0
        self.updated_by = user
        self.save(update_fields=["status", "updated_by", "updated_on"])
        self.line_items.all().update(status=0)


class child_grey_po_table(UppercaseModel):
    """
    Line Items: tx_grey_po
    """
    tm_po = models.ForeignKey(parent_grey_po_table, on_delete=models.CASCADE, related_name="line_items", db_column="tm_po_id")
    fabric = models.ForeignKey(FabricMaster, on_delete=models.PROTECT, related_name="grey_po_line_items")
    fabric_type = models.ForeignKey(FabricTypeMaster, on_delete=models.PROTECT, related_name="grey_po_line_items")
    dia = models.CharField(max_length=50, blank=True)
    gsm = models.PositiveIntegerField(default=0)
    gauge = models.CharField(max_length=50, blank=True)
    rolls = models.IntegerField(default=0)
    quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_grey_po"
        verbose_name = "Grey Fabric PO Line Item"
        verbose_name_plural = "Grey Fabric PO Line Items"

    def clean(self):
        if self.quantity and self.rate:
            self.amount = (self.quantity * Decimal(str(self.rate))).quantize(Decimal("0.001"))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class parent_grey_fabric_sales_table(UppercaseModel):
    """
    Grey Fabric Commercial Sales: tm_grey_fabric_sales
    Invoice document for commercial sale of Grey Fabric rolls from Godown.
    Deducts Grey Fabric stock atomically upon authorization.
    """
    invoice_number = models.CharField(max_length=30, unique=True, db_index=True)
    invoice_date = models.DateField(db_index=True)

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="grey_fabric_sales")
    cfyear = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name="grey_fabric_sales")
    warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="grey_fabric_sales")
    customer = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="grey_fabric_sales_customers", help_text="Buyer / Customer")

    fabric = models.ForeignKey(FabricMaster, on_delete=models.PROTECT, related_name="grey_fabric_sales")
    fabric_type = models.ForeignKey(FabricTypeMaster, on_delete=models.PROTECT, related_name="grey_fabric_sales")

    dia = models.CharField(max_length=50, blank=True)
    gsm = models.PositiveIntegerField(default=0)
    gauge = models.CharField(max_length=50, blank=True)
    lot_no = models.CharField(max_length=50, default="GEN")

    rolls = models.IntegerField(default=0, help_text="Total Sold Rolls")
    quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Net sold weight (Kg)")

    rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"), help_text="Sale rate per Kg")
    subtotal = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("5.00"), help_text="GST %")
    tax_amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    total_amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    payment_terms = models.CharField(max_length=100, blank=True)
    remarks = models.CharField(max_length=200, blank=True)
    is_authorized = models.IntegerField(default=1)
    status = models.IntegerField(default=1)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_grey_fabric_sales")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_grey_fabric_sales")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_grey_fabric_sales"
        verbose_name = "Grey Fabric Sales"
        verbose_name_plural = "Grey Fabric Sales"
        ordering = ["-invoice_date", "-id"]

    def __str__(self):
        return f"{self.invoice_number} -> {self.customer.name} ({self.rolls} Rolls, {self.quantity} Kg)"

    def clean(self):
        if self.quantity and self.rate:
            qty = Decimal(str(self.quantity))
            r = Decimal(str(self.rate))
            self.subtotal = (qty * r).quantize(Decimal("0.001"))
            tax_p = Decimal(str(self.tax_percent or 0)) / Decimal("100.00")
            self.tax_amount = (self.subtotal * tax_p).quantize(Decimal("0.001"))
            self.total_amount = self.subtotal + self.tax_amount

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        self.status = 0
        self.updated_by = user
        self.save(update_fields=["status", "updated_by", "updated_on"])
        self.line_items.all().update(status=0)


class child_grey_fabric_sales_table(UppercaseModel):
    """
    Line Items: tx_grey_fabric_sales
    """
    tm_sales = models.ForeignKey(parent_grey_fabric_sales_table, on_delete=models.CASCADE, related_name="line_items", db_column="tm_sales_id")
    roll_no = models.CharField(max_length=50, blank=True)
    gross_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    net_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    remarks = models.CharField(max_length=150, blank=True)
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_grey_fabric_sales"
        verbose_name = "Grey Fabric Sales Line Item"
        verbose_name_plural = "Grey Fabric Sales Line Items"

    def clean(self):
        if self.net_wt and self.rate:
            self.amount = (Decimal(str(self.net_wt)) * Decimal(str(self.rate))).quantize(Decimal("0.001"))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class parent_grey_fabric_sales_return_table(UppercaseModel):
    """
    Customer Grey Fabric Sales Return: tm_grey_fabric_sales_return
    Accepts returned grey fabric rolls back from customer and re-credits Godown Stock.
    """
    return_number = models.CharField(max_length=30, unique=True, db_index=True)
    return_date = models.DateField(db_index=True)
    sales_invoice = models.ForeignKey(
        parent_grey_fabric_sales_table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="returns",
        db_column="sales_invoice_id"
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="grey_fabric_sales_returns")
    cfyear = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name="grey_fabric_sales_returns")
    warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="grey_fabric_sales_returns")
    customer = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="grey_fabric_sales_return_customers", help_text="Customer returning fabric")

    fabric = models.ForeignKey(FabricMaster, on_delete=models.PROTECT, related_name="grey_fabric_sales_returns")
    fabric_type = models.ForeignKey(FabricTypeMaster, on_delete=models.PROTECT, related_name="grey_fabric_sales_returns")

    dia = models.CharField(max_length=50, blank=True)
    gsm = models.PositiveIntegerField(default=0)
    gauge = models.CharField(max_length=50, blank=True)
    lot_no = models.CharField(max_length=50, default="GEN")

    rolls = models.IntegerField(default=0, help_text="Total Returned Rolls")
    quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Returned Net Weight (Kg)")

    rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    subtotal = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("5.00"))
    tax_amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    total_amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    return_reason = models.CharField(max_length=255, blank=True)
    remarks = models.CharField(max_length=200, blank=True)
    is_authorized = models.IntegerField(default=1)
    status = models.IntegerField(default=1)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_grey_fabric_sales_returns")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_grey_fabric_sales_returns")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_grey_fabric_sales_return"
        verbose_name = "Grey Fabric Sales Return"
        verbose_name_plural = "Grey Fabric Sales Returns"
        ordering = ["-return_date", "-id"]

    def __str__(self):
        return f"{self.return_number} <- {self.customer.name} ({self.rolls} Rolls, {self.quantity} Kg)"

    def clean(self):
        if self.quantity and self.rate:
            qty = Decimal(str(self.quantity))
            r = Decimal(str(self.rate))
            self.subtotal = (qty * r).quantize(Decimal("0.001"))
            tax_p = Decimal(str(self.tax_percent or 0)) / Decimal("100.00")
            self.tax_amount = (self.subtotal * tax_p).quantize(Decimal("0.001"))
            self.total_amount = self.subtotal + self.tax_amount

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        self.status = 0
        self.updated_by = user
        self.save(update_fields=["status", "updated_by", "updated_on"])
        self.line_items.all().update(status=0)


class child_grey_fabric_sales_return_table(UppercaseModel):
    """
    Line Items: tx_grey_fabric_sales_return
    """
    tm_return = models.ForeignKey(parent_grey_fabric_sales_return_table, on_delete=models.CASCADE, related_name="line_items", db_column="tm_return_id")
    roll_no = models.CharField(max_length=50, blank=True)
    gross_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    net_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    remarks = models.CharField(max_length=150, blank=True)
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_grey_fabric_sales_return"
        verbose_name = "Grey Fabric Sales Return Line Item"
        verbose_name_plural = "Grey Fabric Sales Return Line Items"

    def clean(self):
        if self.net_wt and self.rate:
            self.amount = (Decimal(str(self.net_wt)) * Decimal(str(self.rate))).quantize(Decimal("0.001"))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

