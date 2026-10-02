from __future__ import annotations
from rest_framework import serializers
from apps.inventory.models import (
    yarn_stock_table, parent_yarn_inward_table, child_yarn_inward_table,
    parent_yarn_outward_table, child_yarn_outward_table
)


class YarnStockSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)
    mill_name = serializers.CharField(source='mill.name', read_only=True)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)
    yarn_type_display = serializers.CharField(source='get_yarn_type_display', read_only=True)

    class Meta:
        model = yarn_stock_table
        fields = [
            'id', 'company', 'warehouse', 'warehouse_name', 'yarn_type',
            'yarn_type_display', 'yarn_count', 'yarn_count_name', 'mill',
            'mill_name', 'color_shade', 'color_shade_name', 'lot_no',
            'inward_bag', 'inward_quantity', 'outward_bag', 'outward_quantity',
            'sales_bag', 'sales_quantity', 'sales_return_bag', 'sales_return_quantity',
            'balance_bag', 'balance_quantity', 'updated_on'
        ]


class ChildYarnInwardSerializer(serializers.ModelSerializer):
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)

    class Meta:
        model = child_yarn_inward_table
        fields = [
            'id', 'tm_inward', 'yarn_count', 'yarn_count_name', 'color_shade',
            'color_shade_name', 'lot_no', 'bag', 'per_bag', 'gross_wt',
            'tare_wt', 'net_wt', 'rate', 'amount', 'status'
        ]


class ParentYarnInwardSerializer(serializers.ModelSerializer):
    party_name = serializers.CharField(source='party.name', read_only=True)
    mill_name = serializers.CharField(source='mill.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)
    po_number = serializers.CharField(source='po.po_number', read_only=True, default=None)
    outward_number = serializers.CharField(source='outward.outward_number', read_only=True, default=None)
    yarn_type_display = serializers.CharField(source='get_yarn_type_display', read_only=True)
    inward_source_display = serializers.CharField(source='get_inward_source_display', read_only=True)
    line_items = ChildYarnInwardSerializer(many=True, read_only=True)

    class Meta:
        model = parent_yarn_inward_table
        fields = [
            'id', 'inward_number', 'inward_date', 'inward_source', 'inward_source_display',
            'dc_number', 'dc_date', 'vehicle_no', 'yarn_type', 'yarn_type_display',
            'po', 'po_number', 'outward', 'outward_number',
            'company', 'cfyear', 'party', 'party_name', 'mill', 'mill_name',
            'warehouse', 'warehouse_name', 'yarn_count', 'yarn_count_name',
            'color_shade', 'color_shade_name', 'lot_no', 'bag', 'per_bag',
            'gross_wt', 'tare_wt', 'net_wt', 'rate', 'amount',
            'process_loss_wt', 'process_loss_percent', 'dyeing_rate', 'dyeing_charges',
            'remarks', 'is_authorized', 'status', 'created_on', 'updated_on', 'line_items'
        ]
        read_only_fields = ['id', 'company', 'net_wt', 'amount', 'dyeing_charges', 'created_on', 'updated_on']


class ParentYarnOutwardSerializer(serializers.ModelSerializer):
    destination_party_name = serializers.CharField(source='destination_party.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)
    mill_name = serializers.CharField(source='mill.name', read_only=True)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)
    outward_type_display = serializers.CharField(source='get_outward_type_display', read_only=True)
    yarn_type_display = serializers.CharField(source='get_yarn_type_display', read_only=True)

    class Meta:
        model = parent_yarn_outward_table
        fields = [
            'id', 'outward_number', 'outward_date', 'outward_type',
            'outward_type_display', 'company', 'cfyear', 'warehouse',
            'warehouse_name', 'destination_party', 'destination_party_name',
            'yarn_type', 'yarn_type_display', 'yarn_count', 'yarn_count_name',
            'mill', 'mill_name', 'color_shade', 'color_shade_name', 'lot_no',
            'bag', 'quantity', 'received_quantity', 'remaining_quantity', 'is_complete',
            'vehicle_no', 'driver_name', 'remarks', 'is_authorized', 'status',
            'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'company', 'received_quantity', 'remaining_quantity', 'created_on', 'updated_on']

