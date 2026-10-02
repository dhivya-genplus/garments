from __future__ import annotations
from django.contrib import admin
from apps.sales.models import (
    parent_yarn_sales_table, child_yarn_sales_table,
    parent_yarn_sales_return_table, child_yarn_sales_return_table
)


class ChildYarnSalesInline(admin.TabularInline):
    model = child_yarn_sales_table
    extra = 1
    fields = ('yarn_count', 'color_shade', 'mill', 'lot_no', 'bag', 'per_bag', 'quantity', 'rate', 'amount')


@admin.register(parent_yarn_sales_table)
class ParentYarnSalesAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'invoice_date', 'yarn_type', 'customer',
        'yarn_count', 'mill', 'bag', 'quantity', 'rate', 'total_amount'
    )
    list_filter = ('yarn_type', 'invoice_date', 'warehouse', 'customer')
    search_fields = ('invoice_number', 'customer__name', 'mill__name')
    readonly_fields = ('subtotal', 'tax_amount', 'total_amount', 'created_on', 'updated_on')
    inlines = [ChildYarnSalesInline]


class ChildYarnSalesReturnInline(admin.TabularInline):
    model = child_yarn_sales_return_table
    extra = 1
    fields = ('yarn_count', 'color_shade', 'mill', 'lot_no', 'bag', 'quantity', 'rate', 'amount')


@admin.register(parent_yarn_sales_return_table)
class ParentYarnSalesReturnAdmin(admin.ModelAdmin):
    list_display = (
        'return_number', 'return_date', 'yarn_type', 'customer',
        'yarn_count', 'bag', 'quantity', 'amount', 'sales_invoice'
    )
    list_filter = ('yarn_type', 'return_date', 'warehouse', 'customer')
    search_fields = ('return_number', 'customer__name', 'return_reason')
    readonly_fields = ('created_on', 'updated_on')
    inlines = [ChildYarnSalesReturnInline]
