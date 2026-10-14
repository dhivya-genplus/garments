from __future__ import annotations
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from core.permissions import IsCompanyUser, HasModulePrivilege
from core.constants import ModulePermissions, UserRoles, PriceListType
from core.exceptions import ValidationError, ResourceNotFound
from apps.pricing.repositories import (
    PriceListRepository,
    PriceListItemRepository,
    PriceListJobRuleRepository,
    PricingAuditRepository
)
from apps.pricing.services import PriceListService, PricingResolutionService
from apps.pricing.serializers import (
    PriceListSerializer,
    PriceListCreateSerializer,
    PriceListUpdateSerializer,
    PriceListItemSerializer,
    PriceListItemCreateSerializer,
    PriceListJobRuleSerializer,
    PriceListJobRuleCreateSerializer,
    PricingResolveQuerySerializer,
    YarnRateResolveQuerySerializer,
    PricingAuditSerializer,
    PricingAuditCreateSerializer
)


def get_request_company_id(request) -> int:
    user = request.user
    if (getattr(user, "is_superadmin", False) or getattr(user, "role", "") == UserRoles.SUPER_ADMIN or getattr(user, "is_superuser", False)) and request.query_params.get("company_id"):
        return int(request.query_params.get("company_id"))
    if getattr(request, "company", None):
        return request.company.id
    if getattr(user, "company", None):
        return user.company.id
    if getattr(user, "company_id", None):
        return user.company_id
    return 1  # Default fallback tenant


class PriceListListCreateView(APIView):
    """
    GET  /api/v1/pricing/lists/  -> List company price lists
    POST /api/v1/pricing/lists/  -> Create price list
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.PRICING_MANAGE

    def get(self, request):
        company_id = get_request_company_id(request)
        list_type = request.query_params.get("list_type")
        scope = request.query_params.get("scope")
        party_id = request.query_params.get("party_id")
        party_id_int = int(party_id) if party_id else None

        qs = PriceListRepository.list_by_company(
            company_id=company_id,
            list_type=list_type,
            scope=scope,
            party_id=party_id_int
        )
        serializer = PriceListSerializer(qs, many=True)
        return Response({
            "success": True,
            "data": serializer.data,
            "meta": {"total_count": len(serializer.data)}
        }, status=status.HTTP_200_OK)

    def post(self, request):
        company_id = get_request_company_id(request)
        serializer = PriceListCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        items_data = data.pop("items", None)
        job_rules_data = data.pop("job_rules", None)

        user_id = request.user.id if request.user and request.user.is_authenticated else None
        price_list = PriceListService.create_price_list(data, company_id=company_id, user_id=user_id)

        # Create any inline items if provided
        if items_data:
            for item in items_data:
                PriceListService.add_item(price_list.id, item, company_id=company_id, user_id=user_id)

        # Create any inline job rules if provided
        if job_rules_data:
            for rule in job_rules_data:
                PriceListService.add_job_rule(price_list.id, rule, company_id=company_id, user_id=user_id)

        # Fetch fresh with items and job rules
        refreshed = PriceListRepository.get_by_id(price_list.id, company_id)
        return Response({
            "success": True,
            "data": PriceListSerializer(refreshed).data
        }, status=status.HTTP_201_CREATED)


class PriceListDetailView(APIView):
    """
    GET    /api/v1/pricing/lists/{id}/ -> Retrieve price list & active lines
    PUT    /api/v1/pricing/lists/{id}/ -> Update price list header
    DELETE /api/v1/pricing/lists/{id}/ -> Soft delete price list
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.PRICING_MANAGE

    def get(self, request, pk: int):
        company_id = get_request_company_id(request)
        price_list = PriceListRepository.get_by_id(pk, company_id)
        if not price_list:
            return Response({"success": False, "error": {"code": "NOT_FOUND", "message": f"Price list #{pk} not found."}}, status=status.HTTP_404_NOT_FOUND)

        items_qs = PriceListItemRepository.list_by_price_list(pk, company_id)
        job_rules_qs = PriceListJobRuleRepository.list_by_price_list(pk, company_id)
        data = PriceListSerializer(price_list).data
        data["items"] = PriceListItemSerializer(items_qs, many=True).data
        data["job_rules"] = PriceListJobRuleSerializer(job_rules_qs, many=True).data

        return Response({
            "success": True,
            "data": data
        }, status=status.HTTP_200_OK)

    def put(self, request, pk: int):
        company_id = get_request_company_id(request)
        serializer = PriceListUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = request.user.id if request.user and request.user.is_authenticated else None
        updated = PriceListService.update_price_list(pk, serializer.validated_data, company_id=company_id, user_id=user_id)

        return Response({
            "success": True,
            "data": PriceListSerializer(updated).data
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk: int):
        company_id = get_request_company_id(request)
        user_id = request.user.id if request.user and request.user.is_authenticated else None
        PriceListService.delete_price_list(pk, company_id=company_id, user_id=user_id)

        return Response({
            "success": True,
            "data": {"message": f"Price list #{pk} successfully deleted."}
        }, status=status.HTTP_200_OK)


class PriceListItemListCreateView(APIView):
    """
    GET  /api/v1/pricing/lists/{id}/items/ -> List lines
    POST /api/v1/pricing/lists/{id}/items/ -> Add line/slab
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.PRICING_MANAGE

    def get(self, request, list_id: int):
        company_id = get_request_company_id(request)
        items_qs = PriceListItemRepository.list_by_price_list(list_id, company_id)
        serializer = PriceListItemSerializer(items_qs, many=True)
        return Response({
            "success": True,
            "data": serializer.data,
            "meta": {"total_count": len(serializer.data)}
        }, status=status.HTTP_200_OK)

    def post(self, request, list_id: int):
        company_id = get_request_company_id(request)
        serializer = PriceListItemCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = request.user.id if request.user and request.user.is_authenticated else None
        item = PriceListService.add_item(list_id, serializer.validated_data, company_id=company_id, user_id=user_id)

        return Response({
            "success": True,
            "data": PriceListItemSerializer(item).data
        }, status=status.HTTP_201_CREATED)


class PriceListItemDetailView(APIView):
    """
    GET    /api/v1/pricing/items/{id}/ -> Retrieve item
    PUT    /api/v1/pricing/items/{id}/ -> Update item
    DELETE /api/v1/pricing/items/{id}/ -> Soft delete item
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.PRICING_MANAGE

    def get(self, request, pk: int):
        company_id = get_request_company_id(request)
        item = PriceListItemRepository.get_by_id(pk, company_id)
        if not item:
            return Response({"success": False, "error": {"code": "NOT_FOUND", "message": f"Price list item #{pk} not found."}}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "success": True,
            "data": PriceListItemSerializer(item).data
        }, status=status.HTTP_200_OK)

    def put(self, request, pk: int):
        company_id = get_request_company_id(request)
        serializer = PriceListItemCreateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        user_id = request.user.id if request.user and request.user.is_authenticated else None
        item = PriceListService.update_item(pk, serializer.validated_data, company_id=company_id, user_id=user_id)

        return Response({
            "success": True,
            "data": PriceListItemSerializer(item).data
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk: int):
        company_id = get_request_company_id(request)
        user_id = request.user.id if request.user and request.user.is_authenticated else None
        PriceListService.delete_item(pk, company_id=company_id, user_id=user_id)

        return Response({
            "success": True,
            "data": {"message": f"Price list item #{pk} successfully deleted."}
        }, status=status.HTTP_200_OK)


class PriceListJobRuleListCreateView(APIView):
    """
    GET  /api/v1/pricing/lists/{id}/job-rules/ -> List job rules
    POST /api/v1/pricing/lists/{id}/job-rules/ -> Add job rule
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.PRICING_MANAGE

    def get(self, request, list_id: int):
        company_id = get_request_company_id(request)
        rules_qs = PriceListJobRuleRepository.list_by_price_list(list_id, company_id)
        serializer = PriceListJobRuleSerializer(rules_qs, many=True)
        return Response({
            "success": True,
            "data": serializer.data,
            "meta": {"total_count": len(serializer.data)}
        }, status=status.HTTP_200_OK)

    def post(self, request, list_id: int):
        company_id = get_request_company_id(request)
        serializer = PriceListJobRuleCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user_id = request.user.id if request.user and request.user.is_authenticated else None
        rule = PriceListService.add_job_rule(list_id, serializer.validated_data, company_id=company_id, user_id=user_id)

        return Response({
            "success": True,
            "data": PriceListJobRuleSerializer(rule).data
        }, status=status.HTTP_201_CREATED)


class PriceListJobRuleDetailView(APIView):
    """
    GET    /api/v1/pricing/job-rules/{id}/ -> Retrieve job rule
    PUT    /api/v1/pricing/job-rules/{id}/ -> Update job rule
    DELETE /api/v1/pricing/job-rules/{id}/ -> Soft delete job rule
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.PRICING_MANAGE

    def get(self, request, pk: int):
        company_id = get_request_company_id(request)
        rule = PriceListJobRuleRepository.get_by_id(pk, company_id)
        if not rule:
            return Response({"success": False, "error": {"code": "NOT_FOUND", "message": f"Price list job rule #{pk} not found."}}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            "success": True,
            "data": PriceListJobRuleSerializer(rule).data
        }, status=status.HTTP_200_OK)

    def put(self, request, pk: int):
        company_id = get_request_company_id(request)
        serializer = PriceListJobRuleCreateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        user_id = request.user.id if request.user and request.user.is_authenticated else None
        rule = PriceListService.update_job_rule(pk, serializer.validated_data, company_id=company_id, user_id=user_id)

        return Response({
            "success": True,
            "data": PriceListJobRuleSerializer(rule).data
        }, status=status.HTTP_200_OK)

    def delete(self, request, pk: int):
        company_id = get_request_company_id(request)
        user_id = request.user.id if request.user and request.user.is_authenticated else None
        PriceListService.delete_job_rule(pk, company_id=company_id, user_id=user_id)

        return Response({
            "success": True,
            "data": {"message": f"Price list job rule #{pk} successfully deleted."}
        }, status=status.HTTP_200_OK)


class PricingResolveView(APIView):
    """
    POST /api/v1/pricing/resolve/ -> Unified Rate Determination Engine Lookup
    Used by POs, Sales Invoices, Process Programs, and Job Cards to resolve exact rates.
    """
    permission_classes = [IsCompanyUser]

    def post(self, request):
        company_id = get_request_company_id(request)
        serializer = PricingResolveQuerySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data

        context_type = query["context_type"]

        if context_type == PriceListType.JOB_WORK:
            result = PricingResolutionService.resolve_job_work_rate(
                company_id=company_id,
                process_stage_id=query["process_stage_id"],
                doc_date=query.get("doc_date"),
                party_id=query.get("party_id"),
                fabric_type_id=query.get("fabric_type_id"),
                yarn_count_id=query.get("yarn_count_id"),
                machine_gauge=query.get("machine_gauge"),
                dia_range=query.get("dia_range"),
                is_lycra_plated=query.get("is_lycra_plated"),
                shade_category=query.get("shade_category"),
                garment_style_category=query.get("garment_style_category"),
                quantity=query.get("quantity"),
                special_finish_requested=query.get("special_finish_requested"),
                print_color_count=query.get("print_color_count")
            )
        else:
            result = PricingResolutionService.resolve_yarn_rate(
                company_id=company_id,
                context_type=context_type,
                doc_date=query.get("doc_date"),
                party_id=query.get("party_id"),
                yarn_count_id=query.get("yarn_count_id"),
                yarn_type=query.get("yarn_type"),
                color_shade_id=query.get("color_shade_id"),
                quantity=query.get("quantity"),
                item_id=query.get("item_id")
            )

        return Response({
            "success": True,
            "data": result
        }, status=status.HTTP_200_OK)


class PricingAuditListView(APIView):
    """
    GET  /api/v1/pricing/audit/ -> View price overrides and audit log (all or by document)
    POST /api/v1/pricing/audit/ -> Manually record a rate resolution or managerial override
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.PRICING_VIEW

    def get(self, request):
        company_id = get_request_company_id(request)
        doc_type = request.query_params.get("document_type")
        doc_id = request.query_params.get("document_id")
        doc_id_int = int(doc_id) if doc_id else None
        is_override = request.query_params.get("is_override")
        is_override_bool = (is_override.lower() in ("true", "1")) if is_override is not None else None

        qs = PricingAuditRepository.list_by_company(
            company_id=company_id,
            document_type=doc_type,
            document_id=doc_id_int,
            is_override=is_override_bool
        )
        serializer = PricingAuditSerializer(qs, many=True)
        return Response({
            "success": True,
            "data": serializer.data,
            "meta": {"total_count": len(serializer.data)}
        }, status=status.HTTP_200_OK)

    def post(self, request):
        company_id = get_request_company_id(request)
        serializer = PricingAuditCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        user_id = request.user.id if request.user and request.user.is_authenticated else None
        audit = PricingResolutionService.record_override_audit(
            company_id=company_id,
            document_type=data["document_type"],
            document_id=data["document_id"],
            system_rate=data["system_rate"],
            actual_rate=data["actual_rate"],
            resolved_price_list_id=data.get("resolved_price_list_id"),
            resolved_rule_id=data.get("resolved_rule_id"),
            override_reason=data.get("override_reason"),
            approved_by=data.get("approved_by"),
            created_by=user_id,
            line_item_id=data.get("line_item_id")
        )
        return Response({
            "success": True,
            "data": PricingAuditSerializer(audit).data
        }, status=status.HTTP_201_CREATED)


class PricingSeedDefaultsView(APIView):
    """
    POST /api/v1/pricing/seed-defaults/ -> Seeds standard realistic default price lists for the company.
    """
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    required_module = ModulePermissions.PRICING_MANAGE

    def post(self, request):
        company_id = get_request_company_id(request)
        user_id = request.user.id if request.user and request.user.is_authenticated else None
        seeded_lists = PriceListService.seed_default_price_lists(company_id=company_id, user_id=user_id)
        serializer = PriceListSerializer(seeded_lists, many=True)
        return Response({
            "success": True,
            "message": f"Successfully seeded {len(seeded_lists)} price lists with item lines.",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED)

