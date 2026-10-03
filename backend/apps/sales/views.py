from __future__ import annotations
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from core.permissions import IsCompanyUser, HasModulePrivilege
from core.constants import ModulePermissions, UserRoles
from apps.sales.models import parent_yarn_sales_table, parent_yarn_sales_return_table
from apps.sales.serializers import ParentYarnSalesSerializer, ParentYarnSalesReturnSerializer
from apps.sales.services import YarnSalesService, YarnSalesReturnService


class YarnSalesViewSet(ModelViewSet):
    """API endpoint for Yarn Sales Invoices."""
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.SALES_YARN
    serializer_class = ParentYarnSalesSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['invoice_number', 'customer__name', 'mill__name', 'lot_no']
    filterset_fields = ['yarn_type', 'warehouse', 'customer', 'mill', 'yarn_count']
    ordering_fields = ['invoice_date', 'invoice_number', 'total_amount', 'created_on']

    def get_company_id(self):
        user = self.request.user
        if (getattr(user, 'is_superadmin', False) or getattr(user, 'role', '') == UserRoles.SUPER_ADMIN or user.is_superuser) and self.request.query_params.get('company_id'):
            return int(self.request.query_params.get('company_id'))
        if getattr(self.request, 'company', None):
            return self.request.company.id
        if getattr(user, 'company', None):
            return user.company.id
        return None

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = (
            parent_yarn_sales_table.objects
            .select_related("customer", "yarn_count", "mill", "color_shade", "warehouse")
            .prefetch_related("line_items")
            .filter(status=1)
        )
        if company_id:
            qs = qs.filter(company_id=company_id)
        elif not (self.request.user.is_superuser or getattr(self.request.user, 'is_superadmin', False)):
            qs = qs.none()
        return qs.order_by("-invoice_date", "-id")

    def perform_destroy(self, instance):
        company_id = self.get_company_id() or instance.company_id
        YarnSalesService.cancel_sales(instance.id, company_id, user=self.request.user)

    def create(self, request, *args, **kwargs):
        company_id = self.get_company_id()
        line_items_data = request.data.get("line_items", [])

        sales = YarnSalesService.create_sales(
            company_id=company_id,
            data=request.data,
            line_items_data=line_items_data,
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentYarnSalesSerializer(sales).data}, status=status.HTTP_201_CREATED)


class YarnSalesReturnViewSet(ModelViewSet):
    """API endpoint for Yarn Sales Returns."""
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.SALES_YARN_RETURN
    serializer_class = ParentYarnSalesReturnSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['return_number', 'customer__name', 'mill__name', 'lot_no']
    filterset_fields = ['yarn_type', 'warehouse', 'customer', 'mill', 'yarn_count']
    ordering_fields = ['return_date', 'return_number', 'amount', 'created_on']

    def get_company_id(self):
        user = self.request.user
        if (getattr(user, 'is_superadmin', False) or getattr(user, 'role', '') == UserRoles.SUPER_ADMIN or user.is_superuser) and self.request.query_params.get('company_id'):
            return int(self.request.query_params.get('company_id'))
        if getattr(self.request, 'company', None):
            return self.request.company.id
        if getattr(user, 'company', None):
            return user.company.id
        return None

    def get_queryset(self):
        company_id = self.get_company_id()
        qs = (
            parent_yarn_sales_return_table.objects
            .select_related("customer", "yarn_count", "mill", "color_shade", "warehouse", "sales_invoice")
            .prefetch_related("line_items")
            .filter(status=1)
        )
        if company_id:
            qs = qs.filter(company_id=company_id)
        elif not (self.request.user.is_superuser or getattr(self.request.user, 'is_superadmin', False)):
            qs = qs.none()
        return qs.order_by("-return_date", "-id")

    def perform_destroy(self, instance):
        company_id = self.get_company_id() or instance.company_id
        YarnSalesReturnService.cancel_sales_return(instance.id, company_id, user=self.request.user)

    def create(self, request, *args, **kwargs):
        company_id = self.get_company_id()
        line_items_data = request.data.get("line_items", [])

        sales_return = YarnSalesReturnService.create_sales_return(
            company_id=company_id,
            data=request.data,
            line_items_data=line_items_data,
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentYarnSalesReturnSerializer(sales_return).data}, status=status.HTTP_201_CREATED)

