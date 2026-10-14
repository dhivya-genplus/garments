from decimal import Decimal
from django.utils import timezone
from rest_framework import serializers
from apps.pricing.models import PriceList, PriceListItem, PriceListJobRule, PricingAudit
from core.constants import PriceListType, PriceListScope, PriceListItemType, YarnCategory


class PriceListItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceListItem
        fields = [
            "id",
            "company_id",
            "price_list_id",
            "item_type",
            "item_id",
            "yarn_count_id",
            "yarn_type",
            "color_shade_id",
            "uom_id",
            "min_quantity",
            "max_quantity",
            "base_rate",
            "discount_percent",
            "net_rate",
            "lead_time_days",
            "remarks",
            "record_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "company_id", "price_list_id", "net_rate", "record_status", "created_at", "updated_at"]


class PriceListItemCreateSerializer(serializers.Serializer):
    item_type = serializers.ChoiceField(choices=PriceListItemType.CHOICES, default=PriceListItemType.YARN)
    item_id = serializers.IntegerField(required=False, allow_null=True)
    yarn_count_id = serializers.IntegerField(required=False, allow_null=True)
    yarn_type = serializers.ChoiceField(choices=YarnCategory.CHOICES, required=False, allow_null=True, allow_blank=True)
    color_shade_id = serializers.IntegerField(required=False, allow_null=True)
    uom_id = serializers.IntegerField(required=False, allow_null=True)
    min_quantity = serializers.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"))
    max_quantity = serializers.DecimalField(max_digits=18, decimal_places=3, required=False, allow_null=True)
    base_rate = serializers.DecimalField(max_digits=18, decimal_places=4)
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    lead_time_days = serializers.IntegerField(default=0)
    remarks = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        base_rate = attrs.get("base_rate")
        if base_rate is not None and base_rate < Decimal("0.00"):
            raise serializers.ValidationError({"base_rate": "Base rate cannot be negative."})

        min_qty = attrs.get("min_quantity", Decimal("0.000"))
        max_qty = attrs.get("max_quantity")
        if max_qty is not None and max_qty < min_qty:
            raise serializers.ValidationError({"max_quantity": "max_quantity cannot be less than min_quantity."})

        return attrs


class PriceListJobRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceListJobRule
        fields = [
            "id",
            "company_id",
            "price_list_id",
            "process_stage_id",
            "uom_id",
            "fabric_type_id",
            "yarn_count_id",
            "machine_gauge",
            "dia_range",
            "is_lycra_plated",
            "shade_category",
            "dye_class",
            "garment_style_category",
            "print_color_count",
            "job_rate",
            "allowed_loss_percent",
            "lycra_surcharge",
            "special_finish_surcharge",
            "min_quantity",
            "max_quantity",
            "record_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "company_id", "price_list_id", "record_status", "created_at", "updated_at"]


class PriceListJobRuleCreateSerializer(serializers.Serializer):
    process_stage_id = serializers.IntegerField()
    uom_id = serializers.IntegerField(required=False, allow_null=True)
    fabric_type_id = serializers.IntegerField(required=False, allow_null=True)
    yarn_count_id = serializers.IntegerField(required=False, allow_null=True)
    machine_gauge = serializers.CharField(max_length=30, required=False, allow_blank=True, allow_null=True)
    dia_range = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    is_lycra_plated = serializers.BooleanField(required=False, allow_null=True)
    shade_category = serializers.CharField(max_length=30, required=False, allow_blank=True, allow_null=True)
    dye_class = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    garment_style_category = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    print_color_count = serializers.IntegerField(required=False, allow_null=True)
    job_rate = serializers.DecimalField(max_digits=18, decimal_places=4)
    allowed_loss_percent = serializers.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    lycra_surcharge = serializers.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"))
    special_finish_surcharge = serializers.DecimalField(max_digits=18, decimal_places=4, default=Decimal("0.0000"))
    min_quantity = serializers.DecimalField(max_digits=18, decimal_places=3, default=Decimal("0.000"))
    max_quantity = serializers.DecimalField(max_digits=18, decimal_places=3, required=False, allow_null=True)

    def validate(self, attrs):
        job_rate = attrs.get("job_rate")
        if job_rate is not None and job_rate < Decimal("0.00"):
            raise serializers.ValidationError({"job_rate": "Job rate cannot be negative."})

        min_qty = attrs.get("min_quantity", Decimal("0.000"))
        max_qty = attrs.get("max_quantity")
        if max_qty is not None and max_qty < min_qty:
            raise serializers.ValidationError({"max_quantity": "max_quantity cannot be less than min_quantity."})

        return attrs


class PriceListSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    items = PriceListItemSerializer(many=True, read_only=True)
    job_rules_count = serializers.SerializerMethodField()
    job_rules = PriceListJobRuleSerializer(many=True, read_only=True)

    class Meta:
        model = PriceList
        fields = [
            "id",
            "company_id",
            "price_list_code",
            "price_list_name",
            "list_type",
            "scope",
            "party_id",
            "currency_id",
            "valid_from",
            "valid_to",
            "is_default",
            "description",
            "record_status",
            "items_count",
            "items",
            "job_rules_count",
            "job_rules",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "company_id", "record_status", "created_at", "updated_at"]

    def get_items_count(self, obj) -> int:
        return obj.items.filter(record_status="A").count() if hasattr(obj, "items") else 0

    def get_job_rules_count(self, obj) -> int:
        return obj.job_rules.filter(record_status="A").count() if hasattr(obj, "job_rules") else 0


class PriceListCreateSerializer(serializers.Serializer):
    price_list_code = serializers.CharField(max_length=50)
    price_list_name = serializers.CharField(max_length=150)
    list_type = serializers.ChoiceField(choices=PriceListType.CHOICES)
    scope = serializers.ChoiceField(choices=PriceListScope.CHOICES, default=PriceListScope.GENERAL)
    party_id = serializers.IntegerField(required=False, allow_null=True)
    currency_id = serializers.IntegerField(default=1)
    valid_from = serializers.DateField()
    valid_to = serializers.DateField()
    is_default = serializers.BooleanField(default=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    items = PriceListItemCreateSerializer(many=True, required=False)
    job_rules = PriceListJobRuleCreateSerializer(many=True, required=False)

    def validate(self, attrs):
        valid_from = attrs.get("valid_from")
        valid_to = attrs.get("valid_to")
        if valid_from and valid_to and valid_from > valid_to:
            raise serializers.ValidationError({"valid_to": "valid_to date cannot be earlier than valid_from date."})

        scope = attrs.get("scope", PriceListScope.GENERAL)
        party_id = attrs.get("party_id")
        if scope == PriceListScope.PARTY_SPECIFIC and not party_id:
            raise serializers.ValidationError({"party_id": "party_id is required for Party-Specific price lists."})

        return attrs


class PriceListUpdateSerializer(serializers.Serializer):
    price_list_name = serializers.CharField(max_length=150, required=False)
    list_type = serializers.ChoiceField(choices=PriceListType.CHOICES, required=False)
    scope = serializers.ChoiceField(choices=PriceListScope.CHOICES, required=False)
    party_id = serializers.IntegerField(required=False, allow_null=True)
    currency_id = serializers.IntegerField(required=False)
    valid_from = serializers.DateField(required=False)
    valid_to = serializers.DateField(required=False)
    is_default = serializers.BooleanField(required=False)
    description = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    def validate(self, attrs):
        valid_from = attrs.get("valid_from")
        valid_to = attrs.get("valid_to")
        if valid_from and valid_to and valid_from > valid_to:
            raise serializers.ValidationError({"valid_to": "valid_to date cannot be earlier than valid_from date."})
        return attrs


class PricingResolveQuerySerializer(serializers.Serializer):
    context_type = serializers.ChoiceField(choices=[PriceListType.PURCHASE, PriceListType.SALES, PriceListType.JOB_WORK])
    party_id = serializers.IntegerField(required=False, allow_null=True)
    doc_date = serializers.DateField(required=False, default=timezone.now().date)
    quantity = serializers.DecimalField(max_digits=18, decimal_places=3, required=False, allow_null=True)

    # Yarn fields
    yarn_count_id = serializers.IntegerField(required=False, allow_null=True)
    yarn_type = serializers.CharField(max_length=20, required=False, allow_blank=True, allow_null=True)
    color_shade_id = serializers.IntegerField(required=False, allow_null=True)
    item_id = serializers.IntegerField(required=False, allow_null=True)

    # Job Work fields
    process_stage_id = serializers.IntegerField(required=False, allow_null=True)
    fabric_type_id = serializers.IntegerField(required=False, allow_null=True)
    machine_gauge = serializers.CharField(max_length=30, required=False, allow_blank=True, allow_null=True)
    dia_range = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    is_lycra_plated = serializers.BooleanField(required=False, allow_null=True)
    shade_category = serializers.CharField(max_length=30, required=False, allow_blank=True, allow_null=True)
    dye_class = serializers.CharField(max_length=50, required=False, allow_blank=True, allow_null=True)
    garment_style_category = serializers.CharField(max_length=100, required=False, allow_blank=True, allow_null=True)
    special_finish_requested = serializers.BooleanField(required=False, allow_null=True)
    print_color_count = serializers.IntegerField(required=False, allow_null=True)

    def validate(self, attrs):
        if attrs.get("context_type") == PriceListType.JOB_WORK:
            if not attrs.get("process_stage_id"):
                raise serializers.ValidationError({"process_stage_id": "process_stage_id is required for JOB_WORK rate resolution."})
        return attrs


YarnRateResolveQuerySerializer = PricingResolveQuerySerializer


class PricingAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = PricingAudit
        fields = [
            "id",
            "company_id",
            "document_type",
            "document_id",
            "line_item_id",
            "resolved_price_list_id",
            "resolved_rule_id",
            "system_rate",
            "actual_rate",
            "is_override",
            "override_reason",
            "approved_by",
            "created_by",
            "created_at",
        ]
        read_only_fields = fields


class PricingAuditCreateSerializer(serializers.Serializer):
    document_type = serializers.CharField(max_length=50)
    document_id = serializers.IntegerField()
    line_item_id = serializers.IntegerField(required=False, allow_null=True)
    resolved_price_list_id = serializers.IntegerField(required=False, allow_null=True)
    resolved_rule_id = serializers.IntegerField(required=False, allow_null=True)
    system_rate = serializers.DecimalField(max_digits=18, decimal_places=4)
    actual_rate = serializers.DecimalField(max_digits=18, decimal_places=4)
    override_reason = serializers.CharField(max_length=255, required=False, allow_blank=True, allow_null=True)
    approved_by = serializers.IntegerField(required=False, allow_null=True)
