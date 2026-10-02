from __future__ import annotations
from rest_framework import serializers
from apps.sales.models import (
    parent_yarn_sales_table, child_yarn_sales_table,
    parent_yarn_sales_return_table, child_yarn_sales_return_table
)


class ChildYarnSalesSerializer(serializers.ModelSerializer):
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)
    mill_name = serializers.CharField(source='mill.name', read_only=True)

    class Meta:
        model = child_yarn_sales_table
        fields = [
            'id', 'tm_sales', 'yarn_count', 'yarn_count_name', 'color_shade',
            'color_shade_name', 'mill', 'mill_name', 'lot_no', 'bag',
            'per_bag', 'quantity', 'rate', 'amount', 'status'
        ]


class ParentYarnSalesSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    mill_name = serializers.CharField(source='mill.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)
    yarn_type_display = serializers.CharField(source='get_yarn_type_display', read_only=True)
    line_items = ChildYarnSalesSerializer(many=True, read_only=True)

    class Meta:
        model = parent_yarn_sales_table
        fields = [
            'id', 'invoice_number', 'invoice_date', 'yarn_type', 'yarn_type_display',
            'company', 'cfyear', 'warehouse', 'warehouse_name', 'customer',
            'customer_name', 'yarn_count', 'yarn_count_name', 'mill',
            'mill_name', 'color_shade', 'color_shade_name', 'lot_no',
            'bag', 'per_bag', 'quantity', 'rate', 'subtotal', 'tax_percent',
            'tax_amount', 'total_amount', 'payment_terms', 'remarks',
            'is_authorized', 'status', 'created_on', 'updated_on', 'line_items'
        ]
        read_only_fields = [
            'id', 'company', 'subtotal', 'tax_amount', 'total_amount',
            'created_on', 'updated_on'
        ]


class ParentYarnSalesReturnSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name', read_only=True)
    mill_name = serializers.CharField(source='mill.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)
    yarn_type_display = serializers.CharField(source='get_yarn_type_display', read_only=True)

    class Meta:
        model = parent_yarn_sales_return_table
        fields = [
            'id', 'return_number', 'return_date', 'sales_invoice',
            'company', 'cfyear', 'warehouse', 'warehouse_name', 'customer',
            'customer_name', 'yarn_type', 'yarn_type_display', 'yarn_count',
            'yarn_count_name', 'mill', 'mill_name', 'color_shade',
            'color_shade_name', 'lot_no', 'bag', 'quantity', 'rate',
            'amount', 'return_reason', 'is_authorized', 'status',
            'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'company', 'amount', 'created_on', 'updated_on']
