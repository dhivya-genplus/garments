from decimal import Decimal
from rest_framework import serializers
from apps.process.models import (
    parent_process_stage_table,
    parent_process_program_table,
    child_process_program_input_table,
    child_process_program_recipe_table,
    JobWorkMaster,
    JobWorkPartyConfiguration,
)
from apps.masters.models import UnitOfMeasurement, PartyMaster


class ChildProcessProgramInputSerializer(serializers.ModelSerializer):
    class Meta:
        model = child_process_program_input_table
        fields = [
            "id",
            "source_lot_or_roll_no",
            "item_code",
            "item_name",
            "blend_ratio_percent",
            "units",
            "quantity",
            "remarks",
        ]


class ChildProcessProgramRecipeSerializer(serializers.ModelSerializer):
    class Meta:
        model = child_process_program_recipe_table
        fields = [
            "id",
            "item_type",
            "item_name",
            "dosage_unit",
            "dosage_value",
            "process_step",
            "remarks",
        ]


class ParentProcessStageSerializer(serializers.ModelSerializer):
    class Meta:
        model = parent_process_stage_table
        fields = [
            "id",
            "name",
            "code",
            "sequence_order",
            "input_from_stage",
            "input_item_category",
            "input_unit_type",
            "output_to_stage",
            "output_item_category",
            "output_unit_type",
            "standard_loss_percent",
            "standard_rate",
            "has_recipe",
            "has_shrinkage",
            "has_sizes",
            "description",
            "is_active",
        ]
        read_only_fields = ["id"]


class ParentProcessProgramSerializer(serializers.ModelSerializer):
    program_date = serializers.DateField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"])
    process_name = serializers.CharField(source="process_stage.name", read_only=True)
    process_code = serializers.CharField(source="process_stage.code", read_only=True)
    job_worker_name = serializers.CharField(source="job_worker.name", read_only=True)
    source_warehouse_name = serializers.CharField(source="source_warehouse.name", read_only=True)
    dest_warehouse_name = serializers.CharField(source="dest_warehouse.name", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    input_lines = ChildProcessProgramInputSerializer(many=True, read_only=True)
    recipe_lines = ChildProcessProgramRecipeSerializer(many=True, read_only=True)

    class Meta:
        model = parent_process_program_table
        fields = [
            "id",
            "program_number",
            "program_date",
            "process_stage",
            "process_name",
            "process_code",
            "job_worker",
            "job_worker_name",
            "source_warehouse",
            "source_warehouse_name",
            "dest_warehouse",
            "dest_warehouse_name",
            "input_from",
            "input_item",
            "input_type",
            "input_units",
            "input_quantity",
            "output_to",
            "output_item",
            "output_type",
            "expected_output_units",
            "expected_output_qty",
            "received_output_units",
            "received_output_qty",
            "planned_loss_percent",
            "dia",
            "gsm",
            "gauge",
            "loop_length",
            "length_shrinkage_percent",
            "width_shrinkage_percent",
            "spirality_tolerance_percent",
            "lab_dip_no",
            "light_source",
            "dye_class",
            "rate",
            "amount",
            "tax_percent",
            "tax_amount",
            "grand_total",
            "status",
            "status_display",
            "is_authorized",
            "remarks",
            "input_lines",
            "recipe_lines",
            "created_on",
            "updated_on",
        ]
        read_only_fields = [
            "id",
            "expected_output_qty",
            "received_output_units",
            "received_output_qty",
            "amount",
            "tax_amount",
            "grand_total",
            "created_on",
            "updated_on",
        ]


class JobWorkSerializer(serializers.ModelSerializer):
    rate_valid_from = serializers.DateField(
        format="%d/%m/%Y", input_formats=["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"], required=False, allow_null=True
    )
    rate_valid_to = serializers.DateField(
        format="%d/%m/%Y", input_formats=["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"], required=False, allow_null=True
    )
    process_stage_name = serializers.SerializerMethodField()
    process_stage_code = serializers.SerializerMethodField()
    uom_code = serializers.SerializerMethodField()
    job_work_category_display = serializers.CharField(source="get_job_work_category_display", read_only=True)
    material_type_display = serializers.CharField(source="get_material_type_display", read_only=True)

    class Meta:
        model = JobWorkMaster
        fields = [
            "id",
            "company_id",
            "job_work_code",
            "job_work_name",
            "process_stage_id",
            "process_stage_name",
            "process_stage_code",
            "job_work_category",
            "job_work_category_display",
            "material_type",
            "material_type_display",
            "description",
            "uom_id",
            "uom_code",
            "min_order_qty",
            "max_order_qty",
            "standard_batch_qty",
            "procurement_days",
            "processing_days",
            "quality_inspection_days",
            "transportation_days",
            "total_estimated_lead_time",
            "standard_delivery_days",
            "standard_rate",
            "rate_valid_from",
            "rate_valid_to",
            "is_active",
            "remarks",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "total_estimated_lead_time",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
        ]

    def get_process_stage_name(self, obj):
        stage = parent_process_stage_table.objects.filter(id=obj.process_stage_id).first()
        return stage.name if stage else None

    def get_process_stage_code(self, obj):
        stage = parent_process_stage_table.objects.filter(id=obj.process_stage_id).first()
        return stage.code if stage else None

    def get_uom_code(self, obj):
        uom = UnitOfMeasurement.objects.filter(id=obj.uom_id).first()
        return uom.code if uom else None


class JobWorkPartyConfigSerializer(serializers.ModelSerializer):
    effective_from = serializers.DateField(
        format="%d/%m/%Y", input_formats=["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]
    )
    effective_to = serializers.DateField(
        format="%d/%m/%Y", input_formats=["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"]
    )
    job_work_code = serializers.SerializerMethodField()
    job_work_name = serializers.SerializerMethodField()
    party_name = serializers.SerializerMethodField()
    party_code = serializers.SerializerMethodField()
    uom_code = serializers.SerializerMethodField()

    class Meta:
        model = JobWorkPartyConfiguration
        fields = [
            "id",
            "company_id",
            "job_work_id",
            "job_work_code",
            "job_work_name",
            "party_id",
            "party_name",
            "party_code",
            "uom_id",
            "uom_code",
            "min_order_qty",
            "max_order_qty",
            "daily_capacity_qty",
            "procurement_days",
            "processing_days",
            "quality_inspection_days",
            "transportation_days",
            "total_estimated_lead_time",
            "agreed_rate",
            "small_lot_surcharge",
            "allowed_loss_percent",
            "effective_from",
            "effective_to",
            "is_active",
            "remarks",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "total_estimated_lead_time",
            "created_by",
            "created_at",
            "updated_by",
            "updated_at",
        ]

    def get_job_work_code(self, obj):
        jw = JobWorkMaster.objects.filter(id=obj.job_work_id).first()
        return jw.job_work_code if jw else None

    def get_job_work_name(self, obj):
        jw = JobWorkMaster.objects.filter(id=obj.job_work_id).first()
        return jw.job_work_name if jw else None

    def get_party_name(self, obj):
        p = PartyMaster.objects.filter(id=obj.party_id).first()
        return p.name if p else None

    def get_party_code(self, obj):
        p = PartyMaster.objects.filter(id=obj.party_id).first()
        return p.code if p else None

    def get_uom_code(self, obj):
        uom = UnitOfMeasurement.objects.filter(id=obj.uom_id).first()
        return uom.code if uom else None


class JobWorkOrderValidationSerializer(serializers.Serializer):
    job_work_id = serializers.IntegerField(required=True)
    quantity = serializers.DecimalField(max_digits=18, decimal_places=3, required=True)
    party_id = serializers.IntegerField(required=False, allow_null=True)
    uom_id = serializers.IntegerField(required=False, allow_null=True)


class JobWorkScheduleCalculationSerializer(serializers.Serializer):
    job_work_id = serializers.IntegerField(required=True)
    order_date = serializers.DateField(
        format="%d/%m/%Y", input_formats=["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"], required=True
    )
    quantity = serializers.DecimalField(max_digits=18, decimal_places=3, required=False, allow_null=True)
    party_id = serializers.IntegerField(required=False, allow_null=True)
    is_fast_track = serializers.BooleanField(default=False)
