from decimal import Decimal
from django.db import models
from django.conf import settings
from core.base_models import UppercaseModel
from core.constants import YarnCategory, YarnDefectReasons
from apps.authentication.models import Company, FinancialYear
from apps.masters.models import PartyMaster, YarnCountMaster, ColorShadeMaster, WarehouseMaster, TaxMaster


class company_yarn_type_table(UppercaseModel):
    """
    Company-specific Yarn Process / Type Configuration: tc_company_yarn_type
    Allows each tenant company to activate/deactivate specific yarn types
    (e.g., Grey, Dyed, Melange, Blended) and defines conditional field requirements.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="yarn_type_configs")
    yarn_type = models.CharField(max_length=20, choices=YarnCategory.CHOICES, db_index=True)
    display_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True, db_index=True)

    # Dynamic Field Behavior Flags
    requires_color_shade = models.BooleanField(default=False, help_text="True if color shade/lab dip is mandatory (Dyed, Melange)")
    requires_blend_ratio = models.BooleanField(default=False, help_text="True if fiber blend percentage is mandatory (Blended, Melange)")
    requires_ply_twists = models.BooleanField(default=False, help_text="True if ply count and twists per inch are relevant (Wound/TFO)")
    requires_slub_pattern = models.BooleanField(default=False, help_text="True if slub pattern profile is relevant (Slub/Fancy)")
    requires_core_denier = models.BooleanField(default=False, help_text="True if elastane denier is relevant (Core-Spun/Lycra)")

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_yarn_type_configs")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_yarn_type_configs")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tc_company_yarn_type"
        verbose_name = "Company Yarn Type Configuration"
        verbose_name_plural = "Company Yarn Type Configurations"
        unique_together = ("company", "yarn_type")
        ordering = ["yarn_type"]

    def __str__(self):
        return f"{self.company.name} - {self.display_name} ({'Active' if self.is_active else 'Inactive'})"


class parent_po_table(UppercaseModel):
    """
    Primary Header: tm_yarn_po
    Primary document capturing yarn order header, spinning mill details,
    yarn process type (Grey, Dyed, Melange, Blended, etc.), commercial summary, and authorization status.
    """
    po_number = models.CharField(max_length=30, unique=True, db_index=True)
    po_date = models.DateField(db_index=True)
    yarn_type = models.CharField(
        max_length=20,
        choices=YarnCategory.CHOICES,
        default=YarnCategory.GREY,
        db_index=True,
        help_text="Yarn Process Type (Grey, Dyed, Melange, Blended, Wound, Slub, Core-Spun, Recycled)"
    )
    color_shade = models.ForeignKey(
        ColorShadeMaster,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="yarn_pos",
        help_text="Required if yarn_type is DYED or MELANGE"
    )
    blend_ratio = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Fiber blend ratio (e.g. 65/35 PC, 85/15 Melange, 50/50 Cotton Modal)"
    )
    ply_count = models.IntegerField(
        default=1,
        help_text="Ply count (1 for Single, 2 for 2-ply doubled/TFO)"
    )
    twists_per_inch = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="TPI twist specification for wound/twisted yarns"
    )
    slub_pattern = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        help_text="Slub pattern profile code for slub/fancy yarns"
    )
    core_denier = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Core filament denier (e.g. 40D Spandex/Lycra)"
    )
    name = models.CharField(max_length=50, blank=True, null=True, help_text="Order reference name / description")
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="yarn_pos",
        db_column="company_id"
    )
    cfyear = models.ForeignKey(
        FinancialYear,
        on_delete=models.PROTECT,
        related_name="yarn_pos",
        db_column="cfyear",
        help_text="Active Financial Year reference"
    )
    party = models.ForeignKey(
        PartyMaster,
        on_delete=models.PROTECT,
        related_name="yarn_po_parties",
        db_column="party_id",
        help_text="Yarn Supplier / Trader / Agent"
    )
    mill = models.ForeignKey(
        PartyMaster,
        on_delete=models.PROTECT,
        related_name="yarn_po_mills",
        db_column="mill_id",
        help_text="Spinning Mill where yarn is spun"
    )
    yarn_count = models.ForeignKey(
        YarnCountMaster,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="yarn_pos",
        db_column="yarn_count_id",
        help_text="Primary Yarn Count (e.g. 30s Combed, 34s Carded)"
    )
    bag = models.IntegerField(default=0, help_text="Total number of bags ordered")
    per_bag = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("45.360"),
        help_text="Standard weight per bag in Kg (typically 45.360 or 50.000)"
    )
    quantity = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Total Net Quantity in Kg (bag * per_bag)"
    )
    gross_quantity = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        null=True,
        blank=True,
        default=Decimal("0.000"),
        help_text="Gross weight including packing tare"
    )
    rate = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Base rate per Kg"
    )
    discount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Discount per Kg or flat discount"
    )
    net_rate = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Final rate after discount (rate - discount)"
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Total net order value (quantity * net_rate)"
    )
    remarks = models.CharField(max_length=150, blank=True, null=True, help_text="Delivery terms, CSP specs, or payment terms")
    is_delivery = models.IntegerField(default=0, help_text="Flag (0/1): indicates if scheduled split delivery is enabled")
    is_complete = models.IntegerField(default=0, help_text="0 = Pending / In-progress, 1 = Fully received")
    is_authorized = models.IntegerField(default=0, help_text="Approval lock (0 = Draft, 1 = Authorized)")
    authorized_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authorized_yarn_pos",
        db_column="authorized_by"
    )
    authorized_on = models.DateTimeField(null=True, blank=True)
    is_active = models.IntegerField(default=1, help_text="1 = Active, 0 = Inactive")
    status = models.IntegerField(default=1, help_text="Record status (1 = Valid, 0 = Soft Deleted)")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_yarn_pos",
        db_column="created_by"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_yarn_pos",
        db_column="updated_by"
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_yarn_po"
        verbose_name = "Yarn Purchase Order"
        verbose_name_plural = "Yarn Purchase Orders"
        ordering = ["-po_date", "-id"]
        indexes = [
            models.Index(fields=["company", "po_number"]),
            models.Index(fields=["yarn_type", "is_authorized", "is_complete"]),
        ]

    def __str__(self):
        return f"{self.po_number} - {self.mill.name} ({self.get_yarn_type_display()})"

    def clean(self):
        # Calculate quantity, net rate, and total amount
        if self.bag and self.per_bag:
            self.quantity = Decimal(str(self.bag)) * Decimal(str(self.per_bag))
        if self.rate is not None:
            disc = Decimal(str(self.discount or 0))
            self.net_rate = Decimal(str(self.rate)) - disc
        if self.quantity and self.net_rate:
            self.amount = Decimal(str(self.quantity)) * Decimal(str(self.net_rate))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        self.status = 0
        self.is_active = 0
        self.updated_by = user
        self.save(update_fields=["status", "is_active", "updated_by", "updated_on"])
        self.line_items.all().update(status=0, is_active=0)
        self.deliveries.all().update(status=0, is_active=0)



class child_po_table(UppercaseModel):
    """
    Line Items: tx_purchase_order
    Itemized line entries for multi-count yarn purchase orders.
    """
    tm_po = models.ForeignKey(
        parent_po_table,
        on_delete=models.CASCADE,
        related_name="line_items",
        db_column="tm_po_id"
    )
    yarn_type = models.CharField(
        max_length=20,
        choices=YarnCategory.CHOICES,
        default=YarnCategory.GREY,
        help_text="Grey Yarn or Dyed Yarn"
    )
    yarn_count = models.ForeignKey(
        YarnCountMaster,
        on_delete=models.PROTECT,
        related_name="po_line_items",
        db_column="yarn_count_id"
    )
    color_shade = models.ForeignKey(
        ColorShadeMaster,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="po_line_items",
        db_column="color_shade_id",
        help_text="Color shade if Dyed or Melange Yarn"
    )
    blend_ratio = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Fiber blend ratio (e.g. 65/35 PC, 85/15 Melange)"
    )
    ply_count = models.IntegerField(
        default=1,
        help_text="Ply count (1 for Single, 2 for 2-ply doubled/TFO)"
    )
    twists_per_inch = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="TPI twist specification for wound/twisted yarns"
    )
    slub_pattern = models.CharField(
        max_length=60,
        blank=True,
        null=True,
        help_text="Slub pattern profile code for slub/fancy yarns"
    )
    core_denier = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        help_text="Core filament denier (e.g. 40D Spandex/Lycra)"
    )
    bag = models.IntegerField(default=0, help_text="Number of bags ordered for this count")
    per_bag = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("45.360"),
        help_text="Weight per bag in Kg"
    )
    quantity = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Total Net Quantity (bag * per_bag)"
    )
    gross_wt = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        null=True,
        blank=True,
        default=Decimal("0.000"),
        help_text="Gross weight"
    )
    actual_rate = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Mill catalogue / base rate per Kg"
    )
    discount = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Discount per Kg"
    )
    rate = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Effective rate per Kg (actual_rate - discount)"
    )
    amount = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Line item total (quantity * rate)"
    )
    remaining_bag = models.IntegerField(default=0, help_text="Pending unreceived bags")
    remaining_quantity = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Pending unreceived weight (Kg)"
    )
    remaining_amount = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Pending commercial liability"
    )
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_purchase_order"
        verbose_name = "Yarn PO Line Item"
        verbose_name_plural = "Yarn PO Line Items"

    def __str__(self):
        return f"PO #{self.tm_po.po_number} - {self.yarn_count.count} ({self.get_yarn_type_display()})"

    def clean(self):
        if self.bag and self.per_bag:
            self.quantity = Decimal(str(self.bag)) * Decimal(str(self.per_bag))
        if self.actual_rate is not None:
            disc = Decimal(str(self.discount or 0))
            self.rate = Decimal(str(self.actual_rate)) - disc
        if self.quantity and self.rate:
            self.amount = Decimal(str(self.quantity)) * Decimal(str(self.rate))
        # Initial remaining matches order if newly created
        if not self.pk:
            if not self.remaining_bag:
                self.remaining_bag = self.bag
            if not self.remaining_quantity:
                self.remaining_quantity = self.quantity
            if not self.remaining_amount:
                self.remaining_amount = self.amount

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class yarn_po_delivery_table(UppercaseModel):
    """
    Split Delivery Schedule: tx_yarn_po
    Schedule for multi-lot split deliveries and direct dispatches to knitting mills or warehouses.
    """
    tm_po = models.ForeignKey(
        parent_po_table,
        on_delete=models.CASCADE,
        related_name="deliveries",
        db_column="tm_po_id"
    )
    yarn_count = models.ForeignKey(
        YarnCountMaster,
        on_delete=models.PROTECT,
        related_name="po_deliveries",
        db_column="yarn_count_id"
    )
    party = models.ForeignKey(
        PartyMaster,
        on_delete=models.PROTECT,
        related_name="po_deliveries",
        db_column="party_id",
        help_text="Destination Party (Knitting Mill or Own Warehouse)"
    )
    delivery_date = models.DateField(help_text="Expected arrival date")
    bag = models.IntegerField(default=0, help_text="Scheduled bag count")
    bag_wt = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("45.360"),
        help_text="Weight per bag (Kg)"
    )
    quantity = models.DecimalField(
        max_digits=20,
        decimal_places=3,
        default=Decimal("0.000"),
        help_text="Scheduled quantity (bag * bag_wt)"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="po_deliveries",
        db_column="company_id"
    )
    cfyear = models.ForeignKey(
        FinancialYear,
        on_delete=models.PROTECT,
        related_name="po_deliveries",
        db_column="cfyear"
    )
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_yarn_po"
        verbose_name = "Yarn PO Delivery Schedule"
        verbose_name_plural = "Yarn PO Delivery Schedules"
        ordering = ["delivery_date", "id"]

    def __str__(self):
        return f"PO #{self.tm_po.po_number} -> {self.party.name} on {self.delivery_date} ({self.bag} bags)"

    def clean(self):
        if self.bag and self.bag_wt:
            self.quantity = Decimal(str(self.bag)) * Decimal(str(self.bag_wt))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


# =========================================================================
# Yarn PO Return (Vendor Rejection Outward & Mill Debit Note)
# =========================================================================

class parent_yarn_po_return_table(UppercaseModel):
    """
    Yarn PO Return & Debit Note Header: tm_yarn_po_return
    Outward rejection dispatch of defective/substandard yarn back to the spinning mill,
    accompanied by an Accounts Payable Debit Note.
    Atomically decrements Yarn Stock and creates balanced Debit Note in accounting.
    """
    return_number = models.CharField(max_length=30, unique=True, db_index=True)
    return_date = models.DateField(db_index=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="yarn_po_returns")
    cfyear = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name="yarn_po_returns")
    party = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="yarn_po_returns", help_text="Spinning Mill / Supplier")
    po = models.ForeignKey(parent_po_table, on_delete=models.SET_NULL, null=True, blank=True, related_name="po_returns", help_text="Source Yarn PO")
    inward = models.ForeignKey('inventory.parent_yarn_inward_table', on_delete=models.SET_NULL, null=True, blank=True, related_name="po_returns", help_text="Source Inward GRN")
    warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="yarn_po_returns", help_text="Source Godown")

    yarn_type = models.CharField(max_length=20, choices=YarnCategory.CHOICES, default=YarnCategory.GREY, db_index=True)
    yarn_count = models.ForeignKey(YarnCountMaster, on_delete=models.PROTECT, related_name="yarn_po_returns")
    color_shade = models.ForeignKey(ColorShadeMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="yarn_po_returns")
    lot_no = models.CharField(max_length=50, default="GEN", db_index=True)

    defect_reason = models.CharField(max_length=50, choices=YarnDefectReasons.CHOICES, default=YarnDefectReasons.LOW_CSP, db_index=True)
    defect_notes = models.TextField(blank=True, null=True, help_text="Lab test metrics / QC inspection findings")

    bag = models.IntegerField(default=0)
    per_bag = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("45.360"))
    quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Returned Net Weight (Kg)")

    rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"), help_text="Debit rate per Kg")
    subtotal = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Taxable amount before GST")
    tax = models.ForeignKey(TaxMaster, on_delete=models.SET_NULL, null=True, blank=True, related_name="yarn_po_returns")
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("5.00"), help_text="GST Reversal %")
    tax_amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    cgst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("2.50"))
    cgst_amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    sgst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("2.50"))
    sgst_amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    igst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    igst_amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    total_debit_amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Total Debit Note Value")

    transporter_name = models.CharField(max_length=100, blank=True)
    vehicle_no = models.CharField(max_length=30, blank=True)
    lr_number = models.CharField(max_length=50, blank=True, help_text="Lorry Receipt / Bilty No")

    debit_note_number = models.CharField(max_length=50, blank=True, null=True, help_text="Statutory Debit Note Number")
    voucher_id = models.BigIntegerField(null=True, blank=True, help_text="Linked tl_voucher ID")

    is_authorized = models.IntegerField(default=1)
    status = models.IntegerField(default=1)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_yarn_po_returns")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_yarn_po_returns")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_yarn_po_return"
        verbose_name = "Yarn PO Return"
        verbose_name_plural = "Yarn PO Returns"
        ordering = ["-return_date", "-id"]

    def __str__(self):
        return f"{self.return_number} -> {self.party.name} ({self.quantity} Kg) [{self.get_defect_reason_display()}]"

    def clean(self):
        if self.bag and self.per_bag and not self.quantity:
            self.quantity = Decimal(str(self.bag)) * Decimal(str(self.per_bag))
        if self.quantity and self.rate:
            self.subtotal = self.quantity * Decimal(str(self.rate))
            tax_p = Decimal(str(self.tax_percent or 0)) / Decimal("100.00")
            self.tax_amount = self.subtotal * tax_p
            self.total_debit_amount = self.subtotal + self.tax_amount

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        self.status = 0
        self.updated_by = user
        self.save(update_fields=["status", "updated_by", "updated_on"])
        self.line_items.all().update(status=0)


class child_yarn_po_return_table(UppercaseModel):
    """
    Line Items: tx_yarn_po_return
    Itemized counts, lots, and weights returned under a Yarn PO Return document.
    """
    tm_return = models.ForeignKey(parent_yarn_po_return_table, on_delete=models.CASCADE, related_name="line_items", db_column="tm_return_id")
    yarn_count = models.ForeignKey(YarnCountMaster, on_delete=models.PROTECT, related_name="po_return_line_items")
    color_shade = models.ForeignKey(ColorShadeMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="po_return_line_items")
    lot_no = models.CharField(max_length=50, default="GEN")
    bag = models.IntegerField(default=0)
    per_bag = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("45.360"))
    quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_yarn_po_return"
        verbose_name = "Yarn PO Return Line Item"
        verbose_name_plural = "Yarn PO Return Line Items"

    def clean(self):
        if self.bag and self.per_bag and not self.quantity:
            self.quantity = Decimal(str(self.bag)) * Decimal(str(self.per_bag))
        if self.quantity and self.rate:
            self.amount = self.quantity * Decimal(str(self.rate))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


# =========================================================================
# PO Balance & Tracking Unmanaged Database Views
# =========================================================================

class yarn_po_balance_table(models.Model):
    """
    Unmanaged View: yarn_po_balance
    Tracks ordered vs inward received bags and remaining quantities.
    Formula: Balance Quantity = PO Quantity - Total Inward Quantity
    """
    po_id = models.BigIntegerField(primary_key=True)
    po_number = models.CharField(max_length=30)
    yarn_type = models.CharField(max_length=20)
    yarn_count_id = models.IntegerField()
    party_id = models.IntegerField()
    ord_bags = models.IntegerField()
    po_quantity = models.DecimalField(max_digits=20, decimal_places=3)
    in_bag = models.IntegerField(default=0)
    in_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=0)
    balance_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=0)

    class Meta:
        managed = False
        db_table = "yarn_po_balance"
        verbose_name = "Yarn PO Balance"
        verbose_name_plural = "Yarn PO Balances"


class yarn_po_sum_table(models.Model):
    """
    Unmanaged View: yarn_po_sum
    Aggregates ordered vs received bags and weights per PO and Yarn Count.
    """
    tm_po_id = models.BigIntegerField(primary_key=True)
    yarn_count_id = models.IntegerField()
    yarn_type = models.CharField(max_length=20)
    total_ordered_bags = models.IntegerField()
    total_ordered_quantity = models.DecimalField(max_digits=20, decimal_places=3)
    total_received_bags = models.IntegerField(default=0)
    total_received_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=0)

    class Meta:
        managed = False
        db_table = "yarn_po_sum"
        verbose_name = "Yarn PO Summary"
        verbose_name_plural = "Yarn PO Summaries"


class yarn_po_delivery_sum_table(models.Model):
    """
    Unmanaged View: y_po_sum
    Summary of scheduled deliveries per destination party.
    """
    tm_po_id = models.BigIntegerField(primary_key=True)
    party_id = models.IntegerField()
    destination_name = models.CharField(max_length=255)
    total_delivery_bags = models.IntegerField()
    total_delivery_quantity = models.DecimalField(max_digits=20, decimal_places=3)

    class Meta:
        managed = False
        db_table = "y_po_sum"
        verbose_name = "Yarn PO Delivery Summary"
        verbose_name_plural = "Yarn PO Delivery Summaries"
