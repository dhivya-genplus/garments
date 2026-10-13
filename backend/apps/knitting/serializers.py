from __future__ import annotations
from rest_framework import serializers
from apps.knitting.models import (
    parent_knitting_program_table,
    child_knitting_program_yarn_table,
    grey_fabric_stock_table,
    parent_grey_fabric_inward_table,
    child_grey_fabric_inward_table,
    parent_grey_fabric_outward_table,
    child_grey_fabric_outward_table,
    parent_grey_po_table,
    child_grey_po_table,
    parent_grey_fabric_sales_table,
    child_grey_fabric_sales_table,
    parent_grey_fabric_sales_return_table,
    child_grey_fabric_sales_return_table,
)


class ChildKnittingProgramYarnSerializer(serializers.ModelSerializer):
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)
    yarn_type_display = serializers.CharField(source='get_yarn_type_display', read_only=True)

    class Meta:
        model = child_knitting_program_yarn_table
        fields = [
            'id', 'tm_program', 'yarn_count', 'yarn_count_name', 'color_shade',
            'color_shade_name', 'yarn_type', 'yarn_type_display',
            'blend_ratio_percent', 'planned_quantity', 'issued_quantity', 'status'
        ]


class ParentKnittingProgramSerializer(serializers.ModelSerializer):
    knitter_name = serializers.CharField(source='knitter.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    fabric_name = serializers.CharField(source='fabric.fabric_name', read_only=True)
    fabric_type_name = serializers.CharField(source='fabric_type.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    yarn_lines = ChildKnittingProgramYarnSerializer(many=True, read_only=True)

    class Meta:
        model = parent_knitting_program_table
        fields = [
            'id', 'program_number', 'program_date', 'delivery_date',
            'company', 'cfyear', 'knitter', 'knitter_name',
            'warehouse', 'warehouse_name', 'fabric', 'fabric_name',
            'fabric_type', 'fabric_type_name', 'dia', 'gauge', 'gsm', 'loop_length',
            'planned_rolls', 'planned_fabric_quantity', 'expected_loss_percent',
            'total_yarn_required', 'issued_yarn_quantity', 'received_fabric_quantity',
            'knitting_rate', 'total_knitting_amount', 'status', 'status_display',
            'remarks', 'yarn_lines', 'created_on', 'updated_on'
        ]


class GreyFabricStockSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    fabric_name = serializers.CharField(source='fabric.fabric_name', read_only=True)
    fabric_type_name = serializers.CharField(source='fabric_type.name', read_only=True)

    class Meta:
        model = grey_fabric_stock_table
        fields = [
            'id', 'company', 'warehouse', 'warehouse_name', 'fabric', 'fabric_name',
            'fabric_type', 'fabric_type_name', 'dia', 'gsm', 'gauge', 'lot_no',
            'inward_rolls', 'inward_quantity', 'outward_rolls', 'outward_quantity',
            'sales_rolls', 'sales_quantity', 'sales_return_rolls', 'sales_return_quantity',
            'balance_rolls', 'balance_quantity', 'updated_on'
        ]


class ChildGreyFabricInwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = child_grey_fabric_inward_table
        fields = [
            'id', 'tm_inward', 'roll_no', 'gross_wt', 'tare_wt', 'net_wt', 'remarks', 'status'
        ]


class ParentGreyFabricInwardSerializer(serializers.ModelSerializer):
    party_name = serializers.CharField(source='party.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    fabric_name = serializers.CharField(source='fabric.fabric_name', read_only=True)
    fabric_type_name = serializers.CharField(source='fabric_type.name', read_only=True)
    knitting_program_number = serializers.CharField(source='knitting_program.program_number', read_only=True, default=None)
    inward_source_display = serializers.CharField(source='get_inward_source_display', read_only=True)
    line_items = ChildGreyFabricInwardSerializer(many=True, read_only=True)

    class Meta:
        model = parent_grey_fabric_inward_table
        fields = [
            'id', 'inward_number', 'inward_date', 'dc_number', 'dc_date', 'vehicle_no',
            'inward_source', 'inward_source_display',
            'knitting_program', 'knitting_program_number',
            'company', 'cfyear', 'party', 'party_name', 'warehouse', 'warehouse_name',
            'fabric', 'fabric_name', 'fabric_type', 'fabric_type_name',
            'dia', 'gsm', 'gauge', 'lot_no',
            'total_rolls', 'gross_wt', 'tare_wt', 'net_wt',
            'yarn_consumed_wt', 'process_loss_wt', 'process_loss_percent',
            'knitting_rate', 'knitting_charges', 'remarks', 'is_authorized', 'status',
            'line_items', 'created_on', 'updated_on'
        ]


class ChildGreyFabricOutwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = child_grey_fabric_outward_table
        fields = [
            'id', 'tm_outward', 'roll_no', 'gross_wt', 'net_wt', 'remarks', 'status'
        ]


class ParentGreyFabricOutwardSerializer(serializers.ModelSerializer):
    destination_party_name = serializers.CharField(source='destination_party.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    fabric_name = serializers.CharField(source='fabric.fabric_name', read_only=True)
    fabric_type_name = serializers.CharField(source='fabric_type.name', read_only=True)
    outward_type_display = serializers.CharField(source='get_outward_type_display', read_only=True)
    line_items = ChildGreyFabricOutwardSerializer(many=True, read_only=True)

    class Meta:
        model = parent_grey_fabric_outward_table
        fields = [
            'id', 'outward_number', 'outward_date', 'outward_type', 'outward_type_display',
            'company', 'cfyear', 'warehouse', 'warehouse_name',
            'destination_party', 'destination_party_name',
            'fabric', 'fabric_name', 'fabric_type', 'fabric_type_name',
            'dia', 'gsm', 'gauge', 'lot_no', 'rolls', 'quantity',
            'received_quantity', 'remaining_quantity', 'is_complete',
            'vehicle_no', 'driver_name', 'remarks', 'is_authorized', 'status',
            'line_items', 'created_on', 'updated_on'
        ]


class ChildGreyPOSerializer(serializers.ModelSerializer):
    fabric_name = serializers.CharField(source='fabric.fabric_name', read_only=True)
    fabric_type_name = serializers.CharField(source='fabric_type.name', read_only=True)

    class Meta:
        model = child_grey_po_table
        fields = [
            'id', 'tm_po', 'fabric', 'fabric_name', 'fabric_type', 'fabric_type_name',
            'dia', 'gsm', 'gauge', 'rolls', 'quantity', 'rate', 'amount', 'status'
        ]


class ParentGreyPOSerializer(serializers.ModelSerializer):
    party_name = serializers.CharField(source='party.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    line_items = ChildGreyPOSerializer(many=True, read_only=True)

    class Meta:
        model = parent_grey_po_table
        fields = [
            'id', 'po_number', 'po_date', 'delivery_date', 'company', 'cfyear',
            'party', 'party_name', 'warehouse', 'warehouse_name',
            'total_rolls', 'total_quantity', 'subtotal', 'tax_percent', 'tax_amount',
            'total_amount', 'is_authorized', 'status', 'remarks', 'line_items',
            'created_on', 'updated_on'
        ]


class ChildGreyFabricSalesSerializer(serializers.ModelSerializer):
    class Meta:
        model = child_grey_fabric_sales_table
        fields = [
            'id', 'tm_sales', 'roll_no', 'gross_wt', 'net_wt', 'rate', 'amount', 'remarks', 'status'
        ]


class ParentGreyFabricSalesSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    fabric_name = serializers.CharField(source='fabric.fabric_name', read_only=True)
    fabric_type_name = serializers.CharField(source='fabric_type.name', read_only=True)
    line_items = ChildGreyFabricSalesSerializer(many=True, read_only=True)

    class Meta:
        model = parent_grey_fabric_sales_table
        fields = [
            'id', 'invoice_number', 'invoice_date', 'company', 'cfyear',
            'warehouse', 'warehouse_name', 'customer', 'customer_name',
            'fabric', 'fabric_name', 'fabric_type', 'fabric_type_name',
            'dia', 'gsm', 'gauge', 'lot_no', 'rolls', 'quantity',
            'rate', 'subtotal', 'tax_percent', 'tax_amount', 'total_amount',
            'payment_terms', 'remarks', 'is_authorized', 'status',
            'line_items', 'created_on', 'updated_on'
        ]


class ChildGreyFabricSalesReturnSerializer(serializers.ModelSerializer):
    class Meta:
        model = child_grey_fabric_sales_return_table
        fields = [
            'id', 'tm_return', 'roll_no', 'gross_wt', 'net_wt', 'rate', 'amount', 'remarks', 'status'
        ]


class ParentGreyFabricSalesReturnSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    fabric_name = serializers.CharField(source='fabric.fabric_name', read_only=True)
    fabric_type_name = serializers.CharField(source='fabric_type.name', read_only=True)
    sales_invoice_number = serializers.CharField(source='sales_invoice.invoice_number', read_only=True, default=None)
    line_items = ChildGreyFabricSalesReturnSerializer(many=True, read_only=True)

    class Meta:
        model = parent_grey_fabric_sales_return_table
        fields = [
            'id', 'return_number', 'return_date', 'sales_invoice', 'sales_invoice_number',
            'company', 'cfyear', 'warehouse', 'warehouse_name', 'customer', 'customer_name',
            'fabric', 'fabric_name', 'fabric_type', 'fabric_type_name',
            'dia', 'gsm', 'gauge', 'lot_no', 'rolls', 'quantity',
            'rate', 'subtotal', 'tax_percent', 'tax_amount', 'total_amount',
            'return_reason', 'remarks', 'is_authorized', 'status',
            'line_items', 'created_on', 'updated_on'
        ]

