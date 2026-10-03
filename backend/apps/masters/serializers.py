from rest_framework import serializers
from apps.masters.models import (
    UnitOfMeasurement, PartyMaster, YarnCountMaster, YarnTypeMaster,
    ColorShadeMaster, YarnMaster, FabricTypeMaster, FabricMaster,
    ProcessMaster, WarehouseMaster, quality_program_table, sub_quality_program_table
)

class UOMSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitOfMeasurement
        fields = ['id', 'company', 'code', 'name', 'symbol', 'is_active', 'created_on', 'updated_on']
        read_only_fields = ['id', 'company', 'created_on', 'updated_on']


class PartyMasterSerializer(serializers.ModelSerializer):
    party_type_display = serializers.CharField(source='get_party_type_display', read_only=True)

    class Meta:
        model = PartyMaster
        fields = [
            'id', 'company', 'party_type', 'party_type_display', 'code', 'name',
            'contact_person', 'phone', 'email', 'gst_number', 'pan_number',
            'address_line1', 'address_line2', 'city', 'state', 'pincode',
            'credit_days', 'credit_limit', 'opening_balance', 'is_active',
            'created_on', 'updated_on'
        ]
        read_only_fields = ['id', 'company', 'created_on', 'updated_on']


class YarnCountSerializer(serializers.ModelSerializer):
    class Meta:
        model = YarnCountMaster
        fields = ['id', 'company', 'count', 'description', 'is_active', 'created_on', 'updated_on']
        read_only_fields = ['id', 'company', 'created_on', 'updated_on']


class YarnTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = YarnTypeMaster
        fields = ['id', 'company', 'name', 'code', 'description', 'is_active', 'created_on', 'updated_on']
        read_only_fields = ['id', 'company', 'created_on', 'updated_on']


class ColorShadeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColorShadeMaster
        fields = ['id', 'company', 'shade_code', 'color_name', 'hex_code', 'pantone_ref', 'description', 'is_active', 'created_on', 'updated_on']
        read_only_fields = ['id', 'company', 'created_on', 'updated_on']


class YarnMasterSerializer(serializers.ModelSerializer):
    yarn_type_name = serializers.CharField(source='yarn_type.name', read_only=True)
    yarn_count_name = serializers.CharField(source='yarn_count.count', read_only=True)
    color_shade_name = serializers.CharField(source='color_shade.color_name', read_only=True, default=None)
    uom_code = serializers.CharField(source='uom.code', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = YarnMaster
        fields = [
            'id', 'company', 'yarn_code', 'yarn_type', 'yarn_type_name',
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
            sub_quality_program_table.objects.bulk_create(size_objs)
        return instance


