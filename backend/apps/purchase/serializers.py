from rest_framework import serializers
from core.constants import YarnDefectReasons
from apps.inventory.models import parent_yarn_inward_table
from apps.purchase.models import (
    company_yarn_type_table,
    parent_po_table, child_po_table, yarn_po_delivery_table,
    yarn_po_balance_table, yarn_po_sum_table, yarn_po_delivery_sum_table,
    parent_yarn_po_return_table, child_yarn_po_return_table,
)


class CompanyYarnTypeSerializer(serializers.ModelSerializer):
    yarn_type_display = serializers.CharField(source='get_yarn_type_display', read_only=True)

    class Meta:
        model = company_yarn_type_table
        fields = [
            'id', 'yarn_type', 'yarn_type_display', 'display_name', 'is_active',
            'requires_color_shade', 'requires_blend_ratio', 'requires_ply_twists',
            'requires_slub_pattern', 'requires_core_denier'
        ]


class ChildPOSerializer(serializers.ModelSerializer):
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)
    yarn_type_display = serializers.CharField(source='get_yarn_type_display', read_only=True)

    class Meta:
        model = child_po_table
        fields = [
            'id', 'tm_po', 'yarn_type', 'yarn_type_display', 'yarn_count',
            'yarn_count_name', 'color_shade', 'color_shade_name',
            'blend_ratio', 'ply_count', 'twists_per_inch', 'slub_pattern', 'core_denier',
            'bag', 'per_bag', 'quantity', 'gross_wt', 'actual_rate', 'discount',
            'rate', 'amount', 'remaining_bag', 'remaining_quantity',
            'remaining_amount', 'is_active', 'status'
        ]
        read_only_fields = [
            'id', 'tm_po', 'quantity', 'rate', 'amount',
            'remaining_bag', 'remaining_quantity', 'remaining_amount'
        ]


class YarnPODeliverySerializer(serializers.ModelSerializer):
    party_name = serializers.CharField(source='party.name', read_only=True)
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)

    class Meta:
        model = yarn_po_delivery_table
        fields = [
            'id', 'tm_po', 'yarn_count', 'yarn_count_name', 'party',
            'party_name', 'delivery_date', 'bag', 'bag_wt', 'quantity',
            'company', 'cfyear', 'is_active', 'status'
        ]
        read_only_fields = ['id', 'tm_po', 'quantity', 'company', 'cfyear']


class ParentPOSerializer(serializers.ModelSerializer):
    party_name = serializers.CharField(source='party.name', read_only=True)
    mill_name = serializers.CharField(source='mill.name', read_only=True)
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True, default=None)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)
    cfyear_name = serializers.CharField(source='cfyear.name', read_only=True)
    yarn_type_display = serializers.CharField(source='get_yarn_type_display', read_only=True)
    authorized_by_username = serializers.CharField(source='authorized_by.username', read_only=True, default=None)

    line_items = ChildPOSerializer(many=True, read_only=True)
    deliveries = YarnPODeliverySerializer(many=True, read_only=True)

    class Meta:
        model = parent_po_table
        fields = [
            'id', 'po_number', 'po_date', 'yarn_type', 'yarn_type_display',
            'color_shade', 'color_shade_name', 'blend_ratio', 'ply_count',
            'twists_per_inch', 'slub_pattern', 'core_denier',
            'name', 'company', 'cfyear',
            'cfyear_name', 'party', 'party_name', 'mill', 'mill_name',
            'yarn_count', 'yarn_count_name', 'bag', 'per_bag', 'quantity',
            'gross_quantity', 'rate', 'discount', 'net_rate', 'amount',
            'remarks', 'is_delivery', 'is_complete', 'is_authorized',
            'authorized_by', 'authorized_by_username', 'authorized_on',
            'is_active', 'status', 'created_by', 'updated_by',
            'created_on', 'updated_on', 'line_items', 'deliveries'
        ]
        read_only_fields = [
            'id', 'company', 'quantity', 'net_rate', 'amount',
            'is_complete', 'is_authorized', 'authorized_by', 'authorized_on',
            'created_on', 'updated_on', 'created_by', 'updated_by'
        ]


class ParentPOCreateSerializer(serializers.ModelSerializer):
    line_items = ChildPOSerializer(many=True, required=False)
    deliveries = YarnPODeliverySerializer(many=True, required=False)

    class Meta:
        model = parent_po_table
        fields = [
            'id', 'po_number', 'po_date', 'yarn_type', 'color_shade',
            'blend_ratio', 'ply_count', 'twists_per_inch', 'slub_pattern', 'core_denier',
            'name', 'cfyear', 'party', 'mill', 'yarn_count',
            'bag', 'per_bag', 'gross_quantity', 'rate', 'discount',
            'remarks', 'is_delivery', 'line_items', 'deliveries'
        ]


class YarnPOBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = yarn_po_balance_table
        fields = '__all__'


class YarnPOSumSerializer(serializers.ModelSerializer):
    class Meta:
        model = yarn_po_sum_table
        fields = '__all__'


class YarnPODeliverySumSerializer(serializers.ModelSerializer):
    class Meta:
        model = yarn_po_delivery_sum_table
        fields = '__all__'


class ChildYarnPoReturnSerializer(serializers.ModelSerializer):
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)

    class Meta:
        model = child_yarn_po_return_table
        fields = [
            'id', 'tm_return', 'yarn_count', 'yarn_count_name', 'color_shade', 'color_shade_name',
            'lot_no', 'bag', 'per_bag', 'quantity', 'rate', 'amount', 'status'
        ]
        read_only_fields = ['id', 'amount', 'quantity']


class ParentYarnPoReturnSerializer(serializers.ModelSerializer):
    po_number = serializers.CharField(source='po.po_number', read_only=True, default=None)
    inward_number = serializers.CharField(source='inward.inward_number', read_only=True, default=None)
    party_name = serializers.CharField(source='party.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)
    defect_reason_display = serializers.CharField(source='get_defect_reason_display', read_only=True)
    yarn_type_display = serializers.CharField(source='get_yarn_type_display', read_only=True)
    line_items = ChildYarnPoReturnSerializer(many=True, read_only=True)

    po = serializers.PrimaryKeyRelatedField(
        queryset=parent_po_table.objects.all(),
        required=True,
        error_messages={"required": "Upstream Yarn Purchase Order reference is mandatory."}
    )
    inward = serializers.PrimaryKeyRelatedField(
        queryset=parent_yarn_inward_table.objects.all(),
        required=True,
        error_messages={"required": "Upstream Inward GRN reference with unconsumed stock is mandatory."}
    )
    defect_reason = serializers.ChoiceField(
        choices=YarnDefectReasons.CHOICES,
        required=True,
        error_messages={"required": "Quality defect categorization code is mandatory."}
    )
    defect_notes = serializers.CharField(
        required=True,
        min_length=5,
        error_messages={
            "required": "Quality defect lab testing criteria / QC inspection findings must be documented.",
            "min_length": "Quality defect notes must be at least 5 characters long."
        }
    )

    class Meta:
        model = parent_yarn_po_return_table
        fields = [
            'id', 'return_number', 'return_date', 'company', 'cfyear',
            'party', 'party_name', 'po', 'po_number', 'inward', 'inward_number', 'warehouse', 'warehouse_name',
            'yarn_type', 'yarn_type_display', 'yarn_count', 'yarn_count_name',
            'color_shade', 'color_shade_name', 'lot_no',
            'defect_reason', 'defect_reason_display', 'defect_notes',
            'bag', 'per_bag', 'quantity', 'rate', 'subtotal',
            'tax', 'tax_percent', 'tax_amount', 'cgst_percent', 'cgst_amount',
            'sgst_percent', 'sgst_amount', 'igst_percent', 'igst_amount',
            'total_debit_amount', 'transporter_name', 'vehicle_no', 'lr_number',
            'debit_note_number', 'voucher_id', 'is_authorized', 'status',
            'created_on', 'updated_on', 'line_items'
        ]
        read_only_fields = [
            'id', 'return_number', 'subtotal', 'tax_amount', 'cgst_amount', 'sgst_amount',
            'igst_amount', 'total_debit_amount', 'debit_note_number', 'voucher_id',
            'created_on', 'updated_on'
        ]

