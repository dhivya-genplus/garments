from rest_framework import serializers
from apps.authentication.models import Company, FinancialYear, User, Role, Privilege
from core.constants import UserRoles, ModulePermissions

class PrivilegeSerializer(serializers.ModelSerializer):
    module_display = serializers.CharField(source='get_module_display', read_only=True)

    class Meta:
        model = Privilege
        fields = [
            'id', 'module', 'module_display', 'can_create', 'can_read',
            'can_update', 'can_delete', 'can_approve', 'can_export'
        ]


class RoleSerializer(serializers.ModelSerializer):
    privileges = PrivilegeSerializer(many=True, read_only=True)
    privileges_input = PrivilegeSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Role
        fields = [
            'id', 'company', 'name', 'code', 'description',
            'is_system_role', 'privileges', 'privileges_input',
            'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'is_system_role', 'created_on', 'updated_on']


class FinancialYearSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    company = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=Company.objects.all())

    class Meta:
        model = FinancialYear
        fields = [
            'id', 'company', 'company_name', 'name', 'code',
            'start_date', 'end_date', 'is_current', 'is_closed',
            'description', 'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'created_on', 'updated_on']
        validators = []  # Uniqueness is enforced cleanly in FinancialYearService


class CompanySerializer(serializers.ModelSerializer):
    users_count = serializers.SerializerMethodField()
    current_financial_year = FinancialYearSerializer(read_only=True)
    financial_years = FinancialYearSerializer(many=True, read_only=True)

    class Meta:
        model = Company
        fields = [
            'id', 'name', 'code', 'legal_name', 'gst_number', 'pan_number',
            'email', 'phone', 'address_line1', 'address_line2', 'city',
            'state', 'pincode', 'is_active', 'subscription_plan',
            'subscription_end_date', 'users_count', 'current_financial_year',
            'financial_years', 'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'created_on', 'updated_on']

    def get_users_count(self, obj):
        return obj.users.filter(is_deleted=False).count()


class UserSerializer(serializers.ModelSerializer):
    company_details = CompanySerializer(source='company', read_only=True)
    custom_role_details = RoleSerializer(source='custom_role', read_only=True)
    active_financial_year_details = FinancialYearSerializer(source='active_financial_year', read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone', 'employee_code', 'department', 'designation',
            'role', 'role_display', 'company', 'company_details',
            'active_financial_year', 'active_financial_year_details',
            'custom_role', 'custom_role_details', 'is_superadmin',
            'is_company_admin', 'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    company = serializers.PrimaryKeyRelatedField(required=False, queryset=Company.objects.all())
    custom_role_id = serializers.IntegerField(required=False, allow_null=True)
    active_financial_year_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'first_name', 'last_name',
            'phone', 'employee_code', 'department', 'designation',
            'role', 'company', 'custom_role_id', 'active_financial_year_id',
            'is_superadmin', 'is_company_admin', 'is_active'
        ]


class UserUpdateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, min_length=6)
    custom_role_id = serializers.IntegerField(required=False, allow_null=True)
    active_financial_year_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = [
            'email', 'username', 'password', 'first_name', 'last_name',
            'phone', 'employee_code', 'department', 'designation',
            'role', 'custom_role_id', 'active_financial_year_id', 'is_active'
        ]


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)


class SwitchFinancialYearSerializer(serializers.Serializer):
    financial_year_id = serializers.IntegerField(required=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=6)
