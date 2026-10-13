from django.contrib import admin
from apps.process.models import (
    parent_process_stage_table,
    parent_process_program_table,
    child_process_program_input_table,
    child_process_program_recipe_table,
)


@admin.register(parent_process_stage_table)
class ParentProcessStageAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "sequence_order", "input_from_stage", "output_to_stage", "standard_loss_percent", "is_active"]
    list_filter = ["is_active", "input_from_stage", "output_to_stage"]
    search_fields = ["name", "code"]


class ChildProcessProgramInputInline(admin.TabularInline):
    model = child_process_program_input_table
    extra = 0


class ChildProcessProgramRecipeInline(admin.TabularInline):
    model = child_process_program_recipe_table
    extra = 0


@admin.register(parent_process_program_table)
class ParentProcessProgramAdmin(admin.ModelAdmin):
    list_display = ["program_number", "program_date", "process_stage", "job_worker", "input_item", "input_quantity", "expected_output_qty", "grand_total", "status"]
    list_filter = ["process_stage", "status", "program_date"]
    search_fields = ["program_number", "input_item", "output_item"]
    inlines = [ChildProcessProgramInputInline, ChildProcessProgramRecipeInline]
