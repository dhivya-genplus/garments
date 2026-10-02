from __future__ import annotations
from decimal import Decimal
from django.db import models
from django.conf import settings
from core.base_models import UppercaseModel
from core.constants import YarnCategory, YarnOutwardTypes
from apps.authentication.models import Company, FinancialYear
from apps.masters.models import PartyMaster, YarnCountMaster, ColorShadeMaster, WarehouseMaster
from apps.purchase.models import parent_po_table


class yarn_stock_table(models.Model):
    """
    Live Yarn Stock Ledger: tm_yarn_stock
    Maintains real-time stock balances per company, warehouse, yarn type (Grey/Dyed),
    count, mill, color shade, and lot number.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="yarn_stocks")
    warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="yarn_stocks")
    yarn_type = models.CharField(max_length=20, choices=YarnCategory.CHOICES, default=YarnCategory.GREY, db_index=True)
    yarn_count = models.ForeignKey(YarnCountMaster, on_delete=models.PROTECT, related_name="yarn_stocks")
    mill = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="yarn_stocks", help_text="Spinning Mill")
    color_shade = models.ForeignKey(ColorShadeMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="yarn_stocks")
    lot_no = models.CharField(max_length=50, default="GEN", db_index=True)

    # Inward
    inward_bag = models.IntegerField(default=0)
    inward_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    # Outward (Knitting / Dyeing / Purchase Return)
    outward_bag = models.IntegerField(default=0)
    outward_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    # Sales
    sales_bag = models.IntegerField(default=0)
    sales_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    # Sales Return
    sales_return_bag = models.IntegerField(default=0)
    sales_return_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    # Live Balance
    balance_bag = models.IntegerField(default=0, db_index=True)
    balance_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), db_index=True)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_yarn_stock"
        verbose_name = "Yarn Stock"
        verbose_name_plural = "Yarn Stocks"
        unique_together = ("company", "warehouse", "yarn_type", "yarn_count", "mill", "color_shade", "lot_no")
        indexes = [
            models.Index(fields=["company", "yarn_type", "yarn_count"]),
            models.Index(fields=["balance_quantity", "balance_bag"]),
        ]

    def __str__(self):
        shade_str = f" - {self.color_shade.color_name}" if self.color_shade else ""
        return f"{self.yarn_count.count}{shade_str} ({self.get_yarn_type_display()}) | Lot: {self.lot_no} | Bal: {self.balance_quantity} Kg"

    def recalculate_balance(self):
        """Recompute current balance: Inward - Outward - Sales + Sales Return"""
        self.balance_bag = (self.inward_bag + self.sales_return_bag) - (self.outward_bag + self.sales_bag)
        self.balance_quantity = (self.inward_quantity + self.sales_return_quantity) - (self.outward_quantity + self.sales_quantity)


class parent_yarn_inward_table(UppercaseModel):
    """
    Yarn Inward (Goods Receipt): tm_yarn_inward
    Captures inward receipt against Yarn PO or direct receipt for Grey/Dyed Yarn.
    Increments Yarn Stock upon authorization.
    """
    inward_number = models.CharField(max_length=30, unique=True, db_index=True)
    inward_date = models.DateField(db_index=True)
    dc_number = models.CharField(max_length=50, help_text="Delivery Challan / Invoice No from Mill/Trader")
    dc_date = models.DateField()
    vehicle_no = models.CharField(max_length=30, blank=True)

    yarn_type = models.CharField(max_length=20, choices=YarnCategory.CHOICES, default=YarnCategory.GREY, db_index=True)
    inward_source = models.CharField(
        max_length=20,
        choices=[("PURCHASE_PO", "Yarn PO Receipt"), ("DYEING_RETURN", "Dyeing Return (Job Work)")],
        default="PURCHASE_PO",
        db_index=True,
        help_text="Source of Yarn Inward"
    )
    po = models.ForeignKey(
        parent_po_table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inwards",
        db_column="po_id",
        help_text="Associated Yarn Purchase Order"
    )
    outward = models.ForeignKey(
        "parent_yarn_outward_table",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inwards",
        db_column="outward_id",
        help_text="Associated Yarn Outward for Dyeing"
    )
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="yarn_inwards")
    cfyear = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name="yarn_inwards")
    party = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="yarn_inward_parties", help_text="Supplier / Trader / Dyeing Unit")
    mill = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="yarn_inward_mills", help_text="Spinning Mill")
    warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="yarn_inwards")

    yarn_count = models.ForeignKey(YarnCountMaster, on_delete=models.PROTECT, related_name="yarn_inwards")
    color_shade = models.ForeignKey(ColorShadeMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="yarn_inwards")
    lot_no = models.CharField(max_length=50, default="GEN", db_index=True)

    bag = models.IntegerField(default=0)
    per_bag = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("45.360"))
    gross_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    tare_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    net_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Net Weight in Kg")

    rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    # Dyeing Process Loss & Charges (when received from Dyeing Outward)
    process_loss_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Dyeing process loss in Kg")
    process_loss_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), help_text="Dyeing process loss %")
    dyeing_rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"), help_text="Dyeing job work rate per Kg")
    dyeing_charges = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Total dyeing charges")

    remarks = models.CharField(max_length=200, blank=True)
    is_authorized = models.IntegerField(default=1, help_text="1 = Authorized & stock posted, 0 = Draft")
    status = models.IntegerField(default=1)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_yarn_inwards")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_yarn_inwards")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_yarn_inward"
        verbose_name = "Yarn Inward"
        verbose_name_plural = "Yarn Inwards"
        ordering = ["-inward_date", "-id"]

    def __str__(self):
        return f"{self.inward_number} - {self.mill.name} ({self.net_wt} Kg)"

    def clean(self):
        if self.gross_wt and self.tare_wt:
            self.net_wt = self.gross_wt - self.tare_wt
        elif self.bag and self.per_bag and not self.net_wt:
            self.net_wt = Decimal(str(self.bag)) * Decimal(str(self.per_bag))
        if self.net_wt and self.rate:
            self.amount = self.net_wt * Decimal(str(self.rate))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class child_yarn_inward_table(UppercaseModel):
    """
    Line Items: tx_yarn_inward
    Itemized counts/lots received under an inward document.
    """
    tm_inward = models.ForeignKey(parent_yarn_inward_table, on_delete=models.CASCADE, related_name="line_items", db_column="tm_inward_id")
    yarn_count = models.ForeignKey(YarnCountMaster, on_delete=models.PROTECT, related_name="inward_line_items")
    color_shade = models.ForeignKey(ColorShadeMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="inward_line_items")
    lot_no = models.CharField(max_length=50, default="GEN")
    bag = models.IntegerField(default=0)
    per_bag = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("45.360"))
    gross_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    tare_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    net_wt = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_yarn_inward"
        verbose_name = "Yarn Inward Line Item"
        verbose_name_plural = "Yarn Inward Line Items"

    def clean(self):
        if self.gross_wt and self.tare_wt:
            self.net_wt = self.gross_wt - self.tare_wt
        elif self.bag and self.per_bag and not self.net_wt:
            self.net_wt = Decimal(str(self.bag)) * Decimal(str(self.per_bag))
        if self.net_wt and self.rate:
            self.amount = self.net_wt * Decimal(str(self.rate))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class parent_yarn_outward_table(UppercaseModel):
    """
    Yarn Outward: tm_yarn_outward
    Dispatches yarn from stock:
      1. KNITTING: Yarn Outward to Knitting Mill (Knitting Program)
      2. DYEING: Yarn Outward for Dyeing (Grey Yarn to Dyeing Unit)
      3. PURCHASE_RETURN: Yarn Return back to Mill/Trader
    Deducts stock atomically upon authorization.
    """
    outward_number = models.CharField(max_length=30, unique=True, db_index=True)
    outward_date = models.DateField(db_index=True)
    outward_type = models.CharField(max_length=30, choices=YarnOutwardTypes.CHOICES, default=YarnOutwardTypes.KNITTING, db_index=True)

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="yarn_outwards")
    cfyear = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name="yarn_outwards")
    warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="yarn_outwards")
    destination_party = models.ForeignKey(
        PartyMaster,
        on_delete=models.PROTECT,
        related_name="yarn_outward_destinations",
        help_text="Knitting Mill / Dyeing Unit / Mill for Return"
    )

    yarn_type = models.CharField(max_length=20, choices=YarnCategory.CHOICES, default=YarnCategory.GREY, db_index=True)
    yarn_count = models.ForeignKey(YarnCountMaster, on_delete=models.PROTECT, related_name="yarn_outwards")
    mill = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="yarn_outward_mills", help_text="Spinning Mill")
    color_shade = models.ForeignKey(ColorShadeMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="yarn_outwards")
    lot_no = models.CharField(max_length=50, default="GEN")

    bag = models.IntegerField(default=0)
    quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Total Outward Weight (Kg)")
    received_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Received weight from dyeing/knitting (Kg)")
    remaining_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Pending weight at processor (Kg)")
    is_complete = models.IntegerField(default=0, help_text="0 = In-progress at processor, 1 = Fully received / completed")

    vehicle_no = models.CharField(max_length=30, blank=True)
    driver_name = models.CharField(max_length=100, blank=True)
    remarks = models.CharField(max_length=200, blank=True)
    is_authorized = models.IntegerField(default=1)
    status = models.IntegerField(default=1)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_yarn_outwards")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_yarn_outwards")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_yarn_outward"
        verbose_name = "Yarn Outward"
        verbose_name_plural = "Yarn Outwards"
        ordering = ["-outward_date", "-id"]

    def __str__(self):
        return f"{self.outward_number} [{self.get_outward_type_display()}] -> {self.destination_party.name} ({self.quantity} Kg)"

    def clean(self):
        if not self.pk and not self.remaining_quantity:
            self.remaining_quantity = self.quantity

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)



class child_yarn_outward_table(UppercaseModel):
    """
    Line Items: tx_yarn_outward
    Itemized counts/lots dispatched in outward DC.
    """
    tm_outward = models.ForeignKey(parent_yarn_outward_table, on_delete=models.CASCADE, related_name="line_items", db_column="tm_outward_id")
    yarn_count = models.ForeignKey(YarnCountMaster, on_delete=models.PROTECT, related_name="outward_line_items")
    color_shade = models.ForeignKey(ColorShadeMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="outward_line_items")
    mill = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="outward_line_items")
    lot_no = models.CharField(max_length=50, default="GEN")
    bag = models.IntegerField(default=0)
    quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    remarks = models.CharField(max_length=150, blank=True)
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_yarn_outward"
        verbose_name = "Yarn Outward Line Item"
        verbose_name_plural = "Yarn Outward Line Items"
