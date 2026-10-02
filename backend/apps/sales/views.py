from __future__ import annotations
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from core.permissions import IsCompanyUser
from apps.sales.models import parent_yarn_sales_table, parent_yarn_sales_return_table
from apps.sales.serializers import ParentYarnSalesSerializer, ParentYarnSalesReturnSerializer
from apps.sales.services import YarnSalesService, YarnSalesReturnService


class YarnSalesViewSet(ModelViewSet):
    """API endpoint for Yarn Sales Invoices."""
    permission_classes = [IsCompanyUser]
    serializer_class = ParentYarnSalesSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['invoice_number', 'customer__name', 'mill__name', 'lot_no']
    filterset_fields = ['yarn_type', 'warehouse', 'customer', 'mill', 'yarn_count']
    ordering_fields = ['invoice_date', 'invoice_number', 'total_amount', 'created_on']

    def get_queryset(self):
        user = self.request.user
        company_id = getattr(user, 'company_id', None) or 1
        return (
            parent_yarn_sales_table.objects
            .select_related("customer", "yarn_count", "mill", "color_shade", "warehouse")
            .prefetch_related("line_items")
            .filter(company_id=company_id, status=1)
            .order_by("-invoice_date", "-id")
        )

    def create(self, request, *args, **kwargs):
        user = request.user
        company_id = getattr(user, 'company_id', None) or 1
        line_items_data = request.data.get("line_items", [])

        sales = YarnSalesService.create_sales(
            company_id=company_id,
            data=request.data,
            line_items_data=line_items_data,
            user=user if user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentYarnSalesSerializer(sales).data}, status=status.HTTP_201_CREATED)


class YarnSalesReturnViewSet(ModelViewSet):
    """API endpoint for Yarn Sales Returns."""
    permission_classes = [IsCompanyUser]
    serializer_class = ParentYarnSalesReturnSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['return_number', 'customer__name', 'mill__name', 'lot_no']
    filterset_fields = ['yarn_type', 'warehouse', 'customer', 'mill', 'yarn_count']
    ordering_fields = ['return_date', 'return_number', 'amount', 'created_on']

    def get_queryset(self):
        user = self.request.user
        company_id = getattr(user, 'company_id', None) or 1
        return (
            parent_yarn_sales_return_table.objects
            .select_related("customer", "yarn_count", "mill", "color_shade", "warehouse", "sales_invoice")
            .prefetch_related("line_items")
            .filter(company_id=company_id, status=1)
            .order_by("-return_date", "-id")
        )

    def create(self, request, *args, **kwargs):
        user = request.user
        company_id = getattr(user, 'company_id', None) or 1
        line_items_data = request.data.get("line_items", [])

        sales_return = YarnSalesReturnService.create_sales_return(
            company_id=company_id,
            data=request.data,
            line_items_data=line_items_data,
            user=user if user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentYarnSalesReturnSerializer(sales_return).data}, status=status.HTTP_201_CREATED)
