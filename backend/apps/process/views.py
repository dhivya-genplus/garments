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
    JobWorkMaster,
    JobWorkPartyConfiguration,
)
from apps.process.serializers import (
    ParentProcessStageSerializer,
    ParentProcessProgramSerializer,
    JobWorkSerializer,
    JobWorkPartyConfigSerializer,
    JobWorkOrderValidationSerializer,
    JobWorkScheduleCalculationSerializer,
)
from apps.process.services import (
    ProcessStageService,
    ProcessProgramService,
    JobWorkService,
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


class JobWorkViewSet(BaseProcessViewSet):
    """
    Job Work Operation Master API.
    Provides CRUD, order validation against MOQ / capacity thresholds,
    milestone lead-time delivery schedule calculation, and seeding.
    """
    module_name = ModulePermissions.PROCESS_STAGE
    serializer_class = JobWorkSerializer
    filterset_fields = ["job_work_category", "material_type", "is_active", "process_stage_id"]
    search_fields = ["job_work_code", "job_work_name", "description"]
    ordering_fields = ["job_work_code", "job_work_name", "total_estimated_lead_time", "standard_rate"]

    def get_queryset(self):
        return JobWorkMaster.objects.filter(
            company_id=self.get_company_id(),
            record_status="A"
        ).order_by("job_work_code")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job_work = JobWorkService.create_job_work(
            data=serializer.validated_data,
            company_id=self.get_company_id(),
            user_id=request.user.id
        )
        return Response(
            {"success": True, "data": JobWorkSerializer(job_work).data},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        job_work = JobWorkService.update_job_work(
            job_work_id=int(kwargs.get("pk")),
            data=serializer.validated_data,
            company_id=self.get_company_id(),
            user_id=request.user.id
        )
        return Response(
            {"success": True, "data": JobWorkSerializer(job_work).data},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        JobWorkService.delete_job_work(
            job_work_id=int(kwargs.get("pk")),
            company_id=self.get_company_id(),
            user_id=request.user.id
        )
        return Response(
            {"success": True, "message": f"Job Work #{kwargs.get('pk')} deleted successfully."},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["post"], url_path="validate-order")
    def validate_order(self, request):
        serializer = JobWorkOrderValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = JobWorkService.validate_job_work_order(
            company_id=self.get_company_id(),
            job_work_id=serializer.validated_data["job_work_id"],
            quantity=serializer.validated_data["quantity"],
            party_id=serializer.validated_data.get("party_id"),
            uom_id=serializer.validated_data.get("uom_id"),
        )
        return Response({"success": True, "data": result}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="calculate-schedule")
    def calculate_schedule(self, request):
        serializer = JobWorkScheduleCalculationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = JobWorkService.calculate_schedule(
            company_id=self.get_company_id(),
            job_work_id=serializer.validated_data["job_work_id"],
            order_date=serializer.validated_data["order_date"],
            quantity=serializer.validated_data.get("quantity"),
            party_id=serializer.validated_data.get("party_id"),
            is_fast_track=serializer.validated_data.get("is_fast_track", False),
        )
        return Response({"success": True, "data": result}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="seed-defaults")
    def seed_defaults(self, request):
        masters = JobWorkService.seed_default_job_works(
            company_id=self.get_company_id(),
            user_id=request.user.id
        )
        return Response(
            {
                "success": True,
                "message": f"Successfully seeded {len(masters)} default job work operations and vendor terms.",
                "data": JobWorkSerializer(masters, many=True).data
            },
            status=status.HTTP_200_OK
        )


class JobWorkPartyConfigViewSet(BaseProcessViewSet):
    """
    Job Worker Specific Terms and Capacity Configuration API.
    """
    module_name = ModulePermissions.PROCESS_STAGE
    serializer_class = JobWorkPartyConfigSerializer
    filterset_fields = ["job_work_id", "party_id", "is_active"]
    search_fields = ["remarks"]
    ordering_fields = ["effective_from", "agreed_rate", "total_estimated_lead_time"]

    def get_queryset(self):
        return JobWorkPartyConfiguration.objects.filter(
            company_id=self.get_company_id(),
            record_status="A"
        ).order_by("-effective_from", "-id")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        config = JobWorkService.create_party_config(
            data=serializer.validated_data,
            company_id=self.get_company_id(),
            user_id=request.user.id
        )
        return Response(
            {"success": True, "data": JobWorkPartyConfigSerializer(config).data},
            status=status.HTTP_201_CREATED
        )

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, partial=kwargs.get("partial", False))
        serializer.is_valid(raise_exception=True)
        config = JobWorkService.update_party_config(
            config_id=int(kwargs.get("pk")),
            data=serializer.validated_data,
            company_id=self.get_company_id(),
            user_id=request.user.id
        )
        return Response(
            {"success": True, "data": JobWorkPartyConfigSerializer(config).data},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, *args, **kwargs):
        config = JobWorkPartyConfiguration.objects.filter(
            id=int(kwargs.get("pk")),
            company_id=self.get_company_id(),
            record_status="A"
        ).first()
        if not config:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "Configuration not found"}},
                status=status.HTTP_404_NOT_FOUND
            )
        config.soft_delete(request.user.id)
        return Response(
            {"success": True, "message": f"Job Work Party Configuration #{kwargs.get('pk')} deleted successfully."},
            status=status.HTTP_200_OK
        )
