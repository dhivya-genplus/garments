from decimal import Decimal
from django.db import models
from django.conf import settings
from core.base_models import SoftDeleteModel
from core.constants import (
    PartyTypes, PartyCategory, AddressTypes, GstRegistrationType,
    GstTreatment, PaymentModes, VerificationStatus, PartyDocumentTypes,
    YarnCategory, FabricCategory, ProcessTypes, WarehouseTypes
)
from core.utils.encryption import EncryptedCharField
from apps.authentication.models import Company

class UnitOfMeasurement(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="uoms")
    code = models.CharField(max_length=20, db_index=True)  # e.g., KGS, MTR, BAG, ROLL, PCS
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "mx_uom"
        verbose_name = "Unit of Measurement"
        verbose_name_plural = "Units of Measurement"
        unique_together = ("company", "code")
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class PartyMaster(SoftDeleteModel):
    """
    Parties across the textile supply chain: Mills, Traders, Knitting Units,
    Dyeing Units, Customers, Suppliers, Job Workers, Subcontractors, Brokers, Transporters.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="parties")
    party_type = models.CharField(max_length=30, choices=PartyTypes.CHOICES, db_index=True)
    code = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    display_name = models.CharField(max_length=255, blank=True)
    party_category = models.CharField(max_length=30, choices=PartyCategory.CHOICES, default=PartyCategory.MANUFACTURER, db_index=True)
    parent_party = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="child_parties")
    remarks = models.TextField(blank=True)

    # Primary Contact & Flat legacy fields (kept synced for backward compatibility)
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    whatsapp_number = models.CharField(max_length=30, blank=True)
    website = models.URLField(max_length=255, blank=True)

    # Statutory & Tax Information
    gst_registration_type = models.CharField(max_length=30, choices=GstRegistrationType.CHOICES, default=GstRegistrationType.REGULAR, db_index=True)
    gst_number = models.CharField(max_length=20, blank=True, db_index=True)
    pan_number = models.CharField(max_length=20, blank=True, db_index=True)
    cin_number = models.CharField(max_length=30, blank=True, help_text="Corporate Identification Number / LLPIN")
    msme_number = models.CharField(max_length=50, blank=True, help_text="MSME / Udyam Registration No")
    tax_applicable = models.BooleanField(default=True)
    default_gst_treatment = models.CharField(max_length=30, choices=GstTreatment.CHOICES, default=GstTreatment.TAXABLE)
    tds_applicable = models.BooleanField(default=False)
    tds_section = models.CharField(max_length=20, blank=True, help_text="e.g. 194C, 194Q")
    export_import_classification = models.CharField(max_length=50, blank=True, help_text="IEC Code / SEZ")
    country_of_tax_registration = models.CharField(max_length=100, default="India")
    tax_verification_status = models.CharField(max_length=20, choices=VerificationStatus.CHOICES, default=VerificationStatus.UNVERIFIED)

    # Address Flat legacy fields (kept synced with default/registered address)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True, db_index=True)
    state = models.CharField(max_length=100, blank=True, db_index=True)
    pincode = models.CharField(max_length=20, blank=True)

    # Commercial & Price List Configuration
    default_purchase_price_list = models.ForeignKey('pricing.PriceList', on_delete=models.SET_NULL, null=True, blank=True, related_name="parties_default_purchase")
    default_sales_price_list = models.ForeignKey('pricing.PriceList', on_delete=models.SET_NULL, null=True, blank=True, related_name="parties_default_sales")
    default_job_work_price_list = models.ForeignKey('pricing.PriceList', on_delete=models.SET_NULL, null=True, blank=True, related_name="parties_default_job_work")
    currency = models.CharField(max_length=10, default="INR")
    payment_terms = models.CharField(max_length=100, blank=True, help_text="e.g. Net 30, Against Delivery")
    credit_days = models.PositiveIntegerField(default=0)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    rebate_tier = models.CharField(max_length=50, blank=True, help_text="Tier 1, Tier 2, etc.")
    default_discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    freight_terms = models.CharField(max_length=50, blank=True, help_text="Ex-Mill, FOR Destination, Paid by Buyer")
    rate_contract_number = models.CharField(max_length=50, blank=True)
    contract_start_date = models.DateField(null=True, blank=True)
    contract_end_date = models.DateField(null=True, blank=True)
    price_approval_required = models.BooleanField(default=False)

    # Accounting & Ledger Configuration
    ledger_account_code = models.CharField(max_length=50, blank=True, help_text="Chart of accounts code, e.g. 2001, 1002")
    default_purchase_account = models.CharField(max_length=50, blank=True)
    default_sales_account = models.CharField(max_length=50, blank=True)
    default_job_work_expense_account = models.CharField(max_length=50, blank=True)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal("0.00"))
    opening_balance_type = models.CharField(max_length=10, choices=[('DR', 'Debit (Receivable)'), ('CR', 'Credit (Payable)')], default='CR')
    opening_balance_date = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "mx_party"
        verbose_name = "Party Master"
        verbose_name_plural = "Party Masters"
        unique_together = ("company", "code")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["company", "party_type", "is_active", "is_deleted"]),
            models.Index(fields=["company", "party_category", "is_active"]),
            models.Index(fields=["gst_number"]),
        ]

    def __str__(self):
        disp = self.display_name or self.name
        return f"{disp} ({self.get_party_type_display()})"


class PartyRole(SoftDeleteModel):
    """
    Multiple Business Roles per Party: mx_party_role
    Allows a party to be e.g. both a Supplier, Customer, Knitter, and Mill without duplicating party records.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="party_roles")
    party = models.ForeignKey(PartyMaster, on_delete=models.CASCADE, related_name="roles")
    role = models.CharField(max_length=30, choices=PartyTypes.CHOICES, db_index=True)
    is_primary = models.BooleanField(default=False)

    class Meta:
        db_table = "mx_party_role"
        verbose_name = "Party Business Role"
        verbose_name_plural = "Party Business Roles"
        unique_together = ("party", "role")
        ordering = ["-is_primary", "role"]

    def __str__(self):
        pri = " [Primary]" if self.is_primary else ""
        return f"{self.party.name} - {self.get_role_display()}{pri}"


class PartyContact(SoftDeleteModel):
    """
    Multiple Contacts per Party: mx_party_contact
    Captures primary, accounts, dispatch, technical, and management contacts.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="party_contacts")
    party = models.ForeignKey(PartyMaster, on_delete=models.CASCADE, related_name="contacts")
    contact_person = models.CharField(max_length=150)
    designation = models.CharField(max_length=100, blank=True)
    mobile = models.CharField(max_length=30, db_index=True)
    alternate_mobile = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True, db_index=True)
    alternate_email = models.EmailField(blank=True)
    whatsapp_number = models.CharField(max_length=30, blank=True)
    website = models.URLField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "mx_party_contact"
        verbose_name = "Party Contact"
        verbose_name_plural = "Party Contacts"
        ordering = ["-is_primary", "contact_person"]

    def __str__(self):
        pri = " [Primary]" if self.is_primary else ""
        return f"{self.contact_person} ({self.designation or 'Contact'}){pri}"


class PartyAddress(SoftDeleteModel):
    """
    Multiple Addresses per Party: mx_party_address
    Captures Registered, Billing, Delivery / Shipping, and Factory / Branch addresses.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="party_addresses")
    party = models.ForeignKey(PartyMaster, on_delete=models.CASCADE, related_name="addresses")
    address_type = models.CharField(max_length=20, choices=AddressTypes.CHOICES, default=AddressTypes.REGISTERED, db_index=True)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=100, default="India")
    state = models.CharField(max_length=100, db_index=True)
    district = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, db_index=True)
    area_locality = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20)
    gst_state_code = models.CharField(max_length=2, blank=True, help_text="2-digit Indian GST State code (e.g. 33)")
    is_default = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "mx_party_address"
        verbose_name = "Party Address"
        verbose_name_plural = "Party Addresses"
        ordering = ["-is_default", "address_type"]

    def __str__(self):
        return f"{self.get_address_type_display()} - {self.city}, {self.state} ({self.pincode})"


class PartyBankDetail(SoftDeleteModel):
    """
    Bank & Payment Details per Party: mx_party_bank
    Captures bank accounts, IFSC, UPI.
    Sensitive account number is encrypted via EncryptedCharField and masked in read APIs.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="party_banks")
    party = models.ForeignKey(PartyMaster, on_delete=models.CASCADE, related_name="bank_details")
    bank_name = models.CharField(max_length=150)
    branch_name = models.CharField(max_length=150, blank=True)
    account_holder_name = models.CharField(max_length=150)
    account_number = EncryptedCharField(max_length=512, help_text="Encrypted Bank Account Number")
    ifsc_code = models.CharField(max_length=20, db_index=True)
    upi_id = models.CharField(max_length=100, blank=True)
    preferred_payment_mode = models.CharField(max_length=30, choices=PaymentModes.CHOICES, default=PaymentModes.NEFT_RTGS)
    beneficiary_verification_status = models.CharField(max_length=20, choices=VerificationStatus.CHOICES, default=VerificationStatus.UNVERIFIED)
    is_default = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "mx_party_bank"
        verbose_name = "Party Bank Detail"
        verbose_name_plural = "Party Bank Details"
        ordering = ["-is_default", "bank_name"]

    def __str__(self):
        return f"{self.bank_name} - {self.account_holder_name} ({self.ifsc_code})"

    @property
    def masked_account_number(self):
        acc = str(self.account_number or "")
        if len(acc) > 4:
            return "X" * (len(acc) - 4) + acc[-4:]
        return "XXXX" if acc else ""


class PartyCapability(SoftDeleteModel):
    """
    Textile & Job Work Processing Capabilities: mx_party_capability
    Provides conditional operational information for Knitting Units, Dyeing Units, Mills, and Job Workers.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="party_capabilities")
    party = models.OneToOneField(PartyMaster, on_delete=models.CASCADE, related_name="capability")
    processes_performed = models.ManyToManyField('ProcessMaster', blank=True, related_name="capable_parties")
    yarn_counts_handled = models.ManyToManyField('YarnCountMaster', blank=True, related_name="capable_parties")
    fabric_types_handled = models.ManyToManyField('FabricTypeMaster', blank=True, related_name="capable_parties")
    machine_types = models.CharField(max_length=255, blank=True, help_text="e.g. 24GG 30-inch circular knit machines, soft-flow dyeing vessels")
    production_capacity = models.DecimalField(max_digits=15, decimal_places=3, default=Decimal("0.000"), help_text="Daily/Monthly capacity")
    capacity_uom = models.ForeignKey('UnitOfMeasurement', on_delete=models.SET_NULL, null=True, blank=True, related_name="party_capacity_uoms")
    min_job_work_qty = models.DecimalField(max_digits=15, decimal_places=3, default=Decimal("0.000"))
    max_job_work_qty = models.DecimalField(max_digits=15, decimal_places=3, default=Decimal("0.000"))
    standard_processing_days = models.PositiveIntegerField(default=0, help_text="Standard turnaround time in days")
    procurement_lead_time_days = models.PositiveIntegerField(default=0, help_text="Lead time in days")
    default_uom = models.ForeignKey('UnitOfMeasurement', on_delete=models.SET_NULL, null=True, blank=True, related_name="party_default_uoms")
    quality_certifications = models.CharField(max_length=255, blank=True, help_text="e.g. GOTS, OEKO-TEX Standard 100, BCI")
    sample_approval_required = models.BooleanField(default=True)

    class Meta:
        db_table = "mx_party_capability"
        verbose_name = "Party Textile Capability"
        verbose_name_plural = "Party Textile Capabilities"

    def __str__(self):
        return f"Capabilities of {self.party.name}"


class PartyDocument(SoftDeleteModel):
    """
    Statutory, Quality & Contract Documents: mx_party_document
    Stores GST certificates, PAN card copies, MSME certificates, bank proofs, rate contracts.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="party_documents")
    party = models.ForeignKey(PartyMaster, on_delete=models.CASCADE, related_name="documents")
    document_type = models.CharField(max_length=30, choices=PartyDocumentTypes.CHOICES, default=PartyDocumentTypes.OTHER, db_index=True)
    document_number = models.CharField(max_length=100, blank=True)
    file_attachment = models.FileField(upload_to="party_documents/%Y/%m/", null=True, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    verification_status = models.CharField(max_length=20, choices=VerificationStatus.CHOICES, default=VerificationStatus.UNVERIFIED)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="verified_party_documents")
    verified_at = models.DateTimeField(null=True, blank=True)
    remarks = models.TextField(blank=True)

    class Meta:
        db_table = "mx_party_document"
        verbose_name = "Party Document"
        verbose_name_plural = "Party Documents"
        ordering = ["-created_on"]

    def __str__(self):
        return f"{self.get_document_type_display()} - {self.party.name} ({self.document_number or 'No No.'})"


class YarnCountMaster(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="yarn_counts")
    count = models.CharField(max_length=30, db_index=True)  # e.g., "30s", "34s", "40s", "2/40s"
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "mx_yarn_count"
        verbose_name = "Yarn Count Master"
        verbose_name_plural = "Yarn Count Masters"
        unique_together = ("company", "count")
        ordering = ["count"]

    def __str__(self):
        return self.count


class ColorShadeMaster(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="color_shades")
    shade_code = models.CharField(max_length=50, db_index=True)
    color_name = models.CharField(max_length=100, db_index=True)
    hex_code = models.CharField(max_length=10, blank=True)
    pantone_ref = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "mx_color_shade"
        verbose_name = "Color Shade Master"
        verbose_name_plural = "Color Shade Masters"
        unique_together = ("company", "shade_code")
        ordering = ["color_name"]

    def __str__(self):
        return f"{self.color_name} ({self.shade_code})"


class YarnMaster(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="yarns")
    yarn_code = models.CharField(max_length=50, db_index=True)
    yarn_count = models.ForeignKey(YarnCountMaster, on_delete=models.PROTECT, related_name="yarns")
    category = models.CharField(max_length=20, choices=YarnCategory.CHOICES, default=YarnCategory.GREY, db_index=True)
    color_shade = models.ForeignKey(ColorShadeMaster, on_delete=models.SET_NULL, null=True, blank=True, related_name="dyed_yarns")
    uom = models.ForeignKey(UnitOfMeasurement, on_delete=models.PROTECT, related_name="yarns")
    hsn_code = models.CharField(max_length=20, blank=True)
    reorder_level = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "mx_yarn"
        verbose_name = "Yarn Master"
        verbose_name_plural = "Yarn Masters"
        unique_together = ("company", "yarn_code")
        ordering = ["yarn_code"]
        indexes = [
            models.Index(fields=["company", "category", "is_active", "is_deleted"]),
        ]

    def __str__(self):
        color = f" - {self.color_shade.color_name}" if self.color_shade else ""
        return f"{self.yarn_code} ({self.yarn_count.count}{color})"


class FabricTypeMaster(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="fabric_types")
    name = models.CharField(max_length=100, db_index=True)  # e.g., "Single Jersey", "Interlock", "1x1 Rib", "2x2 Rib", "Fleece", "Pique"
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "mx_fabric_type"
        verbose_name = "Fabric Type Master"
        verbose_name_plural = "Fabric Type Masters"
        unique_together = ("company", "code")
        ordering = ["name"]

    def __str__(self):
        return self.name


class FabricMaster(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="fabrics")
    fabric_code = models.CharField(max_length=50, db_index=True)
    fabric_name = models.CharField(max_length=200, db_index=True)
    fabric_type = models.ForeignKey(FabricTypeMaster, on_delete=models.PROTECT, related_name="fabrics")
    category = models.CharField(max_length=20, choices=FabricCategory.CHOICES, default=FabricCategory.GREY, db_index=True)
    yarn = models.ForeignKey(YarnMaster, on_delete=models.SET_NULL, null=True, blank=True, related_name="fabrics")
    color_shade = models.ForeignKey(ColorShadeMaster, on_delete=models.SET_NULL, null=True, blank=True, related_name="dyed_fabrics")
    gsm = models.PositiveIntegerField(default=0, help_text="Grams per Square Meter")
    dia = models.CharField(max_length=50, blank=True, help_text="Diameter / Width in inches or cm")
    gauge = models.CharField(max_length=50, blank=True, help_text="Machine Gauge (e.g. 24GG, 28GG)")
    uom = models.ForeignKey(UnitOfMeasurement, on_delete=models.PROTECT, related_name="fabrics")
    hsn_code = models.CharField(max_length=20, blank=True)
    min_stock_alert = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "mx_fabric"
        verbose_name = "Fabric Master"
        verbose_name_plural = "Fabric Masters"
        unique_together = ("company", "fabric_code")
        ordering = ["fabric_code"]
        indexes = [
            models.Index(fields=["company", "category", "is_active", "is_deleted"]),
        ]

    def __str__(self):
        return f"{self.fabric_code} - {self.fabric_name} ({self.get_category_display()})"


class ProcessMaster(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="processes")
    process_code = models.CharField(max_length=50, db_index=True)
    process_name = models.CharField(max_length=150, db_index=True)
    process_type = models.CharField(max_length=30, choices=ProcessTypes.CHOICES, db_index=True)
    default_loss_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    standard_rate_per_kg = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "mx_process"
        verbose_name = "Process Master"
        verbose_name_plural = "Process Masters"
        unique_together = ("company", "process_code")
        ordering = ["process_name"]

    def __str__(self):
        return f"{self.process_name} ({self.get_process_type_display()})"


class WarehouseMaster(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="warehouses")
    warehouse_code = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=200, db_index=True)
    warehouse_type = models.CharField(max_length=40, choices=WarehouseTypes.CHOICES, db_index=True)
    address = models.TextField(blank=True)
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "mx_warehouse"
        verbose_name = "Warehouse Master"
        verbose_name_plural = "Warehouse Masters"
        unique_together = ("company", "warehouse_code")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} [{self.get_warehouse_type_display()}]"


class UppercaseModel(models.Model):
    """Abstract base model to automatically uppercase all CharField & TextField values."""
    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        for field in self._meta.fields:
            if isinstance(field, (models.CharField, models.TextField)):
                val = getattr(self, field.name)
                if isinstance(val, str): 
                    setattr(self, field.name, val.upper())
        super().save(*args, **kwargs)


class quality_program_table(UppercaseModel):
    quality = models.CharField(max_length=50) 
    style = models.CharField(max_length=50) 
    fabric_id = models.CharField(max_length=50, null=True, blank=True) 
    is_active = models.IntegerField(default=1) 
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(default=1) 
    updated_by = models.IntegerField(default=1)
    
    class Meta:
        db_table = "quality_program"
        verbose_name = "Quality Program" 
        verbose_name_plural = "Quality Programs"

    def __str__(self):
        return f"{self.style} - {self.quality}"

    def soft_delete(self, user=None):
        self.status = 0
        self.is_active = 0
        self.save(update_fields=["status", "is_active", "updated_on"])
        self.sizes.all().update(status=0, is_active=0)


class sub_quality_program_table(UppercaseModel):
    tm = models.ForeignKey(
        quality_program_table,
        on_delete=models.CASCADE,
        related_name="sizes",
        db_column="tm_id",
        verbose_name="Quality Program"
    )
    size_id = models.IntegerField() 
    position = models.IntegerField()
    per_box = models.IntegerField()
    is_active = models.IntegerField(default=1)
    status = models.IntegerField(default=1)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    created_by = models.IntegerField(default=1) 
    updated_by = models.IntegerField(default=1)
     
    class Meta:
        db_table = "mx_quality_program_size"
        verbose_name = "Sub Quality Program Size"
        verbose_name_plural = "Sub Quality Program Sizes"

    def __str__(self):
        return f"TM: {self.tm_id} - Size: {self.size_id}"

    def soft_delete(self, user=None):
        self.status = 0
        self.is_active = 0
        self.save(update_fields=["status", "is_active", "updated_on"])


class TaxMaster(SoftDeleteModel):
    """
    Tax Master: mx_tax
    Defines GST rates, cess, and HSN/SAC classifications per company.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="taxes")
    tax_name = models.CharField(max_length=100)
    tax_code = models.CharField(max_length=50, db_index=True)
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("5.00"))
    cgst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("2.50"))
    sgst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("2.50"))
    igst_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("5.00"))
    hsn_sac_code = models.CharField(max_length=20, blank=True, help_text="HSN/SAC Code (e.g. 5205 for Cotton Yarn)")
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True, db_index=True)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "mx_tax"
        verbose_name = "Tax Master"
        verbose_name_plural = "Tax Masters"
        unique_together = ("company", "tax_code")
        ordering = ["tax_percent", "tax_name"]

    def __str__(self):
        return f"{self.tax_name} ({self.tax_percent}%)"



