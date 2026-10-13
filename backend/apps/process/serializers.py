from rest_framework import serializers
from apps.process.models import (
    parent_process_stage_table,
    parent_process_program_table,
    child_process_program_input_table,
    child_process_program_recipe_table,
)


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
