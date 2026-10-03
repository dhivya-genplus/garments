from decimal import Decimal
from django.db import models
from django.conf import settings
from core.base_models import UppercaseModel
from core.constants import YarnCategory
from apps.authentication.models import Company, FinancialYear
from apps.masters.models import PartyMaster, YarnCountMaster, ColorShadeMaster


class parent_po_table(UppercaseModel):
    """
    Primary Header: tm_yarn_po
    Primary document capturing yarn order header, spinning mill details,
    yarn type (Grey or Dyed Yarn), commercial summary, and authorization status.
    """
    po_number = models.CharField(max_length=30, unique=True, db_index=True)
    po_date = models.DateField(db_index=True)
    yarn_type = models.CharField(
        max_length=20,
        choices=YarnCategory.CHOICES,
        default=YarnCategory.GREY,
        db_index=True,
        help_text="Yarn Type: GREY (Grey Yarn) or DYED (Dyed Yarn)"
    )
    color_shade = models.ForeignKey(
        ColorShadeMaster,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="yarn_pos",
        help_text="Required if yarn_type is DYED"
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
        help_text="Color shade if Dyed Yarn"
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
