from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.constants import UserRoles, PartyTypes, WarehouseTypes, ProcessProgramStatus, ModulePermissions
from apps.authentication.models import Company, FinancialYear, Role, Privilege
from apps.masters.models import PartyMaster, WarehouseMaster, UnitOfMeasurement, YarnCountMaster, FabricTypeMaster, FabricMaster
from core.exceptions import ValidationError, ConflictError, ResourceNotFound
from apps.process.models import (
    parent_process_stage_table,
    parent_process_program_table,
    JobWorkMaster,
    JobWorkPartyConfiguration,
)
from apps.process.services import (
    ProcessStageService,
    ProcessProgramService,
    JobWorkService,
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


class JobWorkMasterAndLeadTimeTests(TestCase):
    def setUp(self):
        import datetime
        self.client = APIClient()

        # 1. Company & FY
        self.company = Company.objects.create(
            name="Tirupur Apparel Innovations Ltd",
            code="TAI-01",
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
            name="Planning Manager",
            code="PLAN_MGR",
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
            username="plan_head",
            email="plan@tai.com",
            password="password123",
            company=self.company,
            active_financial_year=self.fy,
            custom_role=self.role,
            role=UserRoles.COMPANY_USER,
        )
        self.client.force_authenticate(user=self.user)

        # 3. UOMs
        self.uom_kg = UnitOfMeasurement.objects.create(
            company=self.company,
            code="KGS",
            name="Kilograms",
        )
        self.uom_pcs = UnitOfMeasurement.objects.create(
            company=self.company,
            code="PCS",
            name="Pieces",
        )

        # 4. Process Stages
        ProcessStageService.seed_default_stages(self.company.id, self.user)
        self.stage_knit = parent_process_stage_table.objects.get(company=self.company, code="KNITTING")
        self.stage_dye = parent_process_stage_table.objects.get(company=self.company, code="DYEING")

        # 5. Job Worker Parties
        self.knitter = PartyMaster.objects.create(
            company=self.company,
            party_type=PartyTypes.KNITTING_UNIT,
            code="KNIT-ANN",
            name="Annai Knitting Mills",
            city="Tirupur",
        )
        self.dyer = PartyMaster.objects.create(
            company=self.company,
            party_type=PartyTypes.DYEING_UNIT,
            code="DYE-RNB",
            name="Rainbow Dyeing Unit",
            city="Tirupur",
        )

    def test_01_create_job_work_master_sequential_lead_time(self):
        """Test creating a valid JobWorkMaster with auto-calculated sequential lead time."""
        data = {
            "job_work_code": "JW-KNIT-SJ-24",
            "job_work_name": "Single Jersey 24GG Knitting Conversion",
            "process_stage_id": self.stage_knit.id,
            "job_work_category": "KNITTING",
            "material_type": "YARN",
            "uom_id": self.uom_kg.id,
            "min_order_qty": Decimal("100.000"),
            "max_order_qty": Decimal("1000.000"),
            "procurement_days": 2,
            "processing_days": 3,
            "quality_inspection_days": 1,
            "transportation_days": 1,
            "standard_rate": Decimal("18.0000"),
        }
        jw = JobWorkService.create_job_work(data, self.company.id, self.user.id)

        self.assertEqual(jw.job_work_code, "JW-KNIT-SJ-24")
        # Sequential lead time: 2 + 3 + 1 + 1 = 7 days
        self.assertEqual(jw.total_estimated_lead_time, 7)
        self.assertEqual(jw.standard_rate, Decimal("18.0000"))
        self.assertEqual(jw.record_status, "A")

    def test_02_duplicate_job_work_code_rejected(self):
        """Test that duplicate job work codes within the same company are rejected."""
        data = {
            "job_work_code": "JW-KNIT-TEST",
            "job_work_name": "Test Knitting",
            "process_stage_id": self.stage_knit.id,
            "job_work_category": "KNITTING",
            "material_type": "YARN",
            "uom_id": self.uom_kg.id,
        }
        JobWorkService.create_job_work(data.copy(), self.company.id, self.user.id)

        with self.assertRaises(ConflictError):
            JobWorkService.create_job_work(data.copy(), self.company.id, self.user.id)

    def test_03_moq_and_capacity_validation_rules(self):
        """Test MOQ > 0 and Max Order Qty >= MOQ rules."""
        base_data = {
            "job_work_code": "JW-VAL-1",
            "job_work_name": "Validation Test",
            "process_stage_id": self.stage_knit.id,
            "job_work_category": "KNITTING",
            "material_type": "YARN",
            "uom_id": self.uom_kg.id,
        }

        # 1. Zero MOQ rejected
        bad_moq = base_data.copy()
        bad_moq["min_order_qty"] = Decimal("0.000")
        with self.assertRaises(ValidationError):
            JobWorkService.create_job_work(bad_moq, self.company.id, self.user.id)

        # 2. Max < MOQ rejected
        bad_max = base_data.copy()
        bad_max["job_work_code"] = "JW-VAL-2"
        bad_max["min_order_qty"] = Decimal("500.000")
        bad_max["max_order_qty"] = Decimal("200.000")
        with self.assertRaises(ValidationError):
            JobWorkService.create_job_work(bad_max, self.company.id, self.user.id)

        # 3. Max == MOQ allowed
        good_equal = base_data.copy()
        good_equal["job_work_code"] = "JW-VAL-3"
        good_equal["min_order_qty"] = Decimal("500.000")
        good_equal["max_order_qty"] = Decimal("500.000")
        jw = JobWorkService.create_job_work(good_equal, self.company.id, self.user.id)
        self.assertEqual(jw.min_order_qty, jw.max_order_qty)

    def test_04_party_configuration_vendor_specific_lead_times(self):
        """Test binding a specific vendor with negotiated rates and turnaround times."""
        import datetime
        jw = JobWorkService.create_job_work(
            {
                "job_work_code": "JW-KNIT-VEND",
                "job_work_name": "Knitting with Vendor",
                "process_stage_id": self.stage_knit.id,
                "job_work_category": "KNITTING",
                "material_type": "YARN",
                "uom_id": self.uom_kg.id,
                "min_order_qty": Decimal("100.000"),
                "standard_rate": Decimal("18.0000"),
            },
            self.company.id,
            self.user.id
        )

        cfg_data = {
            "job_work_id": jw.id,
            "party_id": self.knitter.id,
            "uom_id": self.uom_kg.id,
            "min_order_qty": Decimal("300.000"),
            "max_order_qty": Decimal("3000.000"),
            "procurement_days": 2,
            "processing_days": 3,
            "quality_inspection_days": 1,
            "transportation_days": 1,
            "agreed_rate": Decimal("16.5000"),
            "small_lot_surcharge": Decimal("2.0000"),
            "effective_from": datetime.date(2026, 4, 1),
            "effective_to": datetime.date(2027, 3, 31),
        }
        cfg = JobWorkService.create_party_config(cfg_data, self.company.id, self.user.id)

        self.assertEqual(cfg.agreed_rate, Decimal("16.5000"))
        self.assertEqual(cfg.small_lot_surcharge, Decimal("2.0000"))
        self.assertEqual(cfg.total_estimated_lead_time, 7)

    def test_05_order_validation_below_moq_with_surcharge(self):
        """Test order validation when proposed quantity is below vendor MOQ."""
        import datetime
        jw = JobWorkService.create_job_work(
            {
                "job_work_code": "JW-DYE-MOQ",
                "job_work_name": "Dyeing MOQ Test",
                "process_stage_id": self.stage_dye.id,
                "job_work_category": "DYEING",
                "material_type": "GREY_FABRIC",
                "uom_id": self.uom_kg.id,
                "min_order_qty": Decimal("100.000"),
                "standard_rate": Decimal("35.0000"),
            },
            self.company.id,
            self.user.id
        )

        JobWorkService.create_party_config(
            {
                "job_work_id": jw.id,
                "party_id": self.dyer.id,
                "uom_id": self.uom_kg.id,
                "min_order_qty": Decimal("200.000"),
                "max_order_qty": Decimal("2000.000"),
                "agreed_rate": Decimal("32.0000"),
                "small_lot_surcharge": Decimal("5.0000"),
                "effective_from": datetime.date(2026, 4, 1),
                "effective_to": datetime.date(2027, 3, 31),
            },
            self.company.id,
            self.user.id
        )

        # Propose 150 kg (< 200 kg vendor MOQ)
        val = JobWorkService.validate_job_work_order(
            company_id=self.company.id,
            job_work_id=jw.id,
            quantity=Decimal("150.000"),
            party_id=self.dyer.id,
        )

        self.assertTrue(val["is_below_moq"])
        self.assertFalse(val["is_capacity_exceeded"])
        # Base: 32.0000 + Surcharge: 5.0000 = 37.0000
        self.assertEqual(Decimal(val["effective_unit_rate"]), Decimal("37.0000"))
        self.assertIn("Small lot surcharge", val["warning_message"])

    def test_06_order_validation_exceeding_capacity(self):
        """Test order validation when proposed quantity exceeds vendor maximum capacity."""
        import datetime
        jw = JobWorkService.create_job_work(
            {
                "job_work_code": "JW-CAP-TEST",
                "job_work_name": "Capacity Test",
                "process_stage_id": self.stage_knit.id,
                "job_work_category": "KNITTING",
                "material_type": "YARN",
                "uom_id": self.uom_kg.id,
                "min_order_qty": Decimal("100.000"),
                "max_order_qty": Decimal("1000.000"),
            },
            self.company.id,
            self.user.id
        )

        val = JobWorkService.validate_job_work_order(
            company_id=self.company.id,
            job_work_id=jw.id,
            quantity=Decimal("1500.000"),
        )
        self.assertFalse(val["is_valid"])
        self.assertTrue(val["is_capacity_exceeded"])
        self.assertIn("exceeds maximum batch capacity", val["warning_message"])

    def test_07_milestone_schedule_calculation_sequential_and_fast_track(self):
        """Test computing sequential vs fast-track overlapping milestone delivery dates."""
        import datetime
        jw = JobWorkService.create_job_work(
            {
                "job_work_code": "JW-LEAD-SCHED",
                "job_work_name": "Schedule Lead Time Test",
                "process_stage_id": self.stage_dye.id,
                "job_work_category": "DYEING",
                "material_type": "GREY_FABRIC",
                "uom_id": self.uom_kg.id,
                "procurement_days": 2,
                "processing_days": 4,
                "quality_inspection_days": 1,
                "transportation_days": 1,
            },
            self.company.id,
            self.user.id
        )

        # 1. Sequential: 2 + 4 + 1 + 1 = 8 days
        sched_seq = JobWorkService.calculate_schedule(
            company_id=self.company.id,
            job_work_id=jw.id,
            order_date="2026-05-01",
            is_fast_track=False,
        )
        self.assertEqual(sched_seq["total_lead_time_days"], 8)
        self.assertEqual(sched_seq["schedule_milestones"]["target_delivery_date"], "2026-05-09")

        # 2. Fast-Track: QC overlaps with final day -> 2 + 4 + 0 + 1 = 7 days
        sched_ft = JobWorkService.calculate_schedule(
            company_id=self.company.id,
            job_work_id=jw.id,
            order_date="2026-05-01",
            is_fast_track=True,
        )
        self.assertEqual(sched_ft["total_lead_time_days"], 7)
        self.assertEqual(sched_ft["schedule_milestones"]["target_delivery_date"], "2026-05-08")

    def test_08_soft_delete_job_work_and_cascade_configs(self):
        """Test soft deletion marks record_status='D' on master and cascades to vendor configs."""
        import datetime
        jw = JobWorkService.create_job_work(
            {
                "job_work_code": "JW-DEL-TEST",
                "job_work_name": "Deletion Test",
                "process_stage_id": self.stage_knit.id,
                "job_work_category": "KNITTING",
                "material_type": "YARN",
                "uom_id": self.uom_kg.id,
            },
            self.company.id,
            self.user.id
        )
        cfg = JobWorkService.create_party_config(
            {
                "job_work_id": jw.id,
                "party_id": self.knitter.id,
                "uom_id": self.uom_kg.id,
                "effective_from": datetime.date(2026, 4, 1),
                "effective_to": datetime.date(2027, 3, 31),
            },
            self.company.id,
            self.user.id
        )

        JobWorkService.delete_job_work(jw.id, self.company.id, self.user.id)

        jw.refresh_from_db()
        cfg.refresh_from_db()
        self.assertEqual(jw.record_status, "D")
        self.assertEqual(cfg.record_status, "D")

    def test_09_api_endpoints_and_seed_defaults(self):
        """Test REST API endpoints for job works, schedule calculation, and seed defaults."""
        # 1. Seed default job works via API
        seed_resp = self.client.post("/api/v1/process/job-works/seed-defaults/")
        self.assertEqual(seed_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(seed_resp.data["data"]) >= 2)

        # 2. List job works via API
        list_resp = self.client.get("/api/v1/process/job-works/")
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        results = list_resp.data.get("results") or list_resp.data.get("data") or list_resp.data
        self.assertTrue(len(results) >= 2)

        first_jw = results[0]
        jw_id = first_jw["id"]

        # 3. Validate order via API action
        val_resp = self.client.post(
            "/api/v1/process/job-works/validate-order/",
            data={
                "job_work_id": jw_id,
                "quantity": "500.000",
            },
            format="json",
        )
        self.assertEqual(val_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(val_resp.data["data"]["is_valid"])

        # 4. Calculate schedule via API action with DMY date
        sched_resp = self.client.post(
            "/api/v1/process/job-works/calculate-schedule/",
            data={
                "job_work_id": jw_id,
                "order_date": "10/05/2026",
                "is_fast_track": False,
            },
            format="json",
        )
        self.assertEqual(sched_resp.status_code, status.HTTP_200_OK)
        self.assertIn("target_delivery_date", sched_resp.data["data"]["schedule_milestones"])
