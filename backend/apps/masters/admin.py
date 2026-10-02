from django.contrib import admin
from apps.masters.models import (
    UnitOfMeasurement, PartyMaster, YarnCountMaster, YarnTypeMaster,
    ColorShadeMaster, YarnMaster, FabricTypeMaster, FabricMaster,
    ProcessMaster, WarehouseMaster, quality_program_table, sub_quality_program_table
)

@admin.register(UnitOfMeasurement)
class UOMAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'symbol', 'company', 'is_active')
    search_fields = ('code', 'name')
    list_filter = ('company', 'is_active')

@admin.register(PartyMaster)
class PartyMasterAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'party_type', 'city', 'phone', 'company', 'is_active')
    search_fields = ('code', 'name', 'gst_number', 'phone')
    list_filter = ('party_type', 'company', 'is_active', 'state')

@admin.register(YarnCountMaster)
class YarnCountAdmin(admin.ModelAdmin):
    list_display = ('count', 'company', 'is_active')
    search_fields = ('count',)
    list_filter = ('company', 'is_active')

@admin.register(YarnTypeMaster)
class YarnTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'company', 'is_active')
    search_fields = ('name', 'code')
    list_filter = ('company', 'is_active')

@admin.register(ColorShadeMaster)
class ColorShadeAdmin(admin.ModelAdmin):
    list_display = ('shade_code', 'color_name', 'hex_code', 'pantone_ref', 'company', 'is_active')
    search_fields = ('shade_code', 'color_name')
    list_filter = ('company', 'is_active')

@admin.register(YarnMaster)
class YarnMasterAdmin(admin.ModelAdmin):
    list_display = ('yarn_code', 'yarn_type', 'yarn_count', 'category', 'color_shade', 'uom', 'company', 'is_active')
    search_fields = ('yarn_code',)
    list_filter = ('category', 'yarn_type', 'yarn_count', 'company', 'is_active')

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

