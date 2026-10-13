from __future__ import annotations
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from core.permissions import IsCompanyUser, HasModulePrivilege
from core.constants import ModulePermissions, UserRoles
from apps.knitting.models import (
    parent_knitting_program_table,
    grey_fabric_stock_table,
    parent_grey_fabric_inward_table,
    parent_grey_fabric_outward_table,
    parent_grey_po_table,
    parent_grey_fabric_sales_table,
    parent_grey_fabric_sales_return_table,
)
from apps.knitting.serializers import (
    ParentKnittingProgramSerializer,
    GreyFabricStockSerializer,
    ParentGreyFabricInwardSerializer,
    ParentGreyFabricOutwardSerializer,
    ParentGreyPOSerializer,
    ParentGreyFabricSalesSerializer,
    ParentGreyFabricSalesReturnSerializer,
)
from apps.knitting.services import (
    KnittingProgramService,
    GreyFabricInwardService,
    GreyFabricOutwardService,
    GreyPOService,
    GreyFabricSalesService,
    GreyFabricSalesReturnService,
)


class BaseKnittingViewSet:
    def get_company_id(self):
        user = self.request.user
        if (getattr(user, 'is_superadmin', False) or getattr(user, 'role', '') == UserRoles.SUPER_ADMIN or user.is_superuser) and self.request.query_params.get('company_id'):
            return int(self.request.query_params.get('company_id'))
        if getattr(self.request, 'company', None):
            return self.request.company.id
        if getattr(user, 'company', None):
            return user.company.id
        return None

    def get_fy_id(self):
        user = self.request.user
        if getattr(self.request, 'financial_year', None):
            return self.request.financial_year.id
        if getattr(user, 'active_financial_year', None):
            return user.active_financial_year.id
        return None


class KnittingProgramViewSet(BaseKnittingViewSet, ModelViewSet):
    """
    API endpoint for Knitting Programs (Job Cards).
    Plans fabric specs, computes required yarn kg and loss %, and tracks progress.
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.KNITTING_PROGRAM
    serializer_class = ParentKnittingProgramSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['program_number', 'knitter__name', 'fabric__fabric_name', 'dia', 'gauge']
    filterset_fields = ['knitter', 'warehouse', 'fabric', 'fabric_type', 'status']
    ordering_fields = ['program_date', 'program_number', 'planned_fabric_quantity', 'created_on']

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = (
            parent_knitting_program_table.objects
            .select_related("knitter", "warehouse", "fabric", "fabric_type")
            .prefetch_related("yarn_lines")
        )
        if company_id:
            qs = qs.filter(company_id=company_id)
        elif not (self.request.user.is_superuser or getattr(self.request.user, 'is_superadmin', False)):
            qs = qs.none()
        return qs.order_by("-program_date", "-id")

    def create(self, request, *args, **kwargs):
        company_id = self.get_company_id()
        fy_id = self.get_fy_id()
        program = KnittingProgramService.create_program(
            company_id=company_id,
            fy_id=fy_id,
            data=dict(request.data),
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentKnittingProgramSerializer(program).data}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def authorize(self, request, pk=None):
        company_id = self.get_company_id()
        program = KnittingProgramService.authorize_program(
            program_id=pk,
            company_id=company_id,
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentKnittingProgramSerializer(program).data})

    @action(detail=True, methods=['post'])
    def unauthorize(self, request, pk=None):
        company_id = self.get_company_id()
        program = KnittingProgramService.unauthorize_program(
            program_id=pk,
            company_id=company_id,
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentKnittingProgramSerializer(program).data})

    @action(detail=True, methods=['get'])
    def summary(self, request, pk=None):
        company_id = self.get_company_id()
        summary_data = KnittingProgramService.get_program_summary(
            program_id=pk,
            company_id=company_id
        )
        return Response({"success": True, "data": summary_data})


class GreyFabricStockViewSet(BaseKnittingViewSet, ReadOnlyModelViewSet):
    """
    API endpoint to view real-time live stock of Grey Fabric (Rolls & Kg).
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.KNITTING_GREY_FABRIC_STOCK
    serializer_class = GreyFabricStockSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['fabric__fabric_name', 'dia', 'lot_no']
    filterset_fields = ['warehouse', 'fabric', 'fabric_type', 'dia', 'gsm']
    ordering_fields = ['balance_quantity', 'balance_rolls', 'updated_on']

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = (
            grey_fabric_stock_table.objects
            .select_related("warehouse", "fabric", "fabric_type")
        )
        if company_id:
            qs = qs.filter(company_id=company_id)
        elif not (self.request.user.is_superuser or getattr(self.request.user, 'is_superadmin', False)):
            qs = qs.none()
        return qs.order_by("fabric__fabric_name", "dia", "gsm")


class GreyFabricInwardViewSet(BaseKnittingViewSet, ModelViewSet):
    """
    API endpoint for Grey Fabric Inward GRN from Knitter (job work) or Trader (PO).
    Increments Grey Fabric stock atomically.
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.KNITTING_GREY_FABRIC_INWARD
    serializer_class = ParentGreyFabricInwardSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['inward_number', 'dc_number', 'party__name', 'fabric__fabric_name', 'lot_no']
    filterset_fields = ['inward_source', 'warehouse', 'party', 'fabric', 'fabric_type']
    ordering_fields = ['inward_date', 'inward_number', 'net_wt', 'total_rolls']

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = (
            parent_grey_fabric_inward_table.objects
            .select_related("party", "warehouse", "fabric", "fabric_type", "knitting_program")
            .prefetch_related("line_items")
            .filter(status=1)
        )
        if company_id:
            qs = qs.filter(company_id=company_id)
        elif not (self.request.user.is_superuser or getattr(self.request.user, 'is_superadmin', False)):
            qs = qs.none()
        return qs.order_by("-inward_date", "-id")

    def create(self, request, *args, **kwargs):
        company_id = self.get_company_id()
        fy_id = self.get_fy_id()
        inward = GreyFabricInwardService.post_inward(
            company_id=company_id,
            fy_id=fy_id,
            data=dict(request.data),
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentGreyFabricInwardSerializer(inward).data}, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        company_id = self.get_company_id() or instance.company_id
        GreyFabricInwardService.cancel_inward(
            inward_id=instance.id,
            company_id=company_id,
            user=self.request.user
        )


class GreyFabricOutwardViewSet(BaseKnittingViewSet, ModelViewSet):
    """
    API endpoint for Grey Fabric Outward Delivery Challan (to Dyeing unit or Knitter return).
    Decrements Grey Fabric stock atomically.
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.KNITTING_GREY_FABRIC_OUTWARD
    serializer_class = ParentGreyFabricOutwardSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['outward_number', 'destination_party__name', 'fabric__fabric_name', 'vehicle_no']
    filterset_fields = ['outward_type', 'warehouse', 'destination_party', 'fabric', 'fabric_type']
    ordering_fields = ['outward_date', 'outward_number', 'quantity', 'rolls']

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = (
            parent_grey_fabric_outward_table.objects
            .select_related("destination_party", "warehouse", "fabric", "fabric_type")
            .prefetch_related("line_items")
            .filter(status=1)
        )
        if company_id:
            qs = qs.filter(company_id=company_id)
        elif not (self.request.user.is_superuser or getattr(self.request.user, 'is_superadmin', False)):
            qs = qs.none()
        return qs.order_by("-outward_date", "-id")

    def create(self, request, *args, **kwargs):
        company_id = self.get_company_id()
        fy_id = self.get_fy_id()
        outward = GreyFabricOutwardService.post_outward(
            company_id=company_id,
            fy_id=fy_id,
            data=dict(request.data),
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentGreyFabricOutwardSerializer(outward).data}, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        company_id = self.get_company_id() or instance.company_id
        GreyFabricOutwardService.cancel_outward(
            outward_id=instance.id,
            company_id=company_id,
            user=self.request.user
        )


class GreyPOViewSet(BaseKnittingViewSet, ModelViewSet):
    """
    API endpoint for Grey Fabric Purchase Orders from Traders.
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.KNITTING_GREY_PO
    serializer_class = ParentGreyPOSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['po_number', 'party__name']
    filterset_fields = ['party', 'warehouse', 'is_authorized']
    ordering_fields = ['po_date', 'po_number', 'total_amount']

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = (
            parent_grey_po_table.objects
            .select_related("party", "warehouse")
            .prefetch_related("line_items")
            .filter(status=1)
        )
        if company_id:
            qs = qs.filter(company_id=company_id)
        elif not (self.request.user.is_superuser or getattr(self.request.user, 'is_superadmin', False)):
            qs = qs.none()
        return qs.order_by("-po_date", "-id")

    def create(self, request, *args, **kwargs):
        company_id = self.get_company_id()
        fy_id = self.get_fy_id()
        po = GreyPOService.create_po(
            company_id=company_id,
            fy_id=fy_id,
            data=dict(request.data),
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentGreyPOSerializer(po).data}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def authorize(self, request, pk=None):
        company_id = self.get_company_id()
        po = GreyPOService.authorize_po(
            po_id=pk,
            company_id=company_id,
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentGreyPOSerializer(po).data})


class GreyFabricSalesViewSet(BaseKnittingViewSet, ModelViewSet):
    """
    API endpoint for Grey Fabric Commercial Sales Tax Invoices.
    Deducts Grey Fabric stock atomically.
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.KNITTING_GREY_FABRIC_SALES
    serializer_class = ParentGreyFabricSalesSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['invoice_number', 'customer__name', 'fabric__fabric_name']
    filterset_fields = ['customer', 'warehouse', 'fabric', 'fabric_type']
    ordering_fields = ['invoice_date', 'invoice_number', 'total_amount', 'quantity']

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = (
            parent_grey_fabric_sales_table.objects
            .select_related("customer", "warehouse", "fabric", "fabric_type")
            .prefetch_related("line_items")
            .filter(status=1)
        )
        if company_id:
            qs = qs.filter(company_id=company_id)
        elif not (self.request.user.is_superuser or getattr(self.request.user, 'is_superadmin', False)):
            qs = qs.none()
        return qs.order_by("-invoice_date", "-id")

    def create(self, request, *args, **kwargs):
        company_id = self.get_company_id()
        fy_id = self.get_fy_id()
        sales = GreyFabricSalesService.create_sales_invoice(
            company_id=company_id,
            fy_id=fy_id,
            data=dict(request.data),
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentGreyFabricSalesSerializer(sales).data}, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        company_id = self.get_company_id() or instance.company_id
        GreyFabricSalesService.cancel_sales_invoice(
            sales_id=instance.id,
            company_id=company_id,
            user=self.request.user
        )


class GreyFabricSalesReturnViewSet(BaseKnittingViewSet, ModelViewSet):
    """
    API endpoint for Grey Fabric Customer Sales Returns.
    Re-credits Grey Fabric stock atomically.
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.KNITTING_GREY_FABRIC_SALES_RETURN
    serializer_class = ParentGreyFabricSalesReturnSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['return_number', 'customer__name', 'sales_invoice__invoice_number']
    filterset_fields = ['customer', 'warehouse', 'fabric', 'fabric_type']
    ordering_fields = ['return_date', 'return_number', 'total_amount', 'quantity']

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = (
            parent_grey_fabric_sales_return_table.objects
            .select_related("customer", "warehouse", "fabric", "fabric_type", "sales_invoice")
            .prefetch_related("line_items")
            .filter(status=1)
        )
        if company_id:
            qs = qs.filter(company_id=company_id)
        elif not (self.request.user.is_superuser or getattr(self.request.user, 'is_superadmin', False)):
            qs = qs.none()
        return qs.order_by("-return_date", "-id")

    def create(self, request, *args, **kwargs):
        company_id = self.get_company_id()
        fy_id = self.get_fy_id()
        ret = GreyFabricSalesReturnService.create_sales_return(
            company_id=company_id,
            fy_id=fy_id,
            data=dict(request.data),
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentGreyFabricSalesReturnSerializer(ret).data}, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        company_id = self.get_company_id() or instance.company_id
        GreyFabricSalesReturnService.cancel_sales_return(
            return_id=instance.id,
            company_id=company_id,
            user=self.request.user
        )

