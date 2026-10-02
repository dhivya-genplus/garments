from rest_framework import serializers
from apps.purchase.models import (
    parent_po_table, child_po_table, yarn_po_delivery_table,
    yarn_po_balance_table, yarn_po_sum_table, yarn_po_delivery_sum_table
)


class ChildPOSerializer(serializers.ModelSerializer):
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)
    yarn_type_display = serializers.CharField(source='get_yarn_type_display', read_only=True)

    class Meta:
        model = child_po_table
        fields = [
            'id', 'tm_po', 'yarn_type', 'yarn_type_display', 'yarn_count',
            'yarn_count_name', 'color_shade', 'color_shade_name', 'bag',
            'per_bag', 'quantity', 'gross_wt', 'actual_rate', 'discount',
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
            'color_shade', 'color_shade_name', 'name', 'company', 'cfyear',
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
