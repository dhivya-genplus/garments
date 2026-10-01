from django.contrib import admin
from apps.authentication.models import Company, FinancialYear, User, Role, Privilege

class PrivilegeInline(admin.TabularInline):
    model = Privilege
    extra = 0

@admin.register(FinancialYear)
class FinancialYearAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'company', 'start_date', 'end_date', 'is_current', 'is_closed')
    search_fields = ('name', 'code', 'company__name')
    list_filter = ('is_current', 'is_closed', 'company')

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'gst_number', 'is_active', 'subscription_plan', 'created_on')
    search_fields = ('name', 'code', 'gst_number')
    list_filter = ('is_active', 'subscription_plan')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'role', 'company', 'employee_code', 'active_financial_year', 'is_superadmin', 'is_company_admin', 'is_active')
    search_fields = ('email', 'username', 'employee_code', 'first_name', 'last_name')
    list_filter = ('role', 'is_superadmin', 'is_company_admin', 'is_active', 'company')

@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'company', 'is_system_role')
    search_fields = ('name', 'code')
    list_filter = ('is_system_role', 'company')
    inlines = [PrivilegeInline]
