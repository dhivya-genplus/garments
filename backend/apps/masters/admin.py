from django.contrib import admin
from apps.masters.models import (
    UnitOfMeasurement, PartyMaster, YarnCountMaster,
    ColorShadeMaster, YarnMaster, FabricTypeMaster, FabricMaster,
    ProcessMaster, WarehouseMaster, quality_program_table, sub_quality_program_table,
    TaxMaster, PartyRole, PartyContact, PartyAddress, PartyBankDetail,
    PartyCapability, PartyDocument
)

@admin.register(UnitOfMeasurement)
class UOMAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'company', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('company', 'is_active')


class PartyRoleInline(admin.TabularInline):
    model = PartyRole
    extra = 0
    fields = ('role', 'is_primary')


class PartyContactInline(admin.TabularInline):
    model = PartyContact
    extra = 0
    fields = ('contact_person', 'designation', 'mobile', 'email', 'is_primary', 'is_active')


class PartyAddressInline(admin.StackedInline):
    model = PartyAddress
    extra = 0
    fields = (
        ('address_type', 'is_default', 'is_active'),
        ('address_line1', 'address_line2'),
        ('city', 'district', 'state', 'pincode', 'gst_state_code')
    )


class PartyBankDetailInline(admin.TabularInline):
    model = PartyBankDetail
    extra = 0
    fields = ('bank_name', 'branch_name', 'account_holder_name', 'account_number', 'ifsc_code', 'preferred_payment_mode', 'is_default', 'is_active')


class PartyCapabilityInline(admin.StackedInline):
    model = PartyCapability
    extra = 0
    filter_horizontal = ('processes_performed', 'yarn_counts_handled', 'fabric_types_handled')
    fields = (
        ('processes_performed', 'yarn_counts_handled', 'fabric_types_handled'),
        ('machine_types', 'production_capacity', 'capacity_uom'),
        ('min_job_work_qty', 'max_job_work_qty', 'standard_processing_days', 'procurement_lead_time_days'),
        ('default_uom', 'quality_certifications', 'sample_approval_required')
    )


class PartyDocumentInline(admin.TabularInline):
    model = PartyDocument
    extra = 0
    fields = ('document_type', 'document_number', 'file_attachment', 'verification_status', 'issue_date', 'expiry_date')


@admin.register(PartyMaster)
class PartyMasterAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'party_type', 'city', 'phone', 'gst_number', 'company', 'is_active')
    search_fields = ('code', 'name', 'display_name', 'gst_number', 'pan_number', 'phone', 'city')
    list_filter = ('party_type', 'party_category', 'company', 'is_active', 'state')
    readonly_fields = ('created_on', 'updated_on', 'created_by', 'updated_by')
    inlines = [
        PartyRoleInline, PartyContactInline, PartyAddressInline,
        PartyBankDetailInline, PartyCapabilityInline, PartyDocumentInline
    ]
    fieldsets = (
        ('Basic Details', {
            'fields': (
                ('code', 'name', 'display_name'),
                ('party_type', 'party_category', 'company'),
                ('parent_party', 'is_active'),
                'remarks'
            )
        }),
        ('Primary Contact', {
            'fields': (
                ('contact_person', 'phone', 'email'),
                ('whatsapp_number', 'website')
            )
        }),
        ('Statutory & GST Information', {
            'fields': (
                ('gst_registration_type', 'gst_number', 'pan_number'),
                ('cin_number', 'msme_number', 'tax_applicable'),
                ('default_gst_treatment', 'tds_applicable', 'tds_section'),
                ('export_import_classification', 'country_of_tax_registration', 'tax_verification_status')
            )
        }),
        ('Registered Address', {
            'fields': (
                ('address_line1', 'address_line2'),
                ('city', 'state', 'pincode')
            )
        }),
        ('Commercial & Pricing Terms', {
            'fields': (
                ('default_purchase_price_list', 'default_sales_price_list', 'default_job_work_price_list'),
                ('currency', 'payment_terms', 'credit_days', 'credit_limit'),
                ('rebate_tier', 'default_discount_percent', 'freight_terms'),
                ('rate_contract_number', 'contract_start_date', 'contract_end_date', 'price_approval_required')
            )
        }),
        ('Accounting & Ledger', {
            'fields': (
                ('ledger_account_code', 'default_purchase_account'),
                ('default_sales_account', 'default_job_work_expense_account'),
                ('opening_balance', 'opening_balance_type', 'opening_balance_date')
            )
        }),
        ('Audit Information', {
            'classes': ('collapse',),
            'fields': (
                ('created_by', 'created_on'),
                ('updated_by', 'updated_on')
            )
        }),
    )

@admin.register(YarnCountMaster)
class YarnCountAdmin(admin.ModelAdmin):
    list_display = ('count', 'company', 'is_active')
    search_fields = ('count',)
    list_filter = ('company', 'is_active')

@admin.register(ColorShadeMaster)
class ColorShadeAdmin(admin.ModelAdmin):
    list_display = ('shade_code', 'color_name', 'hex_code', 'pantone_ref', 'company', 'is_active')
    search_fields = ('shade_code', 'color_name')
    list_filter = ('company', 'is_active')

@admin.register(YarnMaster)
class YarnMasterAdmin(admin.ModelAdmin):
    list_display = ('yarn_code', 'yarn_count', 'category', 'color_shade', 'uom', 'company', 'is_active')
    search_fields = ('yarn_code',)
    list_filter = ('category', 'yarn_count', 'company', 'is_active')

@admin.register(FabricTypeMaster)
class FabricTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'company', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('company', 'is_active')

@admin.register(FabricMaster)
class FabricMasterAdmin(admin.ModelAdmin):
    list_display = ('fabric_code', 'fabric_name', 'fabric_type', 'category', 'gsm', 'dia', 'gauge', 'company', 'is_active')
    search_fields = ('fabric_code', 'fabric_name')
    list_filter = ('category', 'fabric_type', 'company', 'is_active')

@admin.register(ProcessMaster)
class ProcessMasterAdmin(admin.ModelAdmin):
    list_display = ('process_code', 'process_name', 'process_type', 'default_loss_percentage', 'standard_rate_per_kg', 'company', 'is_active')
    search_fields = ('process_code', 'process_name')
    list_filter = ('process_type', 'company', 'is_active')

@admin.register(WarehouseMaster)
class WarehouseMasterAdmin(admin.ModelAdmin):
    list_display = ('warehouse_code', 'name', 'warehouse_type', 'contact_person', 'company', 'is_active')
    search_fields = ('warehouse_code', 'name')
    list_filter = ('warehouse_type', 'company', 'is_active')


class SubQualityProgramInline(admin.TabularInline):
    model = sub_quality_program_table
    extra = 1
    fields = ('size_id', 'position', 'per_box', 'is_active', 'status')


@admin.register(quality_program_table)
class QualityProgramAdmin(admin.ModelAdmin):
    list_display = ('id', 'quality', 'style', 'fabric_id', 'is_active', 'status', 'created_on')
    search_fields = ('quality', 'style', 'fabric_id')
    list_filter = ('is_active', 'status', 'created_on')
    inlines = [SubQualityProgramInline]


@admin.register(sub_quality_program_table)
class SubQualityProgramAdmin(admin.ModelAdmin):
    list_display = ('id', 'tm', 'size_id', 'position', 'per_box', 'is_active', 'status')
    search_fields = ('size_id',)
    list_filter = ('is_active', 'status')


@admin.register(TaxMaster)
class TaxMasterAdmin(admin.ModelAdmin):
    list_display = ('tax_code', 'tax_name', 'tax_percent', 'cgst_percent', 'sgst_percent', 'igst_percent', 'company', 'is_default', 'is_active')
    search_fields = ('tax_code', 'tax_name', 'hsn_sac_code')
    list_filter = ('company', 'is_active', 'is_default')


