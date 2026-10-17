from django.contrib import admin
from apps.authentication.models import Company, FinancialYear, User, Role, Privilege, Employee

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

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        'employee_code', 'first_name', 'last_name', 'department',
        'designation', 'phone', 'email', 'status', 'has_login_account', 'company', 'is_active'
    )
    search_fields = ('employee_code', 'first_name', 'last_name', 'email', 'phone', 'department', 'designation')
    list_filter = ('company', 'department', 'status', 'is_active')
    ordering = ['employee_code']

    @admin.display(boolean=True, description="Has User Account")
    def has_login_account(self, obj):
        return hasattr(obj, 'user_account') and obj.user_account is not None


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'username', 'role', 'company', 'employee_code', 'employee', 'is_active')
    search_fields = ('email', 'username', 'employee_code', 'first_name', 'last_name')
    list_filter = ('role', 'is_superadmin', 'is_company_admin', 'is_active', 'company')

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.company and not obj.is_superadmin and not obj.employee:
            emp_code = obj.employee_code or f"EMP-{obj.id:04d}"
            employee, _ = Employee.objects.get_or_create(
                company=obj.company,
                employee_code=emp_code,
                defaults={
                    "first_name": obj.first_name or obj.username,
                    "last_name": obj.last_name or "",
                    "email": obj.email,
                    "phone": obj.phone or "",
                    "department": obj.department or "General",
                    "designation": obj.designation or "Staff",
                    "status": "ACTIVE",
                    "is_active": obj.is_active,
                    "created_by": request.user,
                }
            )
            obj.employee = employee
            obj.employee_code = employee.employee_code
            obj.save(update_fields=['employee', 'employee_code'])


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'company', 'is_system_role')
    search_fields = ('name', 'code')
    list_filter = ('is_system_role', 'company')
    inlines = [PrivilegeInline]
