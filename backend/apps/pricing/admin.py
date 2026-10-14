from django.contrib import admin
from apps.pricing.models import PriceList, PriceListItem, PriceListJobRule, PricingAudit


@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ("id", "company_id", "price_list_code", "price_list_name", "list_type", "scope", "party_id", "valid_from", "valid_to", "is_default", "record_status")
    list_filter = ("list_type", "scope", "record_status", "is_default", "company_id")
    search_fields = ("price_list_code", "price_list_name")


@admin.register(PriceListItem)
class PriceListItemAdmin(admin.ModelAdmin):
    list_display = ("id", "company_id", "price_list_id", "item_type", "yarn_count_id", "min_quantity", "max_quantity", "base_rate", "discount_percent", "net_rate", "record_status")
    list_filter = ("item_type", "record_status", "company_id")
    search_fields = ("price_list_id",)


@admin.register(PriceListJobRule)
class PriceListJobRuleAdmin(admin.ModelAdmin):
    list_display = ("id", "company_id", "price_list_id", "process_stage_id", "fabric_type_id", "yarn_count_id", "machine_gauge", "is_lycra_plated", "shade_category", "job_rate", "allowed_loss_percent", "record_status")
    list_filter = ("process_stage_id", "is_lycra_plated", "shade_category", "record_status", "company_id")
    search_fields = ("price_list_id", "machine_gauge", "shade_category", "garment_style_category")


@admin.register(PricingAudit)
class PricingAuditAdmin(admin.ModelAdmin):
    list_display = ("id", "company_id", "document_type", "document_id", "system_rate", "actual_rate", "is_override", "approved_by", "created_at")
    list_filter = ("document_type", "is_override", "company_id")
    search_fields = ("document_type", "document_id", "override_reason")
