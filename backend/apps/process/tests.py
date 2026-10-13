from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.constants import UserRoles, PartyTypes, WarehouseTypes, ProcessProgramStatus, ModulePermissions
from apps.authentication.models import Company, FinancialYear, Role, Privilege
from apps.masters.models import PartyMaster, WarehouseMaster, UnitOfMeasurement, YarnCountMaster, FabricTypeMaster, FabricMaster
from apps.process.models import (
    parent_process_stage_table,
    parent_process_program_table,
)
from apps.process.services import (
    ProcessStageService,
    ProcessProgramService,
)

User = get_user_model()


class ProcessProgramWorkflowTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Company & FY Setup
        self.company = Company.objects.create(
            name="Sri Krishna Knits Pvt Ltd",
            code="SKK-01",
            city="Tirupur",
            state="Tamil Nadu",
        )
        self.fy = FinancialYear.objects.create(
            company=self.company,
            name="FY 2026-2027",
            code="FY2627",
            start_date="2026-04-01",
            end_date="2027-03-31",
            is_current=True,
        )

        # 2. Roles & User Setup
        self.role = Role.objects.create(
            company=self.company,
            name="Production Manager",
            code="PROD_MGR",
        )
        for mod in [
            ModulePermissions.PROCESS_STAGE,
            ModulePermissions.PROCESS_PROGRAM,
        ]:
            Privilege.objects.create(
                role=self.role,
                module=mod,
                can_create=True,
                can_read=True,
                can_update=True,
                can_delete=True,
                can_approve=True,
            )

        self.user = User.objects.create_user(
            username="prod_supervisor",
            email="prod@skk.com",
            password="password123",
            company=self.company,
            active_financial_year=self.fy,
            custom_role=self.role,
            role=UserRoles.COMPANY_USER,
        )
        self.client.force_authenticate(user=self.user)

        # 3. Seed Default Process Stages
        stages = ProcessStageService.seed_default_stages(self.company.id, self.user)
        self.stage_knit = parent_process_stage_table.objects.get(company=self.company, code="KNITTING")
        self.stage_dye = parent_process_stage_table.objects.get(company=self.company, code="DYEING")
        self.stage_cut = parent_process_stage_table.objects.get(company=self.company, code="CUTTING")

        # 4. Master Data
        self.knitter = PartyMaster.objects.create(
            company=self.company,
            party_type=PartyTypes.KNITTING_UNIT,
            code="KNIT-001",
            name="Annai Knitting Mills",
            city="Tirupur",
        )
        self.dyer = PartyMaster.objects.create(
            company=self.company,
            party_type=PartyTypes.DYEING_UNIT,
            code="DYE-001",
            name="Rainbow Dyeing Mills",
            city="Tirupur",
        )
        self.cutter = PartyMaster.objects.create(
            company=self.company,
            party_type=PartyTypes.JOB_WORKER,
            code="CUT-001",
            name="Apex Cutting Floor",
            city="Tirupur",
        )

        self.wh_yarn = WarehouseMaster.objects.create(
            company=self.company,
            warehouse_code="WH-YARN-01",
            name="Main Yarn Godown",
            warehouse_type=WarehouseTypes.YARN_GODOWN,
        )
        self.wh_grey = WarehouseMaster.objects.create(
            company=self.company,
            warehouse_code="WH-GREY-01",
            name="Grey Fabric Godown",
            warehouse_type=WarehouseTypes.GREY_FABRIC_GODOWN,
        )
        self.wh_dyed = WarehouseMaster.objects.create(
            company=self.company,
            warehouse_code="WH-DYED-01",
            name="Dyed Fabric Godown",
            warehouse_type=WarehouseTypes.DYED_FABRIC_GODOWN,
        )

    def test_01_knitting_process_program(self):
        """Test creating a Knitting Process Program (Input Yarn -> Output Grey Fabric)."""
        data = {
            "program_date": "2026-05-10",
            "process_stage_id": self.stage_knit.id,
            "job_worker_id": self.knitter.id,
            "source_warehouse_id": self.wh_yarn.id,
            "dest_warehouse_id": self.wh_grey.id,
            "input_from": "YARN",
            "input_item": "30s Combed Cotton Yarn",
            "input_type": "BAG_WT_KG",
            "input_units": 20,
            "input_quantity": Decimal("1000.000"),
            "output_to": "GREY_FABRIC",
            "output_item": "30s Cotton Single Jersey Grey Fabric",
            "output_type": "ROLL_WT_KG",
            "planned_loss_percent": Decimal("2.00"),
            "dia": "24",
            "gsm": 160,
            "gauge": "24GG",
            "rate": Decimal("18.00"),
            "input_lines": [
                {
                    "item_name": "30s Combed Cotton 100%",
                    "blend_ratio_percent": "100.00",
                    "units": 20,
                    "quantity": "1000.000",
                }
            ],
        }
        program = ProcessProgramService.create_program(
            company_id=self.company.id,
            fy_id=self.fy.id,
            data=data,
            user=self.user,
        )

        self.assertTrue(program.program_number.startswith("PRG-KNIT-"))
        # 1000 Kg with 2% loss -> 980.000 Kg expected output
        self.assertEqual(program.expected_output_qty, Decimal("980.000"))
        # Amount: 1000 Kg * 18.00 = 18000.000
        self.assertEqual(program.amount, Decimal("18000.000"))
        self.assertEqual(program.status, ProcessProgramStatus.DRAFT)

        # Authorize Program
        auth_prog = ProcessProgramService.authorize_program(program.id, self.company.id, self.user)
        self.assertEqual(auth_prog.status, ProcessProgramStatus.AUTHORIZED)

    def test_02_dyeing_process_program_with_recipes_and_shrinkage(self):
        """Test creating a Dyeing Process Program (Input Grey Fabric -> Output Dyed Fabric with recipe)."""
        data = {
            "program_date": "2026-05-15",
            "process_stage_id": self.stage_dye.id,
            "job_worker_id": self.dyer.id,
            "source_warehouse_id": self.wh_grey.id,
            "dest_warehouse_id": self.wh_dyed.id,
            "input_from": "GREY_FABRIC",
            "input_item": "30s Cotton Single Jersey Grey Fabric",
            "input_type": "ROLL_WT_KG",
            "input_units": 40,
            "input_quantity": Decimal("800.000"),
            "output_to": "DYED_FABRIC",
            "output_item": "Navy Blue Dyed Single Jersey",
            "output_type": "ROLL_WT_KG",
            "planned_loss_percent": Decimal("5.00"),
            "length_shrinkage_percent": Decimal("4.00"),
            "width_shrinkage_percent": Decimal("4.00"),
            "lab_dip_no": "LD-2026-099",
            "light_source": "D65",
            "rate": Decimal("35.00"),
            "recipe_lines": [
                {
                    "item_type": "DYESTUFF",
                    "item_name": "Reactive Navy Blue RGB",
                    "dosage_unit": "PERCENTAGE",
                    "dosage_value": "2.8500",
                    "process_step": "DYEING",
                },
                {
                    "item_type": "CHEMICAL",
                    "item_name": "Glauber Salt",
                    "dosage_unit": "GPL",
                    "dosage_value": "50.0000",
                    "process_step": "DYEING",
                },
            ],
        }
        program = ProcessProgramService.create_program(
            company_id=self.company.id,
            fy_id=self.fy.id,
            data=data,
            user=self.user,
        )

        self.assertTrue(program.program_number.startswith("PRG-DYE-"))
        # 800 Kg with 5% loss -> 760.000 Kg expected output
        self.assertEqual(program.expected_output_qty, Decimal("760.000"))
        # Amount: 800 Kg * 35.00 = 28000.000
        self.assertEqual(program.amount, Decimal("28000.000"))
        self.assertEqual(program.recipe_lines.count(), 2)

    def test_03_cutting_process_program(self):
        """Test creating a Cutting Process Program (Input Dyed Fabric -> Output Cut Panels)."""
        data = {
            "program_date": "2026-05-20",
            "process_stage_id": self.stage_cut.id,
            "job_worker_id": self.cutter.id,
            "source_warehouse_id": self.wh_dyed.id,
            "dest_warehouse_id": self.wh_dyed.id,
            "input_from": "DYED_FABRIC",
            "input_item": "Navy Blue Dyed Single Jersey",
            "input_type": "ROLL_WT_KG",
            "input_units": 10,
            "input_quantity": Decimal("200.000"),
            "output_to": "CUT_PANELS",
            "output_item": "Crew Neck T-Shirt Cut Panels",
            "output_type": "PIECES",
            "planned_loss_percent": Decimal("3.00"),
            "rate": Decimal("5.00"),
        }
        program = ProcessProgramService.create_program(
            company_id=self.company.id,
            fy_id=self.fy.id,
            data=data,
            user=self.user,
        )

        self.assertTrue(program.program_number.startswith("PRG-CUTT-") or program.program_number.startswith("PRG-CUT-"))
        self.assertEqual(program.expected_output_qty, Decimal("194.000"))

    def test_04_api_integration_and_date_dmy_format(self):
        """Test Process Stage and Process Program API endpoints with DMY date formatting."""
        # 1. List stages
        resp = self.client.get("/api/v1/process/stages/")
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        stages_data = resp.data.get("results") or resp.data.get("data") or resp.data
        self.assertTrue(len(stages_data) >= 3)

        # 2. Create Program via API with DMY date input
        create_resp = self.client.post(
            "/api/v1/process/programs/",
            data={
                "program_date": "25/06/2026",
                "process_stage": self.stage_knit.id,
                "job_worker": self.knitter.id,
                "source_warehouse": self.wh_yarn.id,
                "dest_warehouse": self.wh_grey.id,
                "input_item": "34s Combed Yarn",
                "input_quantity": "500.000",
                "output_item": "Single Jersey 34s Grey",
                "rate": "20.00",
            },
            format="json",
        )
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        # Verify date is formatted as DMY in the response
        self.assertEqual(create_resp.data["data"]["program_date"], "25/06/2026")
