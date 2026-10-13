from django.contrib import admin
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


class ChildKnittingProgramYarnInline(admin.TabularInline):
    model = child_knitting_program_yarn_table
    extra = 1
    fields = ('yarn_count', 'color_shade', 'yarn_type', 'blend_ratio_percent', 'planned_quantity', 'issued_quantity', 'status')


@admin.register(parent_knitting_program_table)
class ParentKnittingProgramAdmin(admin.ModelAdmin):
    list_display = (
        'program_number', 'program_date', 'knitter', 'fabric', 'dia', 'gsm', 'gauge',
        'planned_rolls', 'planned_fabric_quantity', 'received_fabric_quantity',
        'total_yarn_required', 'status', 'company'
    )
    list_filter = ('company', 'status', 'fabric', 'knitter', 'program_date')
    search_fields = ('program_number', 'knitter__name', 'fabric__fabric_name', 'dia')
    inlines = [ChildKnittingProgramYarnInline]
    date_hierarchy = 'program_date'


@admin.register(grey_fabric_stock_table)
class GreyFabricStockAdmin(admin.ModelAdmin):
    list_display = (
        'fabric', 'dia', 'gsm', 'gauge', 'lot_no', 'warehouse',
        'balance_rolls', 'balance_quantity', 'inward_quantity', 'outward_quantity',
        'company'
    )
    list_filter = ('company', 'warehouse', 'fabric', 'dia')
    search_fields = ('fabric__fabric_name', 'dia', 'lot_no')


class ChildGreyFabricInwardInline(admin.TabularInline):
    model = child_grey_fabric_inward_table
    extra = 1
    fields = ('roll_no', 'gross_wt', 'tare_wt', 'net_wt', 'remarks', 'status')


@admin.register(parent_grey_fabric_inward_table)
class ParentGreyFabricInwardAdmin(admin.ModelAdmin):
    list_display = (
        'inward_number', 'inward_date', 'party', 'fabric', 'dia', 'gsm',
        'total_rolls', 'net_wt', 'yarn_consumed_wt', 'process_loss_wt',
        'process_loss_percent', 'knitting_charges', 'company'
    )
    list_filter = ('company', 'party', 'warehouse', 'inward_source', 'inward_date')
    search_fields = ('inward_number', 'dc_number', 'party__name', 'fabric__fabric_name')
    inlines = [ChildGreyFabricInwardInline]
    date_hierarchy = 'inward_date'


class ChildGreyFabricOutwardInline(admin.TabularInline):
    model = child_grey_fabric_outward_table
    extra = 1
    fields = ('roll_no', 'gross_wt', 'net_wt', 'remarks', 'status')


@admin.register(parent_grey_fabric_outward_table)
class ParentGreyFabricOutwardAdmin(admin.ModelAdmin):
    list_display = (
        'outward_number', 'outward_date', 'outward_type', 'destination_party',
        'fabric', 'dia', 'rolls', 'quantity', 'company'
    )
    list_filter = ('company', 'outward_type', 'destination_party', 'warehouse', 'outward_date')
    search_fields = ('outward_number', 'destination_party__name', 'fabric__fabric_name')
    inlines = [ChildGreyFabricOutwardInline]
    date_hierarchy = 'outward_date'


class ChildGreyPOInline(admin.TabularInline):
    model = child_grey_po_table
    extra = 1
    fields = ('fabric', 'fabric_type', 'dia', 'gsm', 'gauge', 'rolls', 'quantity', 'rate', 'amount', 'status')


@admin.register(parent_grey_po_table)
class ParentGreyPOAdmin(admin.ModelAdmin):
    list_display = (
        'po_number', 'po_date', 'party', 'total_rolls', 'total_quantity',
        'total_amount', 'is_authorized', 'company'
    )
    list_filter = ('company', 'party', 'warehouse', 'is_authorized', 'po_date')
    search_fields = ('po_number', 'party__name')
    inlines = [ChildGreyPOInline]
    date_hierarchy = 'po_date'


class ChildGreyFabricSalesInline(admin.TabularInline):
    model = child_grey_fabric_sales_table
    extra = 1
    fields = ('roll_no', 'gross_wt', 'net_wt', 'rate', 'amount', 'remarks', 'status')


@admin.register(parent_grey_fabric_sales_table)
class ParentGreyFabricSalesAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'invoice_date', 'customer', 'fabric', 'dia',
        'rolls', 'quantity', 'rate', 'total_amount', 'company'
    )
    list_filter = ('company', 'customer', 'warehouse', 'invoice_date')
    search_fields = ('invoice_number', 'customer__name', 'fabric__fabric_name')
    inlines = [ChildGreyFabricSalesInline]
    date_hierarchy = 'invoice_date'


class ChildGreyFabricSalesReturnInline(admin.TabularInline):
    model = child_grey_fabric_sales_return_table
    extra = 1
    fields = ('roll_no', 'gross_wt', 'net_wt', 'rate', 'amount', 'remarks', 'status')


@admin.register(parent_grey_fabric_sales_return_table)
class ParentGreyFabricSalesReturnAdmin(admin.ModelAdmin):
    list_display = (
        'return_number', 'return_date', 'customer', 'fabric', 'dia',
        'rolls', 'quantity', 'total_amount', 'company'
    )
    list_filter = ('company', 'customer', 'warehouse', 'return_date')
    search_fields = ('return_number', 'customer__name', 'sales_invoice__invoice_number')
    inlines = [ChildGreyFabricSalesReturnInline]
    date_hierarchy = 'return_date'

