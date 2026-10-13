from django.contrib import admin
from apps.ledger.models import (
    tl_stock_movement,
    tm_stage_stock,
    tl_voucher,
    tl_voucher_line,
)


@admin.register(tl_stock_movement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "movement_date",
        "stage",
        "warehouse",
        "movement_type",
        "item_name",
        "lot_or_batch_no",
        "in_units",
        "in_qty",
        "out_units",
        "out_qty",
        "balance_units",
        "balance_qty",
        "total_value",
        "doc_number",
    )
    list_filter = ("stage", "movement_type", "warehouse", "movement_date")
    search_fields = ("item_name", "lot_or_batch_no", "doc_number", "remarks")
    date_hierarchy = "movement_date"
    readonly_fields = (
        "company",
        "cfyear",
        "movement_date",
        "stage",
        "warehouse",
        "party",
        "movement_type",
        "doc_type",
        "doc_number",
        "item_name",
        "lot_or_batch_no",
        "in_units",
        "in_qty",
        "out_units",
        "out_qty",
        "balance_units",
        "balance_qty",
        "unit_rate",
        "total_value",
        "remarks",
        "created_by",
        "created_on",
    )


@admin.register(tm_stage_stock)
class StageStockAdmin(admin.ModelAdmin):
    list_display = (
        "stage",
        "warehouse",
        "item_name",
        "lot_or_batch_no",
        "balance_units",
        "balance_qty",
        "inward_qty",
        "outward_qty",
        "updated_on",
    )
    list_filter = ("stage", "warehouse")
    search_fields = ("item_name", "lot_or_batch_no")


class VoucherLineInline(admin.TabularInline):
    model = tl_voucher_line
    extra = 0
    fields = ("account_code", "account_name", "party", "debit", "credit", "narration")
    readonly_fields = ("account_code", "account_name", "party", "debit", "credit", "narration")


@admin.register(tl_voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = (
        "voucher_number",
        "voucher_date",
        "voucher_type",
        "stage",
        "party",
        "total_debit",
        "total_credit",
        "is_posted",
        "is_reversed",
    )
    list_filter = ("voucher_type", "stage", "is_posted", "is_reversed", "voucher_date")
    search_fields = ("voucher_number", "reference_no", "narration")
    inlines = [VoucherLineInline]
    date_hierarchy = "voucher_date"
