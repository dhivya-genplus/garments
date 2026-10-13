from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from core.constants import (
    UserRoles,
    PartyTypes,
    WarehouseTypes,
    KnittingProgramStatus,
    GreyFabricOutwardTypes,
    GreyFabricInwardSources,
    ModulePermissions,
)
from core.exceptions import ValidationError
from apps.authentication.models import Company, FinancialYear, Role, Privilege
from apps.masters.models import (
    PartyMaster,
    WarehouseMaster,
    UnitOfMeasurement,
    YarnCountMaster,
    FabricTypeMaster,
    FabricMaster,
)
from apps.knitting.models import (
    parent_knitting_program_table,
    grey_fabric_stock_table,
    parent_grey_fabric_inward_table,
    parent_grey_fabric_outward_table,
    parent_grey_fabric_sales_table,
    parent_grey_fabric_sales_return_table,
)
from apps.knitting.services import (
    KnittingProgramService,
    GreyFabricStockService,
    GreyFabricInwardService,
    GreyFabricOutwardService,
    GreyFabricSalesService,
    GreyFabricSalesReturnService,
)

User = get_user_model()


class KnittingWorkflowTests(TestCase):
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
            name="Knitting Manager",
            code="KNIT_MGR",
        )
        for mod in [
            ModulePermissions.KNITTING_PROGRAM,
            ModulePermissions.KNITTING_GREY_FABRIC_STOCK,
            ModulePermissions.KNITTING_GREY_FABRIC_INWARD,
            ModulePermissions.KNITTING_GREY_FABRIC_OUTWARD,
            ModulePermissions.KNITTING_GREY_PO,
            ModulePermissions.KNITTING_GREY_FABRIC_SALES,
            ModulePermissions.KNITTING_GREY_FABRIC_SALES_RETURN,
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
            username="knitting_supervisor",
            email="knitting@skk.com",
            password="password123",
            company=self.company,
            active_financial_year=self.fy,
            custom_role=self.role,
            role=UserRoles.COMPANY_USER,
        )
        self.client.force_authenticate(user=self.user)

        # 3. Masters Setup
        self.knitter = PartyMaster.objects.create(
            company=self.company,
            party_type=PartyTypes.KNITTING_UNIT,
            code="KNIT-001",
            name="Sri Amman Knitting Mills",
            city="Tirupur",
        )
        self.dyeing_unit = PartyMaster.objects.create(
            company=self.company,
            party_type=PartyTypes.DYEING_UNIT,
            code="DYE-001",
            name="Rainbow Processing Unit",
            city="Tirupur",
        )
        self.customer = PartyMaster.objects.create(
            company=self.company,
            party_type=PartyTypes.CUSTOMER,
            code="CUST-001",
            name="Classic Garments Exports",
            city="Tirupur",
        )
        self.warehouse = WarehouseMaster.objects.create(
            company=self.company,
            warehouse_code="WH-GREY-01",
            name="Main Grey Fabric Godown",
            warehouse_type=WarehouseTypes.GREY_FABRIC_GODOWN,
        )
        self.uom = UnitOfMeasurement.objects.create(
            company=self.company,
            code="KGS",
            name="Kilograms",
        )
        self.yarn_count = YarnCountMaster.objects.create(
            company=self.company,
            count="30s Combed",
        )
        self.fabric_type = FabricTypeMaster.objects.create(
            company=self.company,
            name="Single Jersey",
            code="SJ-01",
        )
        self.fabric = FabricMaster.objects.create(
            company=self.company,
            fabric_code="FAB-SJ-30S",
            fabric_name="30s Cotton Single Jersey Grey",
            fabric_type=self.fabric_type,
            gsm=160,
            dia="24",
            gauge="24GG",
            uom=self.uom,
        )

    def test_01_knitting_program_creation_and_requirement_calculation(self):
        """Test creating knitting program computes yarn requirement including loss %."""
        data = {
            "program_date": "2026-05-10",
            "knitter_id": self.knitter.id,
            "warehouse_id": self.warehouse.id,
            "fabric_id": self.fabric.id,
            "fabric_type_id": self.fabric_type.id,
            "dia": "24",
            "gauge": "24GG",
            "gsm": 160,
            "loop_length": "2.70",
            "planned_rolls": 50,
            "planned_fabric_quantity": Decimal("1000.000"),
            "expected_loss_percent": Decimal("2.00"),
            "knitting_rate": Decimal("18.00"),
            "yarn_lines": [
                {
                    "yarn_count_id": self.yarn_count.id,
                    "yarn_type": "GREY",
                    "blend_ratio_percent": "100.00",
                    "planned_quantity": "1020.000",
                }
            ],
        }
        program = KnittingProgramService.create_program(
            company_id=self.company.id,
            fy_id=self.fy.id,
            data=data,
            user=self.user,
        )

        self.assertEqual(program.status, KnittingProgramStatus.DRAFT)
        self.assertTrue(program.program_number.startswith("KP-"))
        # 1000 Kg * (1 + 0.02) = 1020.000 Kg
        self.assertEqual(program.total_yarn_required, Decimal("1020.000"))
        # 1000 Kg * 18.00 = 18000.000
        self.assertEqual(program.total_knitting_amount, Decimal("18000.000"))
        self.assertEqual(program.yarn_lines.count(), 1)

        # Authorize program
        auth_prog = KnittingProgramService.authorize_program(program.id, self.company.id, self.user)
        self.assertEqual(auth_prog.status, KnittingProgramStatus.AUTHORIZED)

        # Check summary
        summary = KnittingProgramService.get_program_summary(program.id, self.company.id)
        self.assertEqual(summary["status"], "Authorized / Released")
        self.assertEqual(summary["pending_fabric_quantity"], "1000.000")

    def test_02_grey_fabric_stock_service_concurrency_and_safeguards(self):
        """Test Grey Fabric stock addition, deduction, and non-negative safeguard."""
        # 1. Add Stock
        stock = GreyFabricStockService.add_inward_stock(
            company_id=self.company.id,
            warehouse_id=self.warehouse.id,
            fabric_id=self.fabric.id,
            fabric_type_id=self.fabric_type.id,
            dia="24",
            gsm=160,
            gauge="24GG",
            lot_no="LOT-001",
            rolls=20,
            quantity=Decimal("400.000"),
        )
        self.assertEqual(stock.balance_rolls, 20)
        self.assertEqual(stock.balance_quantity, Decimal("400.000"))

        # 2. Deduct Partial Stock
        stock = GreyFabricStockService.deduct_outward_stock(
            company_id=self.company.id,
            warehouse_id=self.warehouse.id,
            fabric_id=self.fabric.id,
            fabric_type_id=self.fabric_type.id,
            dia="24",
            gsm=160,
            gauge="24GG",
            lot_no="LOT-001",
            rolls=10,
            quantity=Decimal("200.000"),
        )
        self.assertEqual(stock.balance_rolls, 10)
        self.assertEqual(stock.balance_quantity, Decimal("200.000"))

        # 3. Deduct More Than Available (Should Raise ValidationError)
        with self.assertRaises(ValidationError):
            GreyFabricStockService.deduct_outward_stock(
                company_id=self.company.id,
                warehouse_id=self.warehouse.id,
                fabric_id=self.fabric.id,
                fabric_type_id=self.fabric_type.id,
                dia="24",
                gsm=160,
                gauge="24GG",
                lot_no="LOT-001",
                rolls=15,
                quantity=Decimal("300.000"),
            )

    def test_03_grey_fabric_inward_and_atomic_cancellation(self):
        """Test inward receipt crediting stock and updating program, and atomic rollback on delete."""
        # Create Knitting Program
        program = KnittingProgramService.create_program(
            company_id=self.company.id,
            fy_id=self.fy.id,
            data={
                "program_date": "2026-05-12",
                "knitter_id": self.knitter.id,
                "warehouse_id": self.warehouse.id,
                "fabric_id": self.fabric.id,
                "fabric_type_id": self.fabric_type.id,
                "dia": "24",
                "gsm": 160,
                "planned_fabric_quantity": Decimal("500.000"),
                "expected_loss_percent": Decimal("2.00"),
            },
            user=self.user,
        )
        KnittingProgramService.authorize_program(program.id, self.company.id, self.user)

        # Post Inward
        inward_data = {
            "inward_date": "2026-05-15",
            "dc_number": "DC-KNT-9988",
            "dc_date": "2026-05-15",
            "knitting_program_id": program.id,
            "party_id": self.knitter.id,
            "warehouse_id": self.warehouse.id,
            "fabric_id": self.fabric.id,
            "fabric_type_id": self.fabric_type.id,
            "dia": "24",
            "gsm": 160,
            "gauge": "24GG",
            "lot_no": "LOT-KNT-01",
            "yarn_consumed_wt": Decimal("510.000"),
            "net_wt": Decimal("500.000"),
            "knitting_rate": Decimal("20.00"),
            "line_items": [
                {"roll_no": "R-01", "gross_wt": "26.000", "tare_wt": "1.000", "net_wt": "25.000"},
                {"roll_no": "R-02", "gross_wt": "26.000", "tare_wt": "1.000", "net_wt": "25.000"},
            ],
        }
        inward = GreyFabricInwardService.post_inward(
            company_id=self.company.id,
            fy_id=self.fy.id,
            data=inward_data,
            user=self.user,
        )

        # Verify stock credited
        stock = grey_fabric_stock_table.objects.get(
            company=self.company,
            warehouse=self.warehouse,
            fabric=self.fabric,
            dia="24",
            gsm=160,
            lot_no="LOT-KNT-01",
        )
        self.assertEqual(stock.balance_quantity, Decimal("500.000"))

        # Verify program updated
        program.refresh_from_db()
        self.assertEqual(program.received_fabric_quantity, Decimal("500.000"))
        self.assertEqual(program.status, KnittingProgramStatus.COMPLETED)

        # Cancel Inward -> Should rollback stock and restore program
        GreyFabricInwardService.cancel_inward(inward.id, self.company.id, self.user)

        stock.refresh_from_db()
        self.assertEqual(stock.balance_quantity, Decimal("0.000"))

        program.refresh_from_db()
        self.assertEqual(program.received_fabric_quantity, Decimal("0.000"))
        self.assertEqual(program.status, KnittingProgramStatus.AUTHORIZED)

    def test_04_grey_fabric_outward_flow(self):
        """Test dispatching grey fabric to dyeing unit deducts stock atomically."""
        # 1. Seed stock
        GreyFabricStockService.add_inward_stock(
            company_id=self.company.id,
            warehouse_id=self.warehouse.id,
            fabric_id=self.fabric.id,
            fabric_type_id=self.fabric_type.id,
            dia="24",
            gsm=160,
            gauge="24GG",
            lot_no="LOT-DYE-01",
            rolls=10,
            quantity=Decimal("250.000"),
        )

        # 2. Post Outward
        outward_data = {
            "outward_date": "2026-05-18",
            "outward_type": GreyFabricOutwardTypes.DYEING,
            "warehouse_id": self.warehouse.id,
            "destination_party_id": self.dyeing_unit.id,
            "fabric_id": self.fabric.id,
            "fabric_type_id": self.fabric_type.id,
            "dia": "24",
            "gsm": 160,
            "gauge": "24GG",
            "lot_no": "LOT-DYE-01",
            "rolls": 4,
            "quantity": Decimal("100.000"),
            "line_items": [
                {"roll_no": "R-1", "gross_wt": "25.000", "net_wt": "25.000"},
                {"roll_no": "R-2", "gross_wt": "25.000", "net_wt": "25.000"},
                {"roll_no": "R-3", "gross_wt": "25.000", "net_wt": "25.000"},
                {"roll_no": "R-4", "gross_wt": "25.000", "net_wt": "25.000"},
            ],
        }
        outward = GreyFabricOutwardService.post_outward(
            company_id=self.company.id,
            fy_id=self.fy.id,
            data=outward_data,
            user=self.user,
        )

        stock = grey_fabric_stock_table.objects.get(
            company=self.company,
            warehouse=self.warehouse,
            fabric=self.fabric,
            dia="24",
            gsm=160,
            lot_no="LOT-DYE-01",
        )
        self.assertEqual(stock.balance_rolls, 6)
        self.assertEqual(stock.balance_quantity, Decimal("150.000"))

        # 3. Cancel Outward -> Restores stock
        GreyFabricOutwardService.cancel_outward(outward.id, self.company.id, self.user)
        stock.refresh_from_db()
        self.assertEqual(stock.balance_rolls, 10)
        self.assertEqual(stock.balance_quantity, Decimal("250.000"))

    def test_05_api_endpoints_integration(self):
        """Test DRF endpoints for Knitting Programs and Grey Fabric Stock."""
        # 1. Create Program via API
        response = self.client.post(
            "/api/v1/knitting/programs/",
            data={
                "program_date": "2026-06-01",
                "knitter": self.knitter.id,
                "warehouse": self.warehouse.id,
                "fabric": self.fabric.id,
                "fabric_type": self.fabric_type.id,
                "dia": "30",
                "gsm": 180,
                "planned_rolls": 10,
                "planned_fabric_quantity": "250.000",
                "expected_loss_percent": "2.50",
                "knitting_rate": "15.00",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        program_id = response.data["data"]["id"]

        # 2. Authorize Program via API action
        auth_resp = self.client.post(f"/api/v1/knitting/programs/{program_id}/authorize/")
        self.assertEqual(auth_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(auth_resp.data["data"]["status"], KnittingProgramStatus.AUTHORIZED)

        # 3. Get Stock Ledger via API
        stock_resp = self.client.get("/api/v1/knitting/stock/")
        self.assertEqual(stock_resp.status_code, status.HTTP_200_OK)

    def test_06_grey_fabric_sales_and_returns(self):
        """Test commercial sales invoice stock deduction and sales return credit."""
        # 1. Seed stock: 20 rolls, 500.000 Kg
        stock = GreyFabricStockService.add_inward_stock(
            company_id=self.company.id,
            warehouse_id=self.warehouse.id,
            fabric_id=self.fabric.id,
            fabric_type_id=self.fabric_type.id,
            dia="24",
            gsm=160,
            gauge="24GG",
            lot_no="LOT-SALES-01",
            rolls=20,
            quantity=Decimal("500.000"),
        )
        self.assertEqual(stock.balance_rolls, 20)
        self.assertEqual(stock.balance_quantity, Decimal("500.000"))

        # 2. Commercial Sales Invoice: 10 rolls, 250.000 Kg @ 220.00 / Kg
        sales_data = {
            "invoice_date": "2026-06-10",
            "customer_id": self.customer.id,
            "warehouse_id": self.warehouse.id,
            "fabric_id": self.fabric.id,
            "fabric_type_id": self.fabric_type.id,
            "dia": "24",
            "gsm": 160,
            "gauge": "24GG",
            "lot_no": "LOT-SALES-01",
            "rolls": 10,
            "quantity": Decimal("250.000"),
            "rate": Decimal("220.00"),
            "amount": Decimal("55000.00"),
            "line_items": [
                {"roll_no": f"R-{i}", "gross_wt": "25.000", "net_wt": "25.000", "rate": "220.00", "amount": "5500.00"}
                for i in range(1, 11)
            ],
        }
        sales = GreyFabricSalesService.create_sales_invoice(
            company_id=self.company.id,
            fy_id=self.fy.id,
            data=sales_data,
            user=self.user,
        )

        stock.refresh_from_db()
        self.assertEqual(stock.sales_rolls, 10)
        self.assertEqual(stock.sales_quantity, Decimal("250.000"))
        self.assertEqual(stock.balance_rolls, 10)
        self.assertEqual(stock.balance_quantity, Decimal("250.000"))

        # 3. Customer Sales Return: 2 rolls, 50.000 Kg
        return_data = {
            "return_date": "2026-06-12",
            "sales_invoice_id": sales.id,
            "customer_id": self.customer.id,
            "warehouse_id": self.warehouse.id,
            "fabric_id": self.fabric.id,
            "fabric_type_id": self.fabric_type.id,
            "dia": "24",
            "gsm": 160,
            "gauge": "24GG",
            "lot_no": "LOT-SALES-01",
            "rolls": 2,
            "quantity": Decimal("50.000"),
            "rate": Decimal("220.00"),
            "amount": Decimal("11000.00"),
            "reason": "Quality rejection - minor hole marks",
            "line_items": [
                {"roll_no": "R-1", "gross_wt": "25.000", "net_wt": "25.000", "rate": "220.00", "amount": "5500.00"},
                {"roll_no": "R-2", "gross_wt": "25.000", "net_wt": "25.000", "rate": "220.00", "amount": "5500.00"},
            ],
        }
        sales_return = GreyFabricSalesReturnService.create_sales_return(
            company_id=self.company.id,
            fy_id=self.fy.id,
            data=return_data,
            user=self.user,
        )

        stock.refresh_from_db()
        self.assertEqual(stock.sales_return_rolls, 2)
        self.assertEqual(stock.sales_return_quantity, Decimal("50.000"))
        # Balance becomes 10 - 0 + 2 = 12 rolls, 250 + 50 = 300.000 Kg
        self.assertEqual(stock.balance_rolls, 12)
        self.assertEqual(stock.balance_quantity, Decimal("300.000"))

        # 4. Cancel Sales Return -> Stock restored back to post-sale state (10 rolls, 250.000 Kg)
        GreyFabricSalesReturnService.cancel_sales_return(sales_return.id, self.company.id, self.user)
        stock.refresh_from_db()
        self.assertEqual(stock.sales_return_rolls, 0)
        self.assertEqual(stock.sales_return_quantity, Decimal("0.000"))
        self.assertEqual(stock.balance_rolls, 10)
        self.assertEqual(stock.balance_quantity, Decimal("250.000"))

        # 5. Cancel Sales Invoice -> Full stock restored (20 rolls, 500.000 Kg)
        GreyFabricSalesService.cancel_sales_invoice(sales.id, self.company.id, self.user)
        stock.refresh_from_db()
        self.assertEqual(stock.sales_rolls, 0)
        self.assertEqual(stock.sales_quantity, Decimal("0.000"))
        self.assertEqual(stock.balance_rolls, 20)
        self.assertEqual(stock.balance_quantity, Decimal("500.000"))

        # 6. Verify DRF API endpoints
        resp_sales = self.client.get("/api/v1/knitting/sales/")
        self.assertEqual(resp_sales.status_code, status.HTTP_200_OK)

        resp_returns = self.client.get("/api/v1/knitting/sales-returns/")
        self.assertEqual(resp_returns.status_code, status.HTTP_200_OK)

