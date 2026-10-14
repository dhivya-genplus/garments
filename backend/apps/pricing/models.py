from decimal import Decimal
from django.db import models
from django.utils import timezone
from core.base_models import UppercaseModel
from core.constants import PriceListType, PriceListScope, PriceListItemType, YarnCategory


class PriceList(UppercaseModel):
    """
    Price List Master Header: tm_price_list
    Captures header configurations for Purchase, Sales, Job Work, General, and Party-Specific price lists.
    No direct foreign keys - relies on bigint references (company_id, party_id, currency_id).
    """
    company_id = models.BigIntegerField(db_index=True)
    price_list_code = models.CharField(max_length=50, db_index=True)
    price_list_name = models.CharField(max_length=150)
    list_type = models.CharField(max_length=20, choices=PriceListType.CHOICES, db_index=True)
    scope = models.CharField(max_length=20, choices=PriceListScope.CHOICES, default=PriceListScope.GENERAL, db_index=True)
    party_id = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Reference to tm_party.id (NULL for General)")
    currency_id = models.BigIntegerField(default=1, db_index=True, help_text="Reference to tc_currency.id (Default INR)")
    valid_from = models.DateField(db_index=True)
    valid_to = models.DateField(db_index=True)
    is_default = models.BooleanField(default=False, help_text="Default list for company when no party contract matches")
    description = models.TextField(blank=True, null=True)

    record_status = models.CharField(max_length=1, default="A", db_index=True)  # 'A'=Active, 'I'=Inactive, 'D'=Deleted
    created_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_by = models.BigIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_price_list"
        verbose_name = "Price List"
        verbose_name_plural = "Price Lists"
        indexes = [
            models.Index(fields=["company_id", "party_id", "list_type", "record_status"]),
            models.Index(fields=["company_id", "valid_from", "valid_to", "record_status"]),
            models.Index(fields=["company_id", "is_default", "list_type", "record_status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["company_id", "price_list_code"],
                condition=~models.Q(record_status="D"),
                name="uq_tm_price_list_code"
            )
        ]

    def __str__(self):
        party_str = f" [Party #{self.party_id}]" if self.party_id else " [General]"
        return f"{self.price_list_code} - {self.price_list_name}{party_str} ({self.get_list_type_display()})"

    def soft_delete(self, user_id=None):
        self.record_status = "D"
        if user_id:
            self.updated_by = user_id
        self.save(update_fields=["record_status", "updated_by", "updated_at"])

    @property
    def items(self):
        return PriceListItem.objects.filter(price_list_id=self.id, record_status="A")

    @property
    def job_rules(self):
        return PriceListJobRule.objects.filter(price_list_id=self.id, record_status="A")




class PriceListItem(UppercaseModel):
    """
    Price List Item Line: tm_price_list_item
    Captures pricing lines, volume slabs, technical variants (e.g. Yarn Count, Color Shade), and discounts.
    """
    company_id = models.BigIntegerField(db_index=True)
    price_list_id = models.BigIntegerField(db_index=True, help_text="Reference to tm_price_list.id")
    item_type = models.CharField(max_length=30, choices=PriceListItemType.CHOICES, default=PriceListItemType.YARN, db_index=True)
    item_id = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Reference to mx_yarn, mx_fabric, etc.")
    
    # Textile Technical Specs (Yarn specific)
    yarn_count_id = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Reference to mx_yarn_count.id")
    yarn_type = models.CharField(max_length=20, choices=YarnCategory.CHOICES, null=True, blank=True, db_index=True, help_text="Grey, Dyed, Melange, Blended, etc.")
    color_shade_id = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Reference to mx_color_shade.id")
    uom_id = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Reference to mx_uom.id")

    # Volume Break Slabs
    min_quantity = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"), help_text="Lower bound of quantity slab (inclusive)")
    max_quantity = models.DecimalField(max_digits=18, decimal_places=3, null=True, blank=True, help_text="Upper bound of quantity slab (inclusive; NULL = unbounded)")

    # Rates & Commercials
    base_rate = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"), help_text="Standard rate per UOM before discount")
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), help_text="Discount percentage (e.g. 2.50%)")
    net_rate = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"), help_text="Net rate after discount (auto-computed)")

    # Lead Times & MOQ
    procurement_days = models.PositiveIntegerField(default=0, help_text="Procurement lead time in days")
    moq = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"), help_text="Minimum Order Quantity (MOQ)")
    lead_time_days = models.IntegerField(default=0)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    record_status = models.CharField(max_length=1, default="A", db_index=True)
    created_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_by = models.BigIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_price_list_item"
        verbose_name = "Price List Item"
        verbose_name_plural = "Price List Items"
        indexes = [
            models.Index(fields=["company_id", "price_list_id", "item_type", "record_status"]),
            models.Index(fields=["company_id", "item_type", "yarn_count_id", "record_status"]),
            models.Index(fields=["company_id", "min_quantity", "max_quantity", "record_status"]),
        ]

    def __str__(self):
        count_str = f" Count #{self.yarn_count_id}" if self.yarn_count_id else ""
        return f"PL #{self.price_list_id} - {self.item_type}{count_str} @ Rs.{self.net_rate}"

    def clean(self):
        if self.base_rate:
            disc = Decimal(str(self.discount_percent or 0)) / Decimal("100.00")
            self.net_rate = (self.base_rate * (Decimal("1.0000") - disc)).quantize(Decimal("0.0001"))
        else:
            self.net_rate = Decimal("0.0000")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self, user_id=None):
        self.record_status = "D"
        if user_id:
            self.updated_by = user_id
        self.save(update_fields=["record_status", "updated_by", "updated_at"])


class PriceListJobRule(UppercaseModel):
    """
    Job Work Conversion Rates & Rules: tm_price_list_job_rule
    Captures subcontract rates, lead times (procurement days, process days),
    MOQ thresholds, small lot surcharges, and technical parameters for Knitting,
    Dyeing, Printing, Cutting, and Stitching.
    """
    company_id = models.BigIntegerField(db_index=True)
    price_list_id = models.BigIntegerField(db_index=True, help_text="Reference to tm_price_list.id")
    process_stage_id = models.BigIntegerField(db_index=True, help_text="Reference to mx_process_stage.id")
    uom_id = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Reference to mx_uom.id (KG, MTR, PCS, DOZEN)")

    # Technical Matching Filters (NULL = Wildcard / Matches any)
    fabric_type_id = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Ref to mx_fabric_type.id (e.g. Single Jersey, Rib)")
    yarn_count_id = models.BigIntegerField(null=True, blank=True, db_index=True, help_text="Ref to mx_yarn_count.id (e.g. 30s, 34s)")
    machine_gauge = models.CharField(max_length=30, blank=True, null=True, help_text="e.g. 24GG, 28GG")
    dia_range = models.CharField(max_length=50, blank=True, null=True, help_text="e.g. 20-30 inches")
    is_lycra_plated = models.BooleanField(null=True, blank=True, help_text="True if Lycra/Spandex attachment applies")
    shade_category = models.CharField(max_length=30, blank=True, null=True, db_index=True, help_text="WHITE, LIGHT, MEDIUM, DARK, EXTRA_DARK")
    dye_class = models.CharField(max_length=50, blank=True, null=True, help_text="REACTIVE, DISPERSE")
    garment_style_category = models.CharField(max_length=100, blank=True, null=True, db_index=True, help_text="CREW_NECK_TEE, POLO, HOODIE")
    print_color_count = models.IntegerField(null=True, blank=True, help_text="Number of print colors")

    # Commercial Conversion Rates & Yield
    job_rate = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"), help_text="Subcontract conversion charge per UOM")
    allowed_loss_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), help_text="Process loss % allowance")

    # Surcharges & Modifiers
    lycra_surcharge = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"), help_text="Lycra plating surcharge per Kg")
    special_finish_surcharge = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"), help_text="Bio-polishing / Silicon finish surcharge")
    small_lot_surcharge = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"), help_text="Surcharge per unit when order quantity is below MOQ")

    # Operational Lead Times & MOQ
    procurement_days = models.PositiveIntegerField(default=0, help_text="Raw material / transit lead time in days (e.g. yarn dispatch to knitter, greige to dyer)")
    process_days = models.PositiveIntegerField(default=0, help_text="Subcontract conversion turnaround time (TAT) in days")
    moq = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"), help_text="Minimum Order Quantity required for this job work process (e.g. 250.000 Kg or 500 Pcs)")

    # Tier Slabs
    min_quantity = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"), help_text="Lower bound of quantity slab")
    max_quantity = models.DecimalField(max_digits=18, decimal_places=3, null=True, blank=True, help_text="Upper bound of quantity slab")

    record_status = models.CharField(max_length=1, default="A", db_index=True)
    created_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_by = models.BigIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_price_list_job_rule"
        verbose_name = "Price List Job Rule"
        verbose_name_plural = "Price List Job Rules"
        indexes = [
            models.Index(fields=["company_id", "price_list_id", "process_stage_id", "record_status"]),
            models.Index(fields=["company_id", "process_stage_id", "fabric_type_id", "yarn_count_id", "record_status"]),
            models.Index(fields=["company_id", "process_stage_id", "shade_category", "record_status"]),
            models.Index(fields=["company_id", "process_stage_id", "garment_style_category", "record_status"]),
        ]

    def __str__(self):
        lycra_str = " + Lycra" if self.is_lycra_plated else ""
        shade_str = f" [{self.shade_category}]" if self.shade_category else ""
        moq_str = f" (MOQ {self.moq})" if self.moq else ""
        return f"JobRule #{self.id} [Stage #{self.process_stage_id}]{shade_str}{lycra_str} @ Rs.{self.job_rate}{moq_str}"

    def soft_delete(self, user_id=None):
        self.record_status = "D"
        if user_id:
            self.updated_by = user_id
        self.save(update_fields=["record_status", "updated_by", "updated_at"])


class PricingAudit(UppercaseModel):
    """
    Pricing Audit Log: ta_pricing_audit
    Maintains an immutable historical audit trail of every price resolution,
    rate override, manual edit, and supervisor approval on transactional documents.
    """
    company_id = models.BigIntegerField(db_index=True)
    document_type = models.CharField(max_length=50, db_index=True, help_text="YARN_PO, YARN_SALES, PROCESS_PROGRAM")
    document_id = models.BigIntegerField(db_index=True)
    line_item_id = models.BigIntegerField(null=True, blank=True)
    
    resolved_price_list_id = models.BigIntegerField(null=True, blank=True, help_text="Price list picked by engine")
    resolved_rule_id = models.BigIntegerField(null=True, blank=True, help_text="Line item rule picked by engine")
    
    system_rate = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"))
    actual_rate = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"))
    is_override = models.BooleanField(default=False, db_index=True, help_text="True if actual_rate differs from system_rate")
    override_reason = models.CharField(max_length=255, blank=True, null=True)
    
    approved_by = models.BigIntegerField(null=True, blank=True)
    created_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "ta_pricing_audit"
        verbose_name = "Pricing Audit Log"
        verbose_name_plural = "Pricing Audit Logs"
        ordering = ["-created_at", "-id"]
        indexes = [
            models.Index(fields=["company_id", "document_type", "document_id"]),
            models.Index(fields=["company_id", "is_override", "created_at"]),
        ]

    def __str__(self):
        override_flag = " [OVERRIDE]" if self.is_override else ""
        return f"{self.document_type} #{self.document_id}: System Rs.{self.system_rate} -> Actual Rs.{self.actual_rate}{override_flag}"
