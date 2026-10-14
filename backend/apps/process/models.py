from decimal import Decimal
from django.db import models
from django.conf import settings
from core.base_models import UppercaseModel
from apps.authentication.models import Company, FinancialYear
from apps.masters.models import PartyMaster, WarehouseMaster, FabricMaster, FabricTypeMaster, ColorShadeMaster
from core.constants import ProcessProgramStatus


class parent_process_stage_table(UppercaseModel):
    """
    Process Stage Master: mx_process_stage
    Defines configured production stages (Knitting, Dyeing, Cutting, Printing, Stitching, etc.)
    with standard routing rules, default inputs/outputs, and loss tolerances.
    """
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="process_stages")
    name = models.CharField(max_length=100, db_index=True, help_text="e.g. Knitting, Dyeing, Cutting")
    code = models.CharField(max_length=50, db_index=True, help_text="e.g. KNITTING, DYEING, CUTTING")
    sequence_order = models.PositiveIntegerField(default=10, help_text="Routing sequence")

    # Routing Configuration
    input_from_stage = models.CharField(max_length=50, help_text="Source stage: YARN, GREY_FABRIC, DYED_FABRIC, CUT_PANELS")
    input_item_category = models.CharField(max_length=100, help_text="GREY_YARN, DYED_YARN, GREY_FABRIC, DYED_FABRIC, PANELS")
    input_unit_type = models.CharField(max_length=50, default="KG", help_text="BAG_WT_KG, ROLL_WT_KG, PIECES, METERS")

    output_to_stage = models.CharField(max_length=50, help_text="Target stage: GREY_FABRIC, DYED_FABRIC, CUT_PANELS, GARMENTS")
    output_item_category = models.CharField(max_length=100, help_text="GREY_FABRIC, DYED_FABRIC, CUT_PANELS, GARMENT")
    output_unit_type = models.CharField(max_length=50, default="KG", help_text="ROLL_WT_KG, PIECES, BOXES")

    # Standards & Tolerances
    standard_loss_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("2.00"))
    standard_rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"), help_text="Standard rate per unit")

    has_recipe = models.BooleanField(default=False, help_text="True if process requires chemical/dye recipe (e.g. Dyeing)")
    has_shrinkage = models.BooleanField(default=False, help_text="True if process monitors shrinkage (e.g. Dyeing, Compacting)")
    has_sizes = models.BooleanField(default=False, help_text="True if process requires size breakdown (e.g. Cutting, Stitching)")

    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    status = models.IntegerField(default=1)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_process_stages")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_process_stages")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "mx_process_stage"
        verbose_name = "Process Stage Master"
        verbose_name_plural = "Process Stage Masters"
        unique_together = ("company", "code")
        ordering = ["sequence_order", "name"]

    def __str__(self):
        return f"{self.name} [{self.code}] ({self.input_from_stage} -> {self.output_to_stage})"


class parent_process_program_table(UppercaseModel):
    """
    Universal Process Program: tm_process_program
    Unified production order / job card for any manufacturing stage:
    Knitting, Dyeing, Compacting, Cutting, Printing, Stitching, etc.
    """
    program_number = models.CharField(max_length=35, unique=True, db_index=True)
    program_date = models.DateField(db_index=True, help_text="Stored as YMD, displayed as DMY")

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="process_programs")
    cfyear = models.ForeignKey(FinancialYear, on_delete=models.PROTECT, related_name="process_programs")
    process_stage = models.ForeignKey(parent_process_stage_table, on_delete=models.PROTECT, related_name="programs")
    job_worker = models.ForeignKey(PartyMaster, on_delete=models.PROTECT, related_name="process_programs", help_text="Knitter, Dyer, Cutter, Job Worker")

    source_warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="outward_process_programs", help_text="Source raw material godown")
    dest_warehouse = models.ForeignKey(WarehouseMaster, on_delete=models.PROTECT, related_name="inward_process_programs", help_text="Destination finished godown")

    # Dynamic Input Definition
    input_from = models.CharField(max_length=50, help_text="Source stage: YARN, GREY_FABRIC, DYED_FABRIC, CUT_PANEL")
    input_item = models.CharField(max_length=200, help_text="Input item description (e.g. 30s Cotton Combed Yarn, Grey Single Jersey)")
    input_type = models.CharField(max_length=50, help_text="Unit type: BAG_WT_KG, ROLL_WT_KG, PIECES, METERS")
    input_units = models.IntegerField(default=0, help_text="Bags / Rolls / Bundles count")
    input_quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Total input weight (Kg) or pieces")

    # Dynamic Output Definition
    output_to = models.CharField(max_length=50, help_text="Destination stage: GREY_FABRIC, DYED_FABRIC, CUT_PANEL, GARMENT")
    output_item = models.CharField(max_length=200, help_text="Output item description (e.g. 30s SJ Grey Fabric, Navy Blue Fabric, T-Shirt Panels)")
    output_type = models.CharField(max_length=50, help_text="Unit type: ROLL_WT_KG, PIECES, BOXES")
    expected_output_units = models.IntegerField(default=0, help_text="Expected rolls or pieces count")
    expected_output_qty = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Calculated output weight / pieces")
    received_output_units = models.IntegerField(default=0, help_text="Actual received rolls or pieces count")
    received_output_qty = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Cumulative actual received weight (Kg) or pieces")

    # Process Loss & Technical Parameters
    planned_loss_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("2.00"), help_text="Planned process loss %")
    dia = models.CharField(max_length=50, blank=True, help_text="Dia / Width (inches or cm)")
    gsm = models.PositiveIntegerField(default=0, help_text="Finished or target GSM")
    gauge = models.CharField(max_length=50, blank=True, help_text="Machine Gauge (e.g. 24GG, 28GG)")
    loop_length = models.CharField(max_length=50, blank=True, help_text="Loop length (e.g. 2.70mm)")

    # Shrinkage & Lab Dip (Dyeing / Compacting specific)
    length_shrinkage_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    width_shrinkage_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    spirality_tolerance_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    lab_dip_no = models.CharField(max_length=50, blank=True, help_text="Lab dip reference card number")
    light_source = models.CharField(max_length=50, blank=True, default="D65", help_text="D65, TL84, CWF")
    dye_class = models.CharField(max_length=50, blank=True, default="REACTIVE", help_text="Reactive, Disperse, Vat")

    # Commercials & Pricing
    rate = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"), help_text="Job rate per unit (INR)")
    amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Job charges subtotal")
    tax_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("5.00"), help_text="GST %")
    tax_amount = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))
    grand_total = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"))

    # Status & Audit
    status = models.IntegerField(default=ProcessProgramStatus.DRAFT, choices=ProcessProgramStatus.CHOICES, db_index=True)
    is_authorized = models.IntegerField(default=0, help_text="0 = Draft, 1 = Authorized")
    remarks = models.CharField(max_length=255, blank=True)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_process_programs")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="updated_process_programs")
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_process_program"
        verbose_name = "Production Process Program"
        verbose_name_plural = "Production Process Programs"
        ordering = ["-program_date", "-id"]
        indexes = [
            models.Index(fields=["company", "status", "program_date"]),
            models.Index(fields=["company", "process_stage", "status"]),
        ]

    def __str__(self):
        return f"{self.program_number} [{self.process_stage.name}] -> {self.job_worker.name} ({self.input_quantity} {self.input_type})"

    def clean(self):
        if self.input_quantity:
            qty = Decimal(str(self.input_quantity))
            loss_p = Decimal(str(self.planned_loss_percent or 0)) / Decimal("100.00")
            self.expected_output_qty = (qty * (Decimal("1.000") - loss_p)).quantize(Decimal("0.001"))

            if self.rate:
                r = Decimal(str(self.rate))
                self.amount = (qty * r).quantize(Decimal("0.001"))
                tax_p = Decimal(str(self.tax_percent or 0)) / Decimal("100.00")
                self.tax_amount = (self.amount * tax_p).quantize(Decimal("0.001"))
                self.grand_total = self.amount + self.tax_amount

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self, user=None):
        self.status = ProcessProgramStatus.CANCELLED
        self.updated_by = user
        self.save(update_fields=["status", "updated_by", "updated_on"])


class child_process_program_input_table(UppercaseModel):
    """
    Process Program Input Lines: tx_process_program_input
    Breakdown of raw materials allocated to this job order:
    - Yarn counts & blend % for Knitting
    - Grey fabric rolls & lot numbers for Dyeing
    - Fabric rolls / lay plies for Cutting
    """
    tm_program = models.ForeignKey(parent_process_program_table, on_delete=models.CASCADE, related_name="input_lines", db_column="tm_program_id")
    source_lot_or_roll_no = models.CharField(max_length=60, blank=True, help_text="Origin lot no, roll no, or batch no")
    item_code = models.CharField(max_length=50, blank=True)
    item_name = models.CharField(max_length=150, help_text="e.g. 30s Cotton Combed / Lot-SJ-01")
    blend_ratio_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("100.00"))
    units = models.IntegerField(default=0, help_text="Bags / Rolls / Layers count")
    quantity = models.DecimalField(max_digits=20, decimal_places=3, default=Decimal("0.000"), help_text="Allocated weight (Kg) or pieces")
    remarks = models.CharField(max_length=150, blank=True)
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_process_program_input"
        verbose_name = "Process Program Input Item"
        verbose_name_plural = "Process Program Input Items"

    def __str__(self):
        return f"{self.item_name} ({self.quantity} Kg / {self.units} units)"


class child_process_program_recipe_table(UppercaseModel):
    """
    Process Program Chemical / Dye Recipe: tx_process_program_recipe
    Dyestuffs, chemicals, and auxiliaries planned for wet processing (Dyeing, Washing, Printing).
    """
    tm_program = models.ForeignKey(parent_process_program_table, on_delete=models.CASCADE, related_name="recipe_lines", db_column="tm_program_id")
    item_type = models.CharField(max_length=40, default="DYESTUFF", help_text="DYESTUFF, CHEMICAL, AUXILIARY")
    item_name = models.CharField(max_length=150, help_text="e.g. Reactive Blue RGB, Caustic Soda, Softener")
    dosage_unit = models.CharField(max_length=30, default="PERCENTAGE", help_text="PERCENTAGE (%), GPL (g/l)")
    dosage_value = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal("0.0000"))
    process_step = models.CharField(max_length=50, blank=True, help_text="SCOURING, BLEACHING, DYEING, SOAPING, FINISHING")
    remarks = models.CharField(max_length=150, blank=True)
    status = models.IntegerField(default=1)

    class Meta:
        db_table = "tx_process_program_recipe"
        verbose_name = "Process Program Recipe Item"
        verbose_name_plural = "Process Program Recipe Items"

    def __str__(self):
        return f"{self.item_name} - {self.dosage_value} {self.dosage_unit} [{self.process_step}]"


class JobWorkMaster(UppercaseModel):
    """
    Job Work Operation Master: tm_job_work
    Centralized catalog of subcontract operations across fabric processing and garmenting:
    Circular Knitting, Soft-flow Dyeing, Printing, Cutting, Stitching, Finishing.
    Configures operational lead times (procurement, processing, inspection, transportation),
    order quantity thresholds (MOQ, max capacity, standard batch size), and benchmark rates.
    """
    company_id = models.BigIntegerField(db_index=True)
    job_work_code = models.CharField(max_length=50, db_index=True, help_text="e.g. JW-KNIT-SJ-24, JW-DYE-REACT-DK")
    job_work_name = models.CharField(max_length=150, help_text="e.g. Single Jersey 24GG Knitting Conversion")
    process_stage_id = models.BigIntegerField(db_index=True, help_text="Reference to mx_process_stage.id")
    job_work_category = models.CharField(
        max_length=40,
        db_index=True,
        choices=[
            ("KNITTING", "Circular / Flat Knitting"),
            ("DYEING", "Fabric Dyeing & Processing"),
            ("COMPACTING", "Compacting & Heat Setting"),
            ("PRINTING", "Screen / Rotary Printing"),
            ("CUTTING", "Fabric Lay Cutting"),
            ("STITCHING", "Garment CMT Assembly"),
            ("FINISHING", "Washing, Ironing & Packing"),
        ]
    )
    material_type = models.CharField(
        max_length=40,
        db_index=True,
        choices=[
            ("YARN", "Raw Yarn"),
            ("GREY_FABRIC", "Grey Fabric Rolls"),
            ("DYED_FABRIC", "Dyed / Finished Fabric"),
            ("CUT_PANEL", "Cut Garment Panels"),
            ("GARMENT", "Semi/Finished Garments"),
        ],
        default="GREY_FABRIC"
    )
    description = models.TextField(blank=True, null=True)
    uom_id = models.BigIntegerField(db_index=True, help_text="Reference to mx_uom.id (KG, MTR, PCS)")

    # Order Quantity Configuration
    min_order_qty = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("100.000"), help_text="Minimum Order Quantity (MOQ)")
    max_order_qty = models.DecimalField(max_digits=18, decimal_places=3, null=True, blank=True, help_text="Maximum Order Capacity per batch/window")
    standard_batch_qty = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"), help_text="Standard batch / vessel run size")

    # Time & Lead-Time Configuration (Days)
    procurement_days = models.PositiveIntegerField(default=0, help_text="Raw material staging & transit buffer (days)")
    processing_days = models.PositiveIntegerField(default=0, help_text="Standard production cycle turnaround time (days)")
    quality_inspection_days = models.PositiveIntegerField(default=0, help_text="Inward batch QC & lab testing turnaround (days)")
    transportation_days = models.PositiveIntegerField(default=0, help_text="Inter-facility road transit buffer (days)")
    total_estimated_lead_time = models.PositiveIntegerField(default=0, help_text="Auto-computed sequential sum (days)")
    standard_delivery_days = models.PositiveIntegerField(default=0, help_text="Contractual delivery promise SLA (days)")

    # Commercial Configuration
    standard_rate = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"), help_text="Benchmark subcontract charge per UOM (INR)")
    rate_valid_from = models.DateField(null=True, blank=True)
    rate_valid_to = models.DateField(null=True, blank=True)

    is_active = models.BooleanField(default=True, db_index=True)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    record_status = models.CharField(max_length=1, default="A", db_index=True)  # 'A'=Active, 'I'=Inactive, 'D'=Deleted
    created_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_job_work"
        verbose_name = "Job Work Master"
        verbose_name_plural = "Job Work Masters"
        ordering = ["job_work_code"]
        indexes = [
            models.Index(fields=["company_id", "job_work_category", "record_status"]),
            models.Index(fields=["company_id", "material_type", "record_status"]),
            models.Index(fields=["company_id", "process_stage_id", "record_status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["company_id", "job_work_code"],
                condition=~models.Q(record_status="D"),
                name="uq_tm_job_work_code"
            )
        ]

    def __str__(self):
        return f"{self.job_work_code} - {self.job_work_name} ({self.total_estimated_lead_time}d lead time)"

    def clean(self):
        if self.min_order_qty is not None and self.min_order_qty <= Decimal("0.000"):
            from core.exceptions import ValidationError
            raise ValidationError("Minimum Order Quantity (MOQ) must be greater than zero.")

        if self.max_order_qty is not None and self.min_order_qty is not None:
            if self.max_order_qty < self.min_order_qty:
                from core.exceptions import ValidationError
                raise ValidationError("Maximum Order Quantity cannot be less than Minimum Order Quantity (MOQ).")

        self.total_estimated_lead_time = (
            (self.procurement_days or 0)
            + (self.processing_days or 0)
            + (self.quality_inspection_days or 0)
            + (self.transportation_days or 0)
        )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self, user_id=None):
        self.record_status = "D"
        if user_id:
            self.updated_by = user_id
        self.save(update_fields=["record_status", "updated_by", "updated_at"])


class JobWorkPartyConfiguration(UppercaseModel):
    """
    Job Worker Specific Planning & Commercial Configuration: tm_job_work_party_config
    Binds an external job worker (knitter, dyer, printer, cutter, stitcher) to a specific
    Job Work Operation with negotiated capacity, MOQ, unit rates, and turnaround times.
    """
    company_id = models.BigIntegerField(db_index=True)
    job_work_id = models.BigIntegerField(db_index=True, help_text="Reference to tm_job_work.id")
    party_id = models.BigIntegerField(db_index=True, help_text="Reference to mx_party.id (Subcontract Job Worker)")
    uom_id = models.BigIntegerField(db_index=True, help_text="Reference to mx_uom.id")

    # Vendor-Specific Capacity & Thresholds
    min_order_qty = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("100.000"), help_text="Vendor negotiated MOQ")
    max_order_qty = models.DecimalField(max_digits=18, decimal_places=3, null=True, blank=True, help_text="Vendor maximum order capacity ceiling")
    daily_capacity_qty = models.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"), help_text="Vendor daily throughput capacity")

    # Vendor-Specific Lead Times (Days)
    procurement_days = models.PositiveIntegerField(default=0, help_text="Material transit lead time to vendor unit (days)")
    processing_days = models.PositiveIntegerField(default=0, help_text="Vendor production conversion turnaround time (days)")
    quality_inspection_days = models.PositiveIntegerField(default=0, help_text="Vendor lot QC inspection turnaround (days)")
    transportation_days = models.PositiveIntegerField(default=0, help_text="Vendor finished goods return logistics (days)")
    total_estimated_lead_time = models.PositiveIntegerField(default=0, help_text="Auto-computed total sequential TAT (days)")

    # Commercial Agreement
    agreed_rate = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"), help_text="Agreed subcontract conversion rate per UOM (INR)")
    small_lot_surcharge = models.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"), help_text="Extra surcharge per unit when order qty is below MOQ")
    allowed_loss_percent = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), help_text="Contractual allowed process loss %")

    effective_from = models.DateField(db_index=True)
    effective_to = models.DateField(db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    remarks = models.CharField(max_length=255, blank=True, null=True)

    record_status = models.CharField(max_length=1, default="A", db_index=True)
    created_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tm_job_work_party_config"
        verbose_name = "Job Work Party Configuration"
        verbose_name_plural = "Job Work Party Configurations"
        ordering = ["-effective_from", "-id"]
        indexes = [
            models.Index(fields=["company_id", "job_work_id", "party_id", "record_status"]),
            models.Index(fields=["company_id", "effective_from", "effective_to", "record_status"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["company_id", "job_work_id", "party_id"],
                condition=models.Q(record_status="A"),
                name="uq_tm_job_work_party_active"
            )
        ]

    def __str__(self):
        return f"PartyConfig: JW #{self.job_work_id} -> Party #{self.party_id} @ Rs.{self.agreed_rate} ({self.total_estimated_lead_time}d)"

    def clean(self):
        if self.min_order_qty is not None and self.min_order_qty <= Decimal("0.000"):
            from core.exceptions import ValidationError
            raise ValidationError("Minimum Order Quantity (MOQ) must be greater than zero.")

        if self.max_order_qty is not None and self.min_order_qty is not None:
            if self.max_order_qty < self.min_order_qty:
                from core.exceptions import ValidationError
                raise ValidationError("Maximum Order Quantity cannot be less than Minimum Order Quantity (MOQ).")

        if self.effective_from and self.effective_to and self.effective_from > self.effective_to:
            from core.exceptions import ValidationError
            raise ValidationError("effective_from date cannot be after effective_to date.")

        self.total_estimated_lead_time = (
            (self.procurement_days or 0)
            + (self.processing_days or 0)
            + (self.quality_inspection_days or 0)
            + (self.transportation_days or 0)
        )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def soft_delete(self, user_id=None):
        self.record_status = "D"
        if user_id:
            self.updated_by = user_id
        self.save(update_fields=["record_status", "updated_by", "updated_at"])
