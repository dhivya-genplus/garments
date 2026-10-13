from decimal import Decimal
from rest_framework import serializers
from apps.ledger.models import (
    tl_stock_movement,
    tm_stage_stock,
    tl_voucher,
    tl_voucher_line,
)


class StockMovementSerializer(serializers.ModelSerializer):
    movement_date = serializers.DateField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"])
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)
    party_name = serializers.CharField(source="party.name", read_only=True)

    class Meta:
        model = tl_stock_movement
        fields = [
            "id",
            "movement_date",
            "stage",
            "warehouse",
            "warehouse_name",
            "movement_type",
            "doc_type",
            "doc_number",
            "item_name",
            "lot_or_batch_no",
            "in_units",
            "in_qty",
            "out_units",
            "out_qty",
            "balance_units",
            "balance_qty",
            "unit_rate",
            "total_value",
            "party",
            "party_name",
            "remarks",
            "created_on",
        ]
        read_only_fields = ["id", "balance_units", "balance_qty", "total_value", "created_on"]


class StageStockSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.CharField(source="warehouse.name", read_only=True)

    class Meta:
        model = tm_stage_stock
        fields = [
            "id",
            "stage",
            "warehouse",
            "warehouse_name",
            "item_name",
            "lot_or_batch_no",
            "dia",
            "gsm",
            "inward_units",
            "inward_qty",
            "outward_units",
            "outward_qty",
            "balance_units",
            "balance_qty",
            "updated_on",
        ]
        read_only_fields = ["id", "balance_units", "balance_qty", "updated_on"]


class VoucherLineSerializer(serializers.ModelSerializer):
    party_name = serializers.CharField(source="party.name", read_only=True)

    class Meta:
        model = tl_voucher_line
        fields = [
            "id",
            "account_code",
            "account_name",
            "party",
            "party_name",
            "debit",
            "credit",
            "narration",
        ]


class VoucherSerializer(serializers.ModelSerializer):
    voucher_date = serializers.DateField(format="%d/%m/%Y", input_formats=["%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d"])
    party_name = serializers.CharField(source="party.name", read_only=True)
    lines = VoucherLineSerializer(many=True, read_only=True)

    class Meta:
        model = tl_voucher
        fields = [
            "id",
            "voucher_number",
            "voucher_date",
            "voucher_type",
            "stage",
            "party",
            "party_name",
            "reference_type",
            "reference_no",
            "reference_id",
            "narration",
            "total_debit",
            "total_credit",
            "is_posted",
            "is_reversed",
            "lines",
            "created_on",
        ]
        read_only_fields = ["id", "voucher_number", "total_debit", "total_credit", "is_posted", "is_reversed", "created_on"]


class PartyPaymentCreateSerializer(serializers.Serializer):
    party = serializers.IntegerField(required=False)
    party_id = serializers.IntegerField(required=False)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal("0.01"), required=True)
    payment_date = serializers.CharField(required=False, default="")
    payment_mode = serializers.CharField(required=False, default="BANK")
    reference_no = serializers.CharField(required=False, allow_blank=True, default="")
    against_doc_type = serializers.CharField(required=False, allow_blank=True, default="")
    against_doc_number = serializers.CharField(required=False, allow_blank=True, default="")
    bank_account_name = serializers.CharField(required=False, default="Bank Account")
    narration = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        p = attrs.get("party") or attrs.get("party_id")
        if not p:
            raise serializers.ValidationError({"party": "party or party_id is required."})
        attrs["party"] = p
        return attrs


class PartyReceiptCreateSerializer(serializers.Serializer):
    party = serializers.IntegerField(required=False)
    party_id = serializers.IntegerField(required=False)
    amount = serializers.DecimalField(max_digits=15, decimal_places=2, min_value=Decimal("0.01"), required=True)
    receipt_date = serializers.CharField(required=False, default="")
    payment_mode = serializers.CharField(required=False, default="BANK")
    reference_no = serializers.CharField(required=False, allow_blank=True, default="")
    against_doc_type = serializers.CharField(required=False, allow_blank=True, default="")
    against_doc_number = serializers.CharField(required=False, allow_blank=True, default="")
    bank_account_name = serializers.CharField(required=False, default="Bank Account")
    narration = serializers.CharField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        p = attrs.get("party") or attrs.get("party_id")
        if not p:
            raise serializers.ValidationError({"party": "party or party_id is required."})
        attrs["party"] = p
        return attrs

