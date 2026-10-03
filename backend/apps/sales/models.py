from __future__ import annotations
from decimal import Decimal
from django.db import models
from django.conf import settings
from core.base_models import UppercaseModel
from core.constants import YarnCategory
from apps.authentication.models import Company, FinancialYear
from apps.masters.models import PartyMaster, YarnCountMaster, ColorShadeMaster, WarehouseMaster


class parent_yarn_sales_table(UppercaseModel):
    """
    Yarn Sales Header: tm_yarn_sales
    Invoice document for direct sale of Grey or Dyed yarn from warehouse stock.
    Decrements Yarn Stock atomically.
    """
    invoice_number = models.CharField(max_length=30, unique=True, db_index=True)
    invoice_date = models.DateField(db_index=True)
    yarn_type = models.CharField(max_length=20, choices=YarnCategory.CHOICES, default=YarnCategory.GREY, db_index=True)

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="yarn_sales")
    cfyear = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name="yarn_sales")
    warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="yarn_sales")
    customer = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="yarn_sales_customers", help_text="Buyer / Customer")

    yarn_count = models.ForeignKey(YarnCountMaster, on_delete=models.PROTECT, related_name="yarn_sales")
    mill = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="yarn_sales_mills", help_text="Spinning Mill")
    color_shade = models.ForeignKey(ColorShadeMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="yarn_sales")
    lot_no = models.CharField(max_length=50, default="GEN")

    bag = models.IntegerField(default=0)
    per_bag = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("45.360"))
    quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Net sold weight (Kg)")

    rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"), help_text="Sale rate per Kg")
    subtotal = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("5.00"), help_text="GST % (typically 5% for Yarn)")
    tax_amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    total_amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    payment_terms = models.CharField(max_length=100, blank=True)
    remarks = models.CharField(max_length=200, blank=True)
    is_authorized = models.IntegerField(default=1)
    status = models.IntegerField(default=1)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_yarn_sales")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_yarn_sales")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_yarn_sales"
        verbose_name = "Yarn Sales"
        verbose_name_plural = "Yarn Sales"
        ordering = ["-invoice_date", "-id"]

    def __str__(self):
        return f"{self.invoice_number} -> {self.customer.name} ({self.quantity} Kg)"

    def clean(self):
        if self.bag and self.per_bag and not self.quantity:
            self.quantity = Decimal(str(self.bag)) * Decimal(str(self.per_bag))
        if self.quantity and self.rate:
            self.subtotal = self.quantity * Decimal(str(self.rate))
            tax_p = Decimal(str(self.tax_percent or 0)) / Decimal("100.00")
            self.tax_amount = self.subtotal * tax_p
            self.total_amount = self.subtotal + self.tax_amount

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        self.status = 0
        self.updated_by = user
        self.save(update_fields=["status", "updated_by", "updated_on"])
        self.line_items.all().update(status=0)


class child_yarn_sales_table(UppercaseModel):
    """
    Line Items: tx_yarn_sales
    Itemized counts/lots billed under a sales invoice.
    """
    tm_sales = models.ForeignKey(parent_yarn_sales_table, on_delete=models.CASCADE, related_name="line_items", db_column="tm_sales_id")
    yarn_count = models.ForeignKey(YarnCountMaster, on_delete=models.PROTECT, related_name="sales_line_items")
    color_shade = models.ForeignKey(ColorShadeMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="sales_line_items")
    mill = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="sales_line_items")
    lot_no = models.CharField(max_length=50, default="GEN")
    bag = models.IntegerField(default=0)
    per_bag = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("45.360"))
    quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_yarn_sales"
        verbose_name = "Yarn Sales Line Item"
        verbose_name_plural = "Yarn Sales Line Items"

    def clean(self):
        if self.bag and self.per_bag and not self.quantity:
            self.quantity = Decimal(str(self.bag)) * Decimal(str(self.per_bag))
        if self.quantity and self.rate:
            self.amount = self.quantity * Decimal(str(self.rate))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class parent_yarn_sales_return_table(UppercaseModel):
    """
    Yarn Sales Return: tm_yarn_sales_return
    Customer returns previously purchased Grey or Dyed yarn.
    Increments Yarn Stock atomically back into inventory.
    """
    return_number = models.CharField(max_length=30, unique=True, db_index=True)
    return_date = models.DateField(db_index=True)
    sales_invoice = models.ForeignKey(
        parent_yarn_sales_table,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="returns",
        help_text="Reference Sales Invoice"
    )

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="yarn_sales_returns")
    cfyear = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name="yarn_sales_returns")
    warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="yarn_sales_returns")
    customer = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="yarn_sales_return_customers")

    yarn_type = models.CharField(max_length=20, choices=YarnCategory.CHOICES, default=YarnCategory.GREY, db_index=True)
    yarn_count = models.ForeignKey(YarnCountMaster, on_delete=models.PROTECT, related_name="yarn_sales_returns")
    mill = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="yarn_sales_return_mills")
    color_shade = models.ForeignKey(ColorShadeMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="yarn_sales_returns")
    lot_no = models.CharField(max_length=50, default="GEN")

    bag = models.IntegerField(default=0)
    quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Returned weight in Kg")
    rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    return_reason = models.CharField(max_length=200, help_text="E.g., Shade Variation, Defective Count, Excess Quantity")
    is_authorized = models.IntegerField(default=1)
    status = models.IntegerField(default=1)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_yarn_sales_returns")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_yarn_sales_returns")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_yarn_sales_return"
        verbose_name = "Yarn Sales Return"
        verbose_name_plural = "Yarn Sales Returns"
        ordering = ["-return_date", "-id"]

    def __str__(self):
        return f"{self.return_number} <- {self.customer.name} ({self.quantity} Kg)"

    def clean(self):
        if self.quantity and self.rate:
            self.amount = self.quantity * Decimal(str(self.rate))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        self.status = 0
        self.updated_by = user
        self.save(update_fields=["status", "updated_by", "updated_on"])
        self.line_items.all().update(status=0)


class child_yarn_sales_return_table(UppercaseModel):
    """
    Line Items: tx_yarn_sales_return
    Itemized counts/lots returned by customer.
    """
    tm_sales_return = models.ForeignKey(parent_yarn_sales_return_table, on_delete=models.CASCADE, related_name="line_items", db_column="tm_sales_return_id")
    yarn_count = models.ForeignKey(YarnCountMaster, on_delete=models.PROTECT, related_name="sales_return_line_items")
    color_shade = models.ForeignKey(ColorShadeMaster, on_delete=models.PROTECT, null=True, blank=True, related_name="sales_return_line_items")
    mill = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="sales_return_line_items")
    lot_no = models.CharField(max_length=50, default="GEN")
    bag = models.IntegerField(default=0)
    quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_yarn_sales_return"
        verbose_name = "Yarn Sales Return Line Item"
        verbose_name_plural = "Yarn Sales Return Line Items"
