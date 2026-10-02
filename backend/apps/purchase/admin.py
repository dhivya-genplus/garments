from django.contrib import admin
from apps.purchase.models import parent_po_table, child_po_table, yarn_po_delivery_table


class ChildPOInline(admin.TabularInline):
    model = child_po_table
    extra = 1
    fields = (
        'yarn_type', 'yarn_count', 'color_shade', 'bag', 'per_bag',
        'quantity', 'actual_rate', 'discount', 'rate', 'amount',
        'remaining_bag', 'remaining_quantity'
    )
    readonly_fields = ('quantity', 'rate', 'amount', 'remaining_bag', 'remaining_quantity')


class YarnPODeliveryInline(admin.TabularInline):
    model = yarn_po_delivery_table
    extra = 1
    fields = ('yarn_count', 'party', 'delivery_date', 'bag', 'bag_wt', 'quantity')
    readonly_fields = ('quantity',)


@admin.register(parent_po_table)
class ParentPOAdmin(admin.ModelAdmin):
    list_display = (
        'po_number', 'po_date', 'yarn_type', 'party', 'mill',
        'bag', 'quantity', 'rate', 'amount', 'is_authorized', 'is_complete'
    )
    list_filter = ('yarn_type', 'is_authorized', 'is_complete', 'company', 'po_date')
    search_fields = ('po_number', 'party__name', 'mill__name', 'name')
    readonly_fields = (
        'quantity', 'net_rate', 'amount', 'authorized_by',
        'authorized_on', 'created_on', 'updated_on'
    )
    inlines = [ChildPOInline, YarnPODeliveryInline]
    actions = ['authorize_pos', 'unauthorize_pos']

    fieldsets = (
        ("Order Details", {
            "fields": (
                "po_number", "po_date", "yarn_type", "color_shade", "name",
                "company", "cfyear", "party", "mill", "yarn_count"
            )
        }),
        ("Quantities & Commercials", {
            "fields": (
                ("bag", "per_bag", "quantity"),
                ("rate", "discount", "net_rate", "amount"),
                "gross_quantity", "remarks"
            )
        }),
        ("Status & Workflow", {
            "fields": (
                ("is_delivery", "is_complete", "is_authorized"),
                ("authorized_by", "authorized_on"),
                ("is_active", "status"),
                ("created_on", "updated_on")
            )
        }),
    )

    @admin.action(description="Authorize selected Yarn Purchase Orders")
    def authorize_pos(self, request, queryset):
        queryset.update(is_authorized=1, authorized_by=request.user)
        self.message_user(request, "Selected purchase orders authorized successfully.")

    @admin.action(description="Un-authorize / Re-open selected Purchase Orders")
    def unauthorize_pos(self, request, queryset):
        queryset.filter(is_complete=0).update(is_authorized=0, authorized_by=None)
        self.message_user(request, "Selected un-fulfilled purchase orders re-opened.")


@admin.register(child_po_table)
class ChildPOAdmin(admin.ModelAdmin):
    list_display = ('id', 'tm_po', 'yarn_type', 'yarn_count', 'bag', 'quantity', 'rate', 'amount')
    list_filter = ('yarn_type', 'yarn_count')
    search_fields = ('tm_po__po_number',)


@admin.register(yarn_po_delivery_table)
class YarnPODeliveryAdmin(admin.ModelAdmin):
    list_display = ('id', 'tm_po', 'party', 'delivery_date', 'bag', 'quantity')
    list_filter = ('delivery_date', 'party')
    search_fields = ('tm_po__po_number', 'party__name')
