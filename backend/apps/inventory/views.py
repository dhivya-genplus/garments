from __future__ import annotations
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from core.permissions import IsCompanyUser, HasModulePrivilege
from core.constants import ModulePermissions, UserRoles
from apps.inventory.models import yarn_stock_table, parent_yarn_inward_table, parent_yarn_outward_table
from apps.inventory.serializers import (
    YarnStockSerializer, ParentYarnInwardSerializer, ParentYarnOutwardSerializer
)
from apps.inventory.services import YarnInwardService, YarnOutwardService


class YarnStockViewSet(ReadOnlyModelViewSet):
    """API endpoint to view real-time live stock of Grey and Dyed yarn."""
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.INVENTORY_YARN_STOCK
    serializer_class = YarnStockSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['lot_no', 'yarn_count__count', 'mill__name']
    filterset_fields = ['warehouse', 'yarn_type', 'yarn_count', 'mill', 'color_shade']
    ordering_fields = ['balance_quantity', 'balance_bag', 'yarn_count']

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
            yarn_stock_table.objects
            .select_related("warehouse", "yarn_count", "mill", "color_shade")
        )
        if company_id:
            qs = qs.filter(company_id=company_id)
        elif not (self.request.user.is_superuser or getattr(self.request.user, 'is_superadmin', False)):
            qs = qs.none()
        return qs.order_by("yarn_type", "yarn_count__count")


class YarnInwardViewSet(ModelViewSet):
    """API endpoint for Yarn Inward GRN from PO."""
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.INVENTORY_YARN_INWARD
    serializer_class = ParentYarnInwardSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['inward_number', 'dc_number', 'lot_no', 'mill__name', 'party__name']
    filterset_fields = ['yarn_type', 'warehouse', 'po', 'party', 'mill', 'yarn_count']
    ordering_fields = ['inward_date', 'inward_number', 'net_wt', 'created_on']

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
            parent_yarn_inward_table.objects
            .select_related("party", "mill", "warehouse", "yarn_count", "color_shade", "po")
            .prefetch_related("line_items")
            .filter(status=1)
        )
        if company_id:
            qs = qs.filter(company_id=company_id)
        elif not (self.request.user.is_superuser or getattr(self.request.user, 'is_superadmin', False)):
            qs = qs.none()
        return qs.order_by("-inward_date", "-id")

    def perform_destroy(self, instance):
        company_id = self.get_company_id() or instance.company_id
        YarnInwardService.cancel_inward(instance.id, company_id, user=self.request.user)

    def create(self, request, *args, **kwargs):
        company_id = self.get_company_id()
        line_items_data = request.data.get("line_items", [])

        inward = YarnInwardService.create_inward(
            company_id=company_id,
            data=request.data,
            line_items_data=line_items_data,
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentYarnInwardSerializer(inward).data}, status=status.HTTP_201_CREATED)


class YarnOutwardViewSet(ModelViewSet):
    """API endpoint for Yarn Outward (Knitting, Dyeing, Return)."""
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.INVENTORY_YARN_OUTWARD
    serializer_class = ParentYarnOutwardSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['outward_number', 'destination_party__name', 'lot_no', 'vehicle_no']
    filterset_fields = ['outward_type', 'yarn_type', 'warehouse', 'destination_party', 'yarn_count']
    ordering_fields = ['outward_date', 'outward_number', 'quantity', 'created_on']

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
            parent_yarn_outward_table.objects
            .select_related("warehouse", "destination_party", "yarn_count", "mill", "color_shade")
            .prefetch_related("line_items")
            .filter(status=1)
        )
        if company_id:
            qs = qs.filter(company_id=company_id)
        elif not (self.request.user.is_superuser or getattr(self.request.user, 'is_superadmin', False)):
            qs = qs.none()
        return qs.order_by("-outward_date", "-id")

    def perform_destroy(self, instance):
        company_id = self.get_company_id() or instance.company_id
        YarnOutwardService.cancel_outward(instance.id, company_id, user=self.request.user)

    def create(self, request, *args, **kwargs):
        company_id = self.get_company_id()
        line_items_data = request.data.get("line_items", [])

        outward = YarnOutwardService.create_outward(
            company_id=company_id,
            data=request.data,
            line_items_data=line_items_data,
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "data": ParentYarnOutwardSerializer(outward).data}, status=status.HTTP_201_CREATED)

