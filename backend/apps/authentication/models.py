from django.db import models
from django.contrib.auth.models import AbstractUser
from core.base_models import SoftDeleteModel, TimeStampedModel
from core.constants import UserRoles, ModulePermissions

class Company(SoftDeleteModel):
    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=50, unique=True, db_index=True)
    legal_name = models.CharField(max_length=255, blank=True)
    gst_number = models.CharField(max_length=20, blank=True, db_index=True)
    pan_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    pincode = models.CharField(max_length=20, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    subscription_plan = models.CharField(max_length=50, default="ENTERPRISE")
    subscription_end_date = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "sys_company"
        verbose_name_plural = "Companies"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["code", "is_active", "is_deleted"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.code})"

    @property
    def current_financial_year(self):
        return self.financial_years.filter(is_current=True, is_deleted=False).first()


class FinancialYear(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="financial_years")
    name = models.CharField(max_length=100)                      # e.g., "FY 2025-2026"
    code = models.CharField(max_length=50, db_index=True)        # e.g., "2025-2026"
    start_date = models.DateField()                              # 2025-04-01
    end_date = models.DateField()                                # 2026-03-31
    is_current = models.BooleanField(default=False, db_index=True)
    is_closed = models.BooleanField(default=False)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "sys_financial_year"
        verbose_name = "Financial Year"
        verbose_name_plural = "Financial Years"
        unique_together = ("company", "code")
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=["company", "is_current", "is_deleted"]),
        ]

    def __str__(self):
        return f"{self.name} [{self.company.code}]"


class Role(SoftDeleteModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name="roles")
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    is_system_role = models.BooleanField(default=False)

    class Meta:
        db_table = "sys_role"
        ordering = ["name"]
        unique_together = ("company", "code")

    def __str__(self):
        comp = self.company.code if self.company else "GLOBAL"
        return f"{self.name} [{comp}]"


class Privilege(SoftDeleteModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name="privileges")
    module = models.CharField(max_length=100, choices=ModulePermissions.ALL_MODULES)
    can_create = models.BooleanField(default=False)
    can_read = models.BooleanField(default=True)
    can_update = models.BooleanField(default=False)
    can_delete = models.BooleanField(default=False)
    can_approve = models.BooleanField(default=False)
    can_export = models.BooleanField(default=False)

    class Meta:
        db_table = "sys_privilege"
        unique_together = ("role", "module")
        indexes = [
            models.Index(fields=["role", "module"]),
        ]

    def __str__(self):
        return f"{self.role.name} - {self.module}"


class User(AbstractUser):
    """
    Unified User model partitioned cleanly by user_type:
    - SUPER_ADMIN: Global system master
    - ADMIN_USER: Company Administrator
    - COMPANY_USER: Company Employee / Staff / Operator
    """
    email = models.EmailField(unique=True, db_index=True)
    phone = models.CharField(max_length=20, blank=True)
    employee_code = models.CharField(max_length=50, blank=True, db_index=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    
    role = models.CharField(max_length=30, choices=UserRoles.CHOICES, default=UserRoles.COMPANY_USER, db_index=True)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, null=True, blank=True, related_name="users")
    active_financial_year = models.ForeignKey(FinancialYear, on_delete=models.SET_NULL, null=True, blank=True, related_name="active_users")
    custom_role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_users")
    
    is_superadmin = models.BooleanField(default=False, db_index=True)
    is_company_admin = models.BooleanField(default=False, db_index=True)

    # Soft delete support
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_on = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name="deleted_users")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = "sys_user"
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email", "role", "is_deleted"]),
            models.Index(fields=["company", "role", "is_deleted"]),
        ]

    def __str__(self):
        return f"{self.email} ({self.get_full_name() or self.username}) - {self.get_role_display()}"

    @property
    def is_super_admin(self):
        return self.role == UserRoles.SUPER_ADMIN or self.is_superadmin or self.is_superuser

    @property
    def is_admin_user(self):
        return self.role == UserRoles.ADMIN_USER or self.is_company_admin

    @property
    def is_company_user(self):
        return self.role == UserRoles.COMPANY_USER

    def soft_delete(self, user=None):
        from django.utils import timezone
        self.is_deleted = True
        self.is_active = False
        self.deleted_on = timezone.now()
        self.deleted_by = user
        self.save(update_fields=["is_deleted", "is_active", "deleted_on", "deleted_by"])
