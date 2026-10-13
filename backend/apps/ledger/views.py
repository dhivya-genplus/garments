from rest_framework import status
from rest_framework.viewsets import ReadOnlyModelViewSet, ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsCompanyUser, HasModulePrivilege
from core.constants import ModulePermissions
from core.exceptions import ValidationError
from apps.ledger.models import (
    tl_stock_movement,
    tm_stage_stock,
    tl_voucher,
)
from apps.ledger.serializers import (
    StockMovementSerializer,
    StageStockSerializer,
    VoucherSerializer,
    PartyPaymentCreateSerializer,
    PartyReceiptCreateSerializer,
)
from apps.ledger.services import (
    StockLedgerService,
    CurrencyLedgerService,
)


import django_filters


class StockMovementFilterSet(django_filters.FilterSet):
    party = django_filters.NumberFilter(field_name="party_id")
    party_id = django_filters.NumberFilter(field_name="party_id")
    party_name = django_filters.CharFilter(field_name="party__name", lookup_expr="icontains")
    warehouse = django_filters.NumberFilter(field_name="warehouse_id")
    warehouse_id = django_filters.NumberFilter(field_name="warehouse_id")
    stage = django_filters.CharFilter(field_name="stage", lookup_expr="iexact")
    movement_type = django_filters.CharFilter(field_name="movement_type", lookup_expr="iexact")
    doc_type = django_filters.CharFilter(field_name="doc_type", lookup_expr="iexact")
    doc_number = django_filters.CharFilter(field_name="doc_number", lookup_expr="icontains")
    lot_or_batch_no = django_filters.CharFilter(field_name="lot_or_batch_no", lookup_expr="icontains")
    from_date = django_filters.CharFilter(method="filter_from_date")
    to_date = django_filters.CharFilter(method="filter_to_date")

    class Meta:
        model = tl_stock_movement
        fields = [
            "party", "party_id", "party_name",
            "warehouse", "warehouse_id", "stage",
            "movement_type", "doc_type", "doc_number",
            "lot_or_batch_no"
        ]

    def filter_from_date(self, queryset, name, value):
        from core.formats import FormatService
        d = FormatService.parse_date(value)
        return queryset.filter(movement_date__gte=d) if d else queryset

    def filter_to_date(self, queryset, name, value):
        from core.formats import FormatService
        d = FormatService.parse_date(value)
        return queryset.filter(movement_date__lte=d) if d else queryset


class BaseLedgerViewSet:
    def get_company_id(self):
        user = self.request.user
        if hasattr(user, "company_id") and user.company_id:
            return user.company_id
        if hasattr(user, "company") and user.company:
            return user.company.id
        raise ValidationError("User is not associated with any Company.")


class StockMovementViewSet(BaseLedgerViewSet, ReadOnlyModelViewSet):
    """
    Physical Stock Ledger Movement audit log (In/Out/Balance).
    Filter by party: ?party_id=1 or ?party_name=Vardhman
    Filter by stage: ?stage=YARN or ?stage=GREY_FABRIC or ?stage=DYED_FABRIC
    Filter by date: ?from_date=01/04/2026&to_date=31/03/2027
    """
    permission_classes = [IsAuthenticated, IsCompanyUser, HasModulePrivilege]
    module_name = ModulePermissions.LEDGER_STOCK
    serializer_class = StockMovementSerializer
    filterset_class = StockMovementFilterSet
    search_fields = ["doc_number", "item_name", "lot_or_batch_no", "remarks", "party__name", "party__code"]
    ordering_fields = ["movement_date", "id", "balance_qty", "in_qty", "out_qty"]

    def get_queryset(self):
        return (
            tl_stock_movement.objects
            .select_related("warehouse", "party")
            .filter(company_id=self.get_company_id())
            .order_by("-movement_date", "-id")
        )

    @action(detail=False, methods=["get"], url_path="party-summary")
    def party_summary(self, request):
        party_id = request.query_params.get("party_id") or request.query_params.get("party")
        if not party_id:
            raise ValidationError("Query parameter 'party_id' is required.")
        data = StockLedgerService.get_party_stock_summary(
            company_id=self.get_company_id(),
            party_id=int(party_id),
            stage=request.query_params.get("stage"),
            from_date=request.query_params.get("from_date"),
            to_date=request.query_params.get("to_date"),
        )
        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)


class StageStockViewSet(BaseLedgerViewSet, ReadOnlyModelViewSet):
    """
    Live on-hand physical stock snapshot per stage.
    """
    permission_classes = [IsAuthenticated, IsCompanyUser, HasModulePrivilege]
    module_name = ModulePermissions.LEDGER_STOCK
    serializer_class = StageStockSerializer
    filterset_fields = ["stage", "warehouse", "lot_or_batch_no"]
    search_fields = ["item_name", "lot_or_batch_no"]
    ordering_fields = ["stage", "item_name", "balance_qty", "balance_units"]

    def get_queryset(self):
        return (
            tm_stage_stock.objects
            .select_related("warehouse")
            .filter(company_id=self.get_company_id())
            .order_by("stage", "item_name")
        )


class VoucherViewSet(BaseLedgerViewSet, ReadOnlyModelViewSet):
    """
    Currency General Ledger Vouchers (Double-Entry Dr/Cr).
    Filter by stage: ?stage=KNITTING or ?stage=DYEING or ?stage=YARN
    """
    permission_classes = [IsAuthenticated, IsCompanyUser, HasModulePrivilege]
    module_name = ModulePermissions.LEDGER_CURRENCY
    serializer_class = VoucherSerializer
    filterset_fields = ["voucher_type", "stage", "party", "is_posted", "is_reversed"]
    search_fields = ["voucher_number", "reference_no", "narration"]
    ordering_fields = ["voucher_date", "id", "total_debit"]

    def get_queryset(self):
        return (
            tl_voucher.objects
            .select_related("party")
            .prefetch_related("lines__party")
            .filter(company_id=self.get_company_id())
            .order_by("-voucher_date", "-id")
        )

    @action(detail=True, methods=["post"])
    def reverse(self, request, pk=None):
        reversal = CurrencyLedgerService.reverse_voucher(
            voucher_id=pk,
            company_id=self.get_company_id(),
            reversal_date=request.data.get("reversal_date"),
            user=request.user,
        )
        return Response(
            {
                "success": True,
                "message": f"Voucher successfully reversed by {reversal.voucher_number}.",
                "data": VoucherSerializer(reversal).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="party-statement")
    def party_statement(self, request):
        party_id = request.query_params.get("party_id") or request.query_params.get("party")
        if not party_id:
            raise ValidationError("Query parameter 'party_id' is required.")

        data = CurrencyLedgerService.get_party_ledger_statement(
            company_id=self.get_company_id(),
            party_id=int(party_id),
            from_date=request.query_params.get("from_date"),
            to_date=request.query_params.get("to_date"),
            reference_no=request.query_params.get("reference_no") or request.query_params.get("transaction_against"),
            voucher_type=request.query_params.get("voucher_type"),
        )
        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="record-payment")
    def record_payment(self, request):
        serializer = PartyPaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        company_id = self.get_company_id()
        user = request.user
        fy_id = getattr(user, "active_financial_year_id", None) or (user.active_financial_year.id if getattr(user, "active_financial_year", None) else None)
        if not fy_id:
            from apps.authentication.models import FinancialYear
            fy = FinancialYear.objects.filter(company_id=company_id).first()
            fy_id = fy.id if fy else 1

        voucher = CurrencyLedgerService.record_party_payment(
            company_id=company_id,
            fy_id=fy_id,
            party_id=vd["party"],
            amount=vd["amount"],
            payment_date=vd.get("payment_date") or None,
            payment_mode=vd.get("payment_mode", "BANK"),
            reference_no=vd.get("reference_no", ""),
            against_doc_type=vd.get("against_doc_type", ""),
            against_doc_number=vd.get("against_doc_number", ""),
            bank_or_cash_account_name=vd.get("bank_account_name", "Bank Account"),
            narration=vd.get("narration", ""),
            user=user,
        )
        return Response(
            {
                "success": True,
                "message": f"Payment voucher {voucher.voucher_number} created successfully.",
                "data": VoucherSerializer(voucher).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["post"], url_path="record-receipt")
    def record_receipt(self, request):
        serializer = PartyReceiptCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        vd = serializer.validated_data

        company_id = self.get_company_id()
        user = request.user
        fy_id = getattr(user, "active_financial_year_id", None) or (user.active_financial_year.id if getattr(user, "active_financial_year", None) else None)
        if not fy_id:
            from apps.authentication.models import FinancialYear
            fy = FinancialYear.objects.filter(company_id=company_id).first()
            fy_id = fy.id if fy else 1

        voucher = CurrencyLedgerService.record_party_receipt(
            company_id=company_id,
            fy_id=fy_id,
            party_id=vd["party"],
            amount=vd["amount"],
            receipt_date=vd.get("receipt_date") or None,
            payment_mode=vd.get("payment_mode", "BANK"),
            reference_no=vd.get("reference_no", ""),
            against_doc_type=vd.get("against_doc_type", ""),
            against_doc_number=vd.get("against_doc_number", ""),
            bank_or_cash_account_name=vd.get("bank_account_name", "Bank Account"),
            narration=vd.get("narration", ""),
            user=user,
        )
        return Response(
            {
                "success": True,
                "message": f"Receipt voucher {voucher.voucher_number} created successfully.",
                "data": VoucherSerializer(voucher).data,
            },
            status=status.HTTP_201_CREATED,
        )

