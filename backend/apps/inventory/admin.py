from __future__ import annotations
from django.contrib import admin
from apps.inventory.models import (
    yarn_stock_table, parent_yarn_inward_table, child_yarn_inward_table,
    parent_yarn_outward_table, child_yarn_outward_table
)


@admin.register(yarn_stock_table)
class YarnStockAdmin(admin.ModelAdmin):
    list_display = (
        'warehouse', 'yarn_type', 'yarn_count', 'mill', 'color_shade',
        'lot_no', 'balance_bag', 'balance_quantity', 'inward_quantity', 'outward_quantity'
    )
    list_filter = ('yarn_type', 'warehouse', 'yarn_count', 'mill')
    search_fields = ('lot_no', 'yarn_count__count', 'mill__name')
    readonly_fields = (
        'inward_bag', 'inward_quantity', 'outward_bag', 'outward_quantity',
        'sales_bag', 'sales_quantity', 'sales_return_bag', 'sales_return_quantity',
        'balance_bag', 'balance_quantity', 'created_on', 'updated_on'
    )


class ChildYarnInwardInline(admin.TabularInline):
    model = child_yarn_inward_table
    extra = 1
    fields = ('yarn_count', 'color_shade', 'lot_no', 'bag', 'per_bag', 'gross_wt', 'tare_wt', 'net_wt', 'rate', 'amount')


@admin.register(parent_yarn_inward_table)
class ParentYarnInwardAdmin(admin.ModelAdmin):
    list_display = (
        'inward_number', 'inward_date', 'yarn_type', 'party', 'mill',
        'yarn_count', 'bag', 'net_wt', 'rate', 'amount', 'po'
    )
    list_filter = ('yarn_type', 'inward_date', 'warehouse', 'mill')
    search_fields = ('inward_number', 'dc_number', 'mill__name', 'party__name')
    readonly_fields = ('net_wt', 'amount', 'created_on', 'updated_on')
    inlines = [ChildYarnInwardInline]


class ChildYarnOutwardInline(admin.TabularInline):
    model = child_yarn_outward_table
    extra = 1
    fields = ('yarn_count', 'color_shade', 'mill', 'lot_no', 'bag', 'quantity', 'remarks')


@admin.register(parent_yarn_outward_table)
class ParentYarnOutwardAdmin(admin.ModelAdmin):
    list_display = (
        'outward_number', 'outward_date', 'outward_type', 'yarn_type',
        'destination_party', 'yarn_count', 'bag', 'quantity'
    )
    list_filter = ('outward_type', 'yarn_type', 'outward_date', 'warehouse')
    search_fields = ('outward_number', 'destination_party__name', 'vehicle_no')
    readonly_fields = ('created_on', 'updated_on')
    inlines = [ChildYarnOutwardInline]
