from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from core.permissions import IsCompanyUser, HasModulePrivilege
from core.constants import ModulePermissions, UserRoles
from apps.masters.models import (
    UnitOfMeasurement, PartyMaster, YarnCountMaster, YarnTypeMaster,
    ColorShadeMaster, YarnMaster, FabricTypeMaster, FabricMaster,
    ProcessMaster, WarehouseMaster, quality_program_table, sub_quality_program_table
)
from apps.masters.serializers import (
    UOMSerializer, PartyMasterSerializer, YarnCountSerializer, YarnTypeSerializer,
    ColorShadeSerializer, YarnMasterSerializer, FabricTypeSerializer,
    FabricMasterSerializer, ProcessMasterSerializer, WarehouseMasterSerializer,
    QualityProgramSerializer, SubQualityProgramSerializer
)
from apps.masters.services import (
    UOMService, PartyService, YarnService, FabricService,
    ProcessService, WarehouseService
)
from apps.masters.repositories import (
    UOMRepository, PartyRepository, YarnCountRepository, YarnTypeRepository,
    ColorShadeRepository, YarnRepository, FabricTypeRepository, FabricRepository,
    ProcessRepository, WarehouseRepository
)

class BaseMasterViewSet(ModelViewSet):
    """Base ViewSet ensuring company scoping and RBAC permissions for all master models."""
    permission_classes = [IsCompanyUser, HasModulePrivilege]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_company_id(self):
        user = self.request.user
        if (user.is_superadmin or user.role == UserRoles.SUPER_ADMIN or user.is_superuser) and self.request.query_params.get('company_id'):
            return int(self.request.query_params.get('company_id'))
        if getattr(self.request, 'company', None):
            return self.request.company.id
        if user.company:
            return user.company.id
        return None

    def perform_destroy(self, instance):
        instance.soft_delete(user=self.request.user)


class UOMViewSet(BaseMasterViewSet):
    required_module = ModulePermissions.MASTERS_UOM
    serializer_class = UOMSerializer
    search_fields = ['code', 'name', 'symbol']
    filterset_fields = ['is_active']
    ordering_fields = ['code', 'name', 'created_on']

    def get_queryset(self):
        company_id = self.get_company_id()
        return UOMRepository.get_for_company(company_id) if company_id else UOMRepository.list_all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_id = self.get_company_id()
        instance = UOMService.create_uom(company_id, serializer.validated_data, request.user)
        return Response(UOMSerializer(instance).data, status=status.HTTP_201_CREATED)


class PartyMasterViewSet(BaseMasterViewSet):
    required_module = ModulePermissions.MASTERS_PARTY
    serializer_class = PartyMasterSerializer
    search_fields = ['code', 'name', 'contact_person', 'phone', 'email', 'gst_number', 'city']
    filterset_fields = ['party_type', 'is_active', 'city', 'state']
    ordering_fields = ['name', 'code', 'created_on']

    def get_queryset(self):
        company_id = self.get_company_id()
        return PartyRepository.get_for_company(company_id) if company_id else PartyRepository.list_all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_id = self.get_company_id()
        instance = PartyService.create_party(company_id, serializer.validated_data, request.user)
        return Response(PartyMasterSerializer(instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)
        company_id = self.get_company_id()
        updated = PartyService.update_party(instance.id, company_id, serializer.validated_data, request.user)
        return Response(PartyMasterSerializer(updated).data, status=status.HTTP_200_OK)


class YarnCountViewSet(BaseMasterViewSet):
    required_module = ModulePermissions.MASTERS_YARN
    serializer_class = YarnCountSerializer
    search_fields = ['count', 'description']
    filterset_fields = ['is_active']
    ordering_fields = ['count', 'created_on']

    def get_queryset(self):
        company_id = self.get_company_id()
        return YarnCountRepository.get_for_company(company_id) if company_id else YarnCountRepository.list_all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_id = self.get_company_id()
        instance = YarnCountRepository.create(company_id=company_id, created_by=request.user, **serializer.validated_data)
        return Response(YarnCountSerializer(instance).data, status=status.HTTP_201_CREATED)


class YarnTypeViewSet(BaseMasterViewSet):
    required_module = ModulePermissions.MASTERS_YARN
    serializer_class = YarnTypeSerializer
    search_fields = ['name', 'code', 'description']
    filterset_fields = ['is_active']
    ordering_fields = ['name', 'code', 'created_on']

    def get_queryset(self):
        company_id = self.get_company_id()
        return YarnTypeRepository.get_for_company(company_id) if company_id else YarnTypeRepository.list_all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_id = self.get_company_id()
        instance = YarnTypeRepository.create(company_id=company_id, created_by=request.user, **serializer.validated_data)
        return Response(YarnTypeSerializer(instance).data, status=status.HTTP_201_CREATED)


class ColorShadeViewSet(BaseMasterViewSet):
    required_module = ModulePermissions.MASTERS_COLOR
    serializer_class = ColorShadeSerializer
    search_fields = ['shade_code', 'color_name', 'pantone_ref']
    filterset_fields = ['is_active']
    ordering_fields = ['color_name', 'shade_code', 'created_on']

    def get_queryset(self):
        company_id = self.get_company_id()
        return ColorShadeRepository.get_for_company(company_id) if company_id else ColorShadeRepository.list_all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_id = self.get_company_id()
        instance = ColorShadeRepository.create(company_id=company_id, created_by=request.user, **serializer.validated_data)
        return Response(ColorShadeSerializer(instance).data, status=status.HTTP_201_CREATED)


class YarnMasterViewSet(BaseMasterViewSet):
    required_module = ModulePermissions.MASTERS_YARN
    serializer_class = YarnMasterSerializer
    search_fields = ['yarn_code', 'yarn_type__name', 'yarn_count__count', 'description']
    filterset_fields = ['category', 'yarn_type', 'yarn_count', 'color_shade', 'is_active']
    ordering_fields = ['yarn_code', 'created_on']

    def get_queryset(self):
        company_id = self.get_company_id()
        return YarnRepository.get_for_company(company_id) if company_id else YarnRepository.list_all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_id = self.get_company_id()
        instance = YarnService.create_yarn(company_id, serializer.validated_data, request.user)
        return Response(YarnMasterSerializer(instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)
        company_id = self.get_company_id()
        updated = YarnService.update_yarn(instance.id, company_id, serializer.validated_data, request.user)
        return Response(YarnMasterSerializer(updated).data, status=status.HTTP_200_OK)


class FabricTypeViewSet(BaseMasterViewSet):
    required_module = ModulePermissions.MASTERS_FABRIC
    serializer_class = FabricTypeSerializer
    search_fields = ['name', 'code', 'description']
    filterset_fields = ['is_active']
    ordering_fields = ['name', 'code', 'created_on']

    def get_queryset(self):
        company_id = self.get_company_id()
        return FabricTypeRepository.get_for_company(company_id) if company_id else FabricTypeRepository.list_all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_id = self.get_company_id()
        instance = FabricTypeRepository.create(company_id=company_id, created_by=request.user, **serializer.validated_data)
        return Response(FabricTypeSerializer(instance).data, status=status.HTTP_201_CREATED)


class FabricMasterViewSet(BaseMasterViewSet):
    required_module = ModulePermissions.MASTERS_FABRIC
    serializer_class = FabricMasterSerializer
    search_fields = ['fabric_code', 'fabric_name', 'fabric_type__name', 'dia', 'gauge']
    filterset_fields = ['category', 'fabric_type', 'yarn', 'color_shade', 'is_active']
    ordering_fields = ['fabric_code', 'fabric_name', 'gsm', 'created_on']

    def get_queryset(self):
        company_id = self.get_company_id()
        return FabricRepository.get_for_company(company_id) if company_id else FabricRepository.list_all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_id = self.get_company_id()
        instance = FabricService.create_fabric(company_id, serializer.validated_data, request.user)
        return Response(FabricMasterSerializer(instance).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=kwargs.pop('partial', False))
        serializer.is_valid(raise_exception=True)
        company_id = self.get_company_id()
        updated = FabricService.update_fabric(instance.id, company_id, serializer.validated_data, request.user)
        return Response(FabricMasterSerializer(updated).data, status=status.HTTP_200_OK)


class ProcessMasterViewSet(BaseMasterViewSet):
    required_module = ModulePermissions.MASTERS_PROCESS
    serializer_class = ProcessMasterSerializer
    search_fields = ['process_code', 'process_name', 'description']
    filterset_fields = ['process_type', 'is_active']
    ordering_fields = ['process_name', 'process_code', 'created_on']

    def get_queryset(self):
        company_id = self.get_company_id()
        return ProcessRepository.get_for_company(company_id) if company_id else ProcessRepository.list_all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_id = self.get_company_id()
        instance = ProcessService.create_process(company_id, serializer.validated_data, request.user)
        return Response(ProcessMasterSerializer(instance).data, status=status.HTTP_201_CREATED)


class WarehouseMasterViewSet(BaseMasterViewSet):
    required_module = ModulePermissions.MASTERS_WAREHOUSE
    serializer_class = WarehouseMasterSerializer
    search_fields = ['warehouse_code', 'name', 'contact_person', 'phone']
    filterset_fields = ['warehouse_type', 'is_active']
    ordering_fields = ['name', 'warehouse_code', 'created_on']

    def get_queryset(self):
        company_id = self.get_company_id()
        return WarehouseRepository.get_for_company(company_id) if company_id else WarehouseRepository.list_all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        company_id = self.get_company_id()
        instance = WarehouseService.create_warehouse(company_id, serializer.validated_data, request.user)
        return Response(WarehouseMasterSerializer(instance).data, status=status.HTTP_201_CREATED)


class QualityProgramViewSet(ModelViewSet):
    queryset = quality_program_table.objects.all().order_by('-id')
    serializer_class = QualityProgramSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['quality', 'style', 'fabric_id']
    filterset_fields = ['is_active', 'status']
    ordering_fields = ['id', 'created_on', 'quality', 'style']


class SubQualityProgramViewSet(ModelViewSet):
    queryset = sub_quality_program_table.objects.all().order_by('position')
    serializer_class = SubQualityProgramSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tm', 'size_id', 'is_active', 'status']

