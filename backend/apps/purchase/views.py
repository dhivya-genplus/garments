from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from core.permissions import IsCompanyUser, HasModulePrivilege
from core.constants import ModulePermissions, UserRoles
from apps.purchase.models import (
    parent_po_table, child_po_table, yarn_po_delivery_table,
    yarn_po_balance_table
)
from apps.purchase.serializers import (
    ParentPOSerializer, ParentPOCreateSerializer, ChildPOSerializer,
    YarnPODeliverySerializer, YarnPOBalanceSerializer
)
from apps.purchase.services import YarnPOService
from apps.purchase.repositories import YarnPORepository


class YarnPOViewSet(ModelViewSet):
    """
    API ViewSet for Yarn Purchase Orders.
    Supports nested creation of child line items and delivery schedules,
    Grey vs Dyed yarn filtering, and approval/authorization workflow.
    """
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['po_number', 'name', 'remarks', 'party__name', 'mill__name']
    filterset_fields = ['yarn_type', 'party', 'mill', 'yarn_count', 'is_authorized', 'is_complete', 'is_active']
    ordering_fields = ['po_date', 'po_number', 'amount', 'created_on']

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return ParentPOCreateSerializer
        return ParentPOSerializer

    def get_company_id(self):
        user = self.request.user
        if (getattr(user, 'is_superadmin', False) or getattr(user, 'role', '') == UserRoles.SUPER_ADMIN or user.is_superuser) and self.request.query_params.get('company_id'):
            return int(self.request.query_params.get('company_id'))
        if getattr(self.request, 'company', None):
            return self.request.company.id
        if getattr(user, 'company', None):
            return user.company.id
        return 1

    def get_queryset(self):
        company_id = self.get_company_id()
        return (
            parent_po_table.objects
            .select_related("company", "cfyear", "party", "mill", "yarn_count", "color_shade", "authorized_by")
            .prefetch_related("line_items", "deliveries")
            .filter(company_id=company_id, status=1)
            .order_by("-po_date", "-id")
        )

    def create(self, request, *args, **kwargs):
        company_id = self.get_company_id()
        line_items_data = request.data.get("line_items", [])
        deliveries_data = request.data.get("deliveries", [])

        po = YarnPOService.create_yarn_po(
            company_id=company_id,
            data=request.data,
            line_items_data=line_items_data,
            deliveries_data=deliveries_data,
            user=request.user if request.user.is_authenticated else None
        )
        serializer = ParentPOSerializer(po)
        return Response({"success": True, "data": serializer.data}, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        company_id = self.get_company_id()
        po_id = int(kwargs.get("pk"))
        line_items_data = request.data.get("line_items")
        deliveries_data = request.data.get("deliveries")

        po = YarnPOService.update_yarn_po(
            po_id=po_id,
            company_id=company_id,
            data=request.data,
            line_items_data=line_items_data,
            deliveries_data=deliveries_data,
            user=request.user if request.user.is_authenticated else None
        )
        serializer = ParentPOSerializer(po)
        return Response({"success": True, "data": serializer.data})

    @action(detail=True, methods=['post'], url_path='authorize')
    def authorize(self, request, pk=None):
        """Authorize and lock the Yarn Purchase Order."""
        company_id = self.get_company_id()
        po = YarnPOService.authorize_yarn_po(
            po_id=int(pk),
            company_id=company_id,
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "message": f"PO #{po.po_number} successfully authorized.", "data": ParentPOSerializer(po).data})

    @action(detail=True, methods=['post'], url_path='unauthorize')
    def unauthorize(self, request, pk=None):
        """Re-open an authorized PO for edits."""
        company_id = self.get_company_id()
        po = YarnPOService.unauthorize_yarn_po(
            po_id=int(pk),
            company_id=company_id,
            user=request.user if request.user.is_authenticated else None
        )
        return Response({"success": True, "message": f"PO #{po.po_number} re-opened.", "data": ParentPOSerializer(po).data})


class YarnPODeliveryViewSet(ModelViewSet):
    permission_classes = [IsCompanyUser]
    serializer_class = YarnPODeliverySerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ['tm_po', 'party', 'yarn_count', 'is_active']
    ordering_fields = ['delivery_date', 'id']

    def get_queryset(self):
        user = self.request.user
        company_id = getattr(user, 'company_id', None) or 1
        return yarn_po_delivery_table.objects.filter(company_id=company_id, status=1).order_by("delivery_date")


class YarnPOBalanceViewSet(ReadOnlyModelViewSet):
    """Read-only view for tracking PO ordered vs inward received balances."""
    permission_classes = [IsCompanyUser]
    serializer_class = YarnPOBalanceSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['po_number']
    filterset_fields = ['yarn_type', 'yarn_count_id', 'party_id']

    def get_queryset(self):
        return yarn_po_balance_table.objects.all()
