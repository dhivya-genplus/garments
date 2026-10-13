from rest_framework import status
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from core.permissions import IsCompanyUser, HasModulePrivilege
from core.constants import ModulePermissions
from core.exceptions import ValidationError
from apps.process.models import (
    parent_process_stage_table,
    parent_process_program_table,
)
from apps.process.serializers import (
    ParentProcessStageSerializer,
    ParentProcessProgramSerializer,
)
from apps.process.services import (
    ProcessStageService,
    ProcessProgramService,
)


class BaseProcessViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated, IsCompanyUser, HasModulePrivilege]

    def get_company_id(self):
        user = self.request.user
        if hasattr(user, "company_id") and user.company_id:
            return user.company_id
        if hasattr(user, "company") and user.company:
            return user.company.id
        raise ValidationError("User is not associated with any Company.")

    def get_fy_id(self):
        user = self.request.user
        if hasattr(user, "active_financial_year_id") and user.active_financial_year_id:
            return user.active_financial_year_id
        if hasattr(user, "active_financial_year") and user.active_financial_year:
            return user.active_financial_year.id
        raise ValidationError("User does not have an active Financial Year selected.")


class ProcessStageViewSet(BaseProcessViewSet):
    """
    CRUD API for configured Process Stages (Knitting, Dyeing, Cutting, etc.)
    """
    module_name = ModulePermissions.PROCESS_STAGE
    serializer_class = ParentProcessStageSerializer
    filterset_fields = ["code", "is_active", "input_from_stage", "output_to_stage"]
    search_fields = ["name", "code", "description"]
    ordering_fields = ["sequence_order", "name"]

    def get_queryset(self):
        return parent_process_stage_table.objects.filter(
            company_id=self.get_company_id(),
            is_active=True,
        ).order_by("sequence_order", "name")

    def perform_create(self, serializer):
        serializer.save(
            company_id=self.get_company_id(),
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    @action(detail=False, methods=["post"], url_path="seed-defaults")
    def seed_defaults(self, request):
        stages = ProcessStageService.seed_default_stages(self.get_company_id(), request.user)
        return Response(
            {
                "success": True,
                "message": f"Successfully seeded {len(stages)} default process stages.",
                "data": ParentProcessStageSerializer(stages, many=True).data,
            },
            status=status.HTTP_200_OK,
        )


class ProcessProgramViewSet(BaseProcessViewSet):
    """
    Production Process Program (Job Order) API.
    Supports Knitting, Dyeing, Cutting, Printing, Stitching programs.
    """
    module_name = ModulePermissions.PROCESS_PROGRAM
    serializer_class = ParentProcessProgramSerializer
    filterset_fields = ["process_stage__code", "status", "job_worker", "is_authorized"]
    search_fields = ["program_number", "input_item", "output_item", "remarks"]
    ordering_fields = ["program_date", "id", "input_quantity", "grand_total"]

    def get_queryset(self):
        return (
            parent_process_program_table.objects
            .select_related("process_stage", "job_worker", "source_warehouse", "dest_warehouse")
            .prefetch_related("input_lines", "recipe_lines")
            .filter(company_id=self.get_company_id())
            .order_by("-program_date", "-id")
        )

    def create(self, request, *args, **kwargs):
        program = ProcessProgramService.create_program(
            company_id=self.get_company_id(),
            fy_id=self.get_fy_id(),
            data=request.data.copy(),
            user=request.user,
        )
        return Response(
            {"success": True, "data": ParentProcessProgramSerializer(program).data},
            status=status.HTTP_201_CREATED,
        )

    def destroy(self, request, *args, **kwargs):
        program = ProcessProgramService.cancel_program(
            program_id=kwargs.get("pk"),
            company_id=self.get_company_id(),
            user=request.user,
        )
        return Response(
            {"success": True, "message": f"Process Program {program.program_number} cancelled successfully."},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def authorize(self, request, pk=None):
        program = ProcessProgramService.authorize_program(
            program_id=pk,
            company_id=self.get_company_id(),
            user=request.user,
        )
        return Response(
            {"success": True, "data": ParentProcessProgramSerializer(program).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def unauthorize(self, request, pk=None):
        program = ProcessProgramService.unauthorize_program(
            program_id=pk,
            company_id=self.get_company_id(),
            user=request.user,
        )
        return Response(
            {"success": True, "data": ParentProcessProgramSerializer(program).data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        data = ProcessProgramService.get_program_summary(
            program_id=pk,
            company_id=self.get_company_id(),
        )
        return Response({"success": True, "data": data}, status=status.HTTP_200_OK)
