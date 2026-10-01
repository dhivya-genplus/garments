from django.db import models
from core.base_models import SoftDeleteModel
from core.constants import PartyTypes, YarnCategory, FabricCategory, ProcessTypes, WarehouseTypes
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
    Parties across the supply chain: Mills, Traders, Knitting Units,
    Dyeing Units, Customers, Suppliers, Job Workers.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="parties")
    party_type = models.CharField(max_length=30, choices=PartyTypes.CHOICES, db_index=True)
    code = models.CharField(max_length=50, db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    gst_number = models.CharField(max_length=20, blank=True, db_index=True)
    pan_number = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20, blank=True)
    credit_days = models.PositiveIntegerField(default=0)
    credit_limit = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    opening_balance = models.DecimalField(max_digits=15, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = "mx_party"
        verbose_name = "Party Master"
        verbose_name_plural = "Party Masters"
        unique_together = ("company", "code")
        ordering = ["name"]
        indexes = [
            models.Index(fields=["company", "party_type", "is_active", "is_deleted"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_party_type_display()})"


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


class YarnTypeMaster(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="yarn_types")
    name = models.CharField(max_length=100, db_index=True)  # e.g., "100% Cotton Combed", "Carded", "PC Blend", "Modal"
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "mx_yarn_type"
        verbose_name = "Yarn Type Master"
        verbose_name_plural = "Yarn Type Masters"
        unique_together = ("company", "code")
        ordering = ["name"]

    def __str__(self):
        return self.name


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
    yarn_type = models.ForeignKey(YarnTypeMaster, on_delete=models.PROTECT, related_name="yarns")
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
        return f"{self.yarn_code} ({self.yarn_type.name} {self.yarn_count.count}{color})"


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
