from rest_framework import serializers
from apps.masters.models import (
    UnitOfMeasurement, PartyMaster, YarnCountMaster,
    ColorShadeMaster, YarnMaster, FabricTypeMaster, FabricMaster,
    ProcessMaster, WarehouseMaster, quality_program_table, sub_quality_program_table,
    TaxMaster, PartyRole, PartyContact, PartyAddress, PartyBankDetail,
    PartyCapability, PartyDocument
)

class UOMSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasurement
        fields = ['id', 'company', 'code', 'name', 'symbol', 'is_active', 'created_on', 'updated_on']
        read_only_fields = ['id', 'company', 'created_on', 'updated_on']


class PartyRoleSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = PartyRole
        fields = ['id', 'role', 'role_display', 'is_primary']


class PartyContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartyContact
        fields = [
            'id', 'contact_person', 'designation', 'mobile', 'alternate_mobile',
            'email', 'alternate_email', 'whatsapp_number', 'website', 'is_primary', 'is_active'
        ]


class PartyAddressSerializer(serializers.ModelSerializer):
    address_type_display = serializers.CharField(source='get_address_type_display', read_only=True)

    class Meta:
        model = PartyAddress
        fields = [
            'id', 'address_type', 'address_type_display', 'address_line1', 'address_line2',
            'country', 'state', 'district', 'city', 'area_locality', 'pincode',
            'gst_state_code', 'is_default', 'is_active'
        ]


class PartyBankDetailSerializer(serializers.ModelSerializer):
    masked_account_number = serializers.SerializerMethodField()

    class Meta:
        model = PartyBankDetail
        fields = [
            'id', 'bank_name', 'branch_name', 'account_holder_name', 'account_number',
            'masked_account_number', 'ifsc_code', 'upi_id', 'preferred_payment_mode',
            'beneficiary_verification_status', 'is_default', 'is_active'
        ]
        extra_kwargs = {
            'account_number': {'write_only': False}
        }

    def get_masked_account_number(self, obj):
        acc = str(obj.account_number or "")
        if len(acc) > 4:
            return "X" * (len(acc) - 4) + acc[-4:]
        return "XXXX" if acc else ""

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        # If user is not superadmin or company admin, mask raw account number
        if user and not (user.is_superuser or getattr(user, 'is_superadmin', False) or getattr(user, 'is_company_admin', False)):
            ret['account_number'] = ret['masked_account_number']
        return ret


class PartyCapabilitySerializer(serializers.ModelSerializer):
    capacity_uom_name = serializers.CharField(source='capacity_uom.code', read_only=True)
    default_uom_name = serializers.CharField(source='default_uom.code', read_only=True)
    processes_performed_names = serializers.SerializerMethodField()

    class Meta:
        model = PartyCapability
        fields = [
            'id', 'machine_types', 'production_capacity', 'capacity_uom', 'capacity_uom_name',
            'min_job_work_qty', 'max_job_work_qty', 'standard_processing_days',
            'procurement_lead_time_days', 'default_uom', 'default_uom_name',
            'quality_certifications', 'sample_approval_required',
            'processes_performed', 'processes_performed_names',
            'yarn_counts_handled', 'fabric_types_handled'
        ]

    def get_processes_performed_names(self, obj):
        return [p.process_name for p in obj.processes_performed.all()]


class PartyDocumentSerializer(serializers.ModelSerializer):
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.username', read_only=True)

    class Meta:
        model = PartyDocument
        fields = [
            'id', 'document_type', 'document_type_display', 'document_number',
            'file_attachment', 'issue_date', 'expiry_date', 'verification_status',
            'verified_by', 'verified_by_name', 'verified_at', 'remarks', 'created_on'
        ]
        read_only_fields = ['id', 'created_on', 'verified_at']


class PartyMasterSerializer(serializers.ModelSerializer):
    party_type_display = serializers.CharField(source='get_party_type_display', read_only=True)
    party_category_display = serializers.CharField(source='get_party_category_display', read_only=True)
    parent_party_name = serializers.CharField(source='parent_party.name', read_only=True)

    default_purchase_price_list_name = serializers.CharField(source='default_purchase_price_list.price_list_name', read_only=True)
    default_sales_price_list_name = serializers.CharField(source='default_sales_price_list.price_list_name', read_only=True)
    default_job_work_price_list_name = serializers.CharField(source='default_job_work_price_list.price_list_name', read_only=True)

    roles = PartyRoleSerializer(many=True, required=False)
    contacts = PartyContactSerializer(many=True, required=False)
    addresses = PartyAddressSerializer(many=True, required=False)
    bank_details = PartyBankDetailSerializer(many=True, required=False)
    capability = PartyCapabilitySerializer(required=False)
    documents = PartyDocumentSerializer(many=True, required=False)

    outstanding_amount = serializers.SerializerMethodField()
    last_transaction_date = serializers.SerializerMethodField()

    class Meta:
        model = PartyMaster
        fields = [
            'id', 'company', 'party_type', 'party_type_display', 'code', 'name', 'display_name',
            'party_category', 'party_category_display', 'parent_party', 'parent_party_name', 'remarks',

            # Primary Contact (legacy & flat display)
            'contact_person', 'phone', 'email', 'whatsapp_number', 'website',

            # Statutory & GST
            'gst_registration_type', 'gst_number', 'pan_number', 'cin_number', 'msme_number',
            'tax_applicable', 'default_gst_treatment', 'tds_applicable', 'tds_section',
            'export_import_classification', 'country_of_tax_registration', 'tax_verification_status',

            # Addresses (legacy & flat display)
            'address_line1', 'address_line2', 'city', 'state', 'pincode',

            # Commercial & Price Lists
            'default_purchase_price_list', 'default_purchase_price_list_name',
            'default_sales_price_list', 'default_sales_price_list_name',
            'default_job_work_price_list', 'default_job_work_price_list_name',
            'currency', 'payment_terms', 'credit_days', 'credit_limit', 'rebate_tier',
            'default_discount_percent', 'freight_terms', 'rate_contract_number',
            'contract_start_date', 'contract_end_date', 'price_approval_required',

            # Accounting & Opening Balance
            'ledger_account_code', 'default_purchase_account', 'default_sales_account',
            'default_job_work_expense_account', 'opening_balance', 'opening_balance_type',
            'opening_balance_date', 'outstanding_amount', 'last_transaction_date',

            # Related child collections
            'roles', 'contacts', 'addresses', 'bank_details', 'capability', 'documents',

            'is_active', 'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'company', 'created_on', 'updated_on', 'outstanding_amount', 'last_transaction_date']

    def get_outstanding_amount(self, obj):
        try:
            from apps.masters.services import PartyService
            summary = PartyService.get_party_financial_summary(obj.id, obj.company_id)
            return summary.get('net_outstanding_balance', obj.opening_balance)
        except Exception:
            return obj.opening_balance

    def get_last_transaction_date(self, obj):
        try:
            from apps.masters.services import PartyService
            summary = PartyService.get_party_financial_summary(obj.id, obj.company_id)
            return summary.get('last_transaction_date')
        except Exception:
            return None


class YarnCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = YarnCountMaster
        fields = ['id', 'company', 'count', 'description', 'is_active', 'created_on', 'updated_on']
        read_only_fields = ['id', 'company', 'created_on', 'updated_on']


class ColorShadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColorShadeMaster
        fields = ['id', 'company', 'shade_code', 'color_name', 'hex_code', 'pantone_ref', 'description', 'is_active', 'created_on', 'updated_on']
        read_only_fields = ['id', 'company', 'created_on', 'updated_on']


class YarnMasterSerializer(serializers.ModelSerializer):
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)
    uom_code = serializers.CharField(source='uom.code', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = YarnMaster
        fields = [
            'id', 'company', 'yarn_code',
            'yarn_count', 'yarn_count_name', 'category', 'category_display',
            'color_shade', 'color_shade_name', 'uom', 'uom_code',
            'hsn_code', 'reorder_level', 'description', 'is_active',
            'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'company', 'created_on', 'updated_on']


class FabricTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = FabricTypeMaster
        fields = ['id', 'company', 'name', 'code', 'description', 'is_active', 'created_on', 'updated_on']
        read_only_fields = ['id', 'company', 'created_on', 'updated_on']


class FabricMasterSerializer(serializers.ModelSerializer):
    fabric_type_name = serializers.CharField(source='fabric_type.name', read_only=True)
    yarn_code_name = serializers.CharField(source='yarn.yarn_code', read_only=True, default=None)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)
    uom_code = serializers.CharField(source='uom.code', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = FabricMaster
        fields = [
            'id', 'company', 'fabric_code', 'fabric_name', 'fabric_type',
            'fabric_type_name', 'category', 'category_display', 'yarn',
            'yarn_code_name', 'color_shade', 'color_shade_name', 'gsm',
            'dia', 'gauge', 'uom', 'uom_code', 'hsn_code', 'min_stock_alert',
            'description', 'is_active', 'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'company', 'created_on', 'updated_on']


class ProcessMasterSerializer(serializers.ModelSerializer):
    process_type_display = serializers.CharField(source='get_process_type_display', read_only=True)

    class Meta:
        model = ProcessMaster
        fields = [
            'id', 'company', 'process_code', 'process_name', 'process_type',
            'process_type_display', 'default_loss_percentage',
            'standard_rate_per_kg', 'description', 'is_active',
            'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'company', 'created_on', 'updated_on']


class WarehouseMasterSerializer(serializers.ModelSerializer):
    warehouse_type_display = serializers.CharField(source='get_warehouse_type_display', read_only=True)

    class Meta:
        model = WarehouseMaster
        fields = [
            'id', 'company', 'warehouse_code', 'name', 'warehouse_type',
            'warehouse_type_display', 'address', 'contact_person', 'phone',
            'is_active', 'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'company', 'created_on', 'updated_on']


class SubQualityProgramSerializer(serializers.ModelSerializer):
    class Meta:
        model = sub_quality_program_table
        fields = [
            'id', 'tm', 'size_id', 'position', 'per_box',
            'is_active', 'status', 'created_on', 'updated_on',
            'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_on', 'updated_on']
        extra_kwargs = {
            'tm': {'required': False}
        }


class QualityProgramSerializer(serializers.ModelSerializer):
    sizes = SubQualityProgramSerializer(many=True, required=False)

    class Meta:
        model = quality_program_table
        fields = [
            'id', 'quality', 'style', 'fabric_id', 'is_active',
            'status', 'sizes', 'created_on', 'updated_on',
            'created_by', 'updated_by'
        ]
        read_only_fields = ['id', 'created_on', 'updated_on']

    def create(self, validated_data):
        sizes_data = validated_data.pop('sizes', [])
        qp = quality_program_table.objects.create(**validated_data)
        if sizes_data:
            size_objs = [
                sub_quality_program_table(
                    tm=qp,
                    size_id=s.get('size_id'),
                    position=s.get('position', idx + 1),
                    per_box=s.get('per_box', 0),
                    is_active=s.get('is_active', 1),
                    status=s.get('status', 1),
                    created_by=validated_data.get('created_by', 1),
                    updated_by=validated_data.get('updated_by', 1),
                )
                for idx, s in enumerate(sizes_data)
            ]
            sub_quality_program_table.objects.bulk_create(size_objs)
        return qp

    def update(self, instance, validated_data):
        sizes_data = validated_data.pop('sizes', None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if sizes_data is not None:
            sub_quality_program_table.objects.filter(tm=instance).delete()
            size_objs = [
                sub_quality_program_table(
                    tm=instance,
                    size_id=s.get('size_id'),
                    position=s.get('position', idx + 1),
                    per_box=s.get('per_box', 0),
                    is_active=s.get('is_active', 1),
                    status=s.get('status', 1),
                    created_by=instance.created_by,
                    updated_by=instance.updated_by,
                )
                for idx, s in enumerate(sizes_data)
            ]
        return instance


class TaxMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxMaster
        fields = [
            'id', 'company', 'tax_name', 'tax_code', 'tax_percent',
            'cgst_percent', 'sgst_percent', 'igst_percent', 'hsn_sac_code',
            'is_default', 'is_active', 'description', 'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'company', 'created_on', 'updated_on']



