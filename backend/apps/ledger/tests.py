from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from apps.authentication.models import User, Company, FinancialYear, Role, Privilege
from apps.masters.models import WarehouseMaster, PartyMaster
from apps.ledger.models import tl_stock_movement, tm_stage_stock, tl_voucher, tl_voucher_line
from apps.ledger.services import StockLedgerService, CurrencyLedgerService
from core.constants import UserRoles, StockMovementTypes, VoucherTypes, ModulePermissions, PartyTypes, WarehouseTypes
from core.exceptions import ValidationError, ConflictError


class LedgerEngineTestCase(TestCase):
    def setUp(self):
        # 1. Company & FY Setup
        self.company = Company.objects.create(
            name="Tex Garments Mills Ltd",
            code="TEX01",
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

        # 2. Roles & Privileges
        self.role = Role.objects.create(
            company=self.company,
            name="Ledger Accountant",
            code="LEDGER_ACC",
        )
        for mod in [ModulePermissions.LEDGER_STOCK, ModulePermissions.LEDGER_CURRENCY]:
            Privilege.objects.create(
                role=self.role,
                module=mod,
                can_create=True,
                can_read=True,
                can_update=True,
                can_delete=True,
                can_approve=True,
            )

        # 3. User
        self.user = User.objects.create_user(
            username="accountant",
            email="accountant@texgarments.com",
            password="testpassword123",
            company=self.company,
            active_financial_year=self.fy,
            custom_role=self.role,
            role=UserRoles.COMPANY_USER,
        )

        # 4. Master fixtures
        self.warehouse = WarehouseMaster.objects.create(
            company=self.company,
            name="Main Spinning Warehouse",
            warehouse_code="WH-SPIN-01",
            warehouse_type=WarehouseTypes.YARN_GODOWN,
        )
        self.knitter = PartyMaster.objects.create(
            company=self.company,
            name="Sri Murugan Knitting Works",
            code="KNT-001",
            party_type=PartyTypes.KNITTING_UNIT,
        )

        # 5. Client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_stock_inward_outward_and_balance(self):
        # Step 1: Inward 50 Bags (2500.000 Kg) of 30s Cotton Combed Yarn
        inward = StockLedgerService.record_movement(
            company_id=self.company.id,
            fy_id=self.fy.id,
            movement_date="05/10/2026",
            stage="YARN",
            warehouse_id=self.warehouse.id,
            movement_type=StockMovementTypes.INWARD,
            doc_type="INWARD_GRN",
            doc_number="YRN-GRN-001",
            item_name="30s Combed Cotton Yarn",
            lot_or_batch_no="LOT-A101",
            in_units=50,
            in_qty=Decimal("2500.000"),
            unit_rate=Decimal("280.00"),
            user=self.user,
        )
        self.assertEqual(inward.balance_units, 50)
        self.assertEqual(inward.balance_qty, Decimal("2500.000"))
        self.assertEqual(inward.total_value, Decimal("700000.00"))

        # Check live snapshot
        live_stock = tm_stage_stock.objects.get(
            company=self.company,
            warehouse=self.warehouse,
            stage="YARN",
            lot_or_batch_no="LOT-A101"
        )
        self.assertEqual(live_stock.balance_units, 50)
        self.assertEqual(live_stock.balance_qty, Decimal("2500.000"))

        # Step 2: Issue 20 Bags (1000.000 Kg) outward to Knitting
        outward = StockLedgerService.record_movement(
            company_id=self.company.id,
            fy_id=self.fy.id,
            movement_date="05/10/2026",
            stage="YARN",
            warehouse_id=self.warehouse.id,
            movement_type=StockMovementTypes.OUTWARD,
            doc_type="OUTWARD_DC",
            doc_number="YRN-DC-001",
            item_name="30s Combed Cotton Yarn",
            lot_or_batch_no="LOT-A101",
            out_units=20,
            out_qty=Decimal("1000.000"),
            unit_rate=Decimal("280.00"),
            party_id=self.knitter.id,
            user=self.user,
        )
        self.assertEqual(outward.balance_units, 30)
        self.assertEqual(outward.balance_qty, Decimal("1500.000"))
        self.assertEqual(outward.total_value, Decimal("420000.00"))

        # Check live snapshot updated
        live_stock.refresh_from_db()
        self.assertEqual(live_stock.balance_units, 30)
        self.assertEqual(live_stock.balance_qty, Decimal("1500.000"))

    def test_insufficient_stock_prevents_outward_underflow(self):
        # Attempt to issue 100 Kg when balance is 0
        with self.assertRaises(ValidationError) as ctx:
            StockLedgerService.record_movement(
                company_id=self.company.id,
                fy_id=self.fy.id,
                movement_date="05/10/2026",
                stage="YARN",
                warehouse_id=self.warehouse.id,
                movement_type=StockMovementTypes.OUTWARD,
                doc_type="OUTWARD_DC",
                doc_number="YRN-DC-ERR",
                item_name="40s Modal Yarn",
                lot_or_batch_no="LOT-ZERO",
                out_units=5,
                out_qty=Decimal("100.000"),
                user=self.user,
            )
        self.assertIn("Insufficient stock", str(ctx.exception))

    def test_currency_voucher_posting_and_balance_invariant(self):
        # 1. Balanced Voucher (Debit == Credit)
        lines = [
            {"account_code": "5001", "account_name": "Knitting Jobwork Expense", "debit": Decimal("18000.00"), "credit": Decimal("0.00")},
            {"account_code": "2001", "account_name": "Sundry Creditors (Knitter)", "party_id": self.knitter.id, "debit": Decimal("0.00"), "credit": Decimal("18000.00")},
        ]
        voucher = CurrencyLedgerService.post_voucher(
            company_id=self.company.id,
            fy_id=self.fy.id,
            voucher_date="05/10/2026",
            voucher_type=VoucherTypes.JOURNAL,
            stage="KNITTING",
            lines=lines,
            party_id=self.knitter.id,
            narration="Knitting charges for Job Order #KO-001",
            user=self.user,
        )
        self.assertTrue(voucher.is_posted)
        self.assertEqual(voucher.total_debit, Decimal("18000.00"))
        self.assertEqual(voucher.total_credit, Decimal("18000.00"))
        self.assertEqual(voucher.lines.count(), 2)

        # 2. Imbalanced Voucher (Debit != Credit) MUST fail with ValidationError
        unbalanced_lines = [
            {"account_code": "5001", "account_name": "Knitting Expense", "debit": Decimal("18000.00"), "credit": Decimal("0.00")},
            {"account_code": "2001", "account_name": "Knitter", "party_id": self.knitter.id, "debit": Decimal("0.00"), "credit": Decimal("15000.00")},
        ]
        with self.assertRaises(ValidationError) as ctx:
            CurrencyLedgerService.post_voucher(
                company_id=self.company.id,
                fy_id=self.fy.id,
                voucher_date="05/10/2026",
                voucher_type=VoucherTypes.JOURNAL,
                stage="KNITTING",
                lines=unbalanced_lines,
                user=self.user,
            )
        self.assertIn("Ledger Imbalance", str(ctx.exception))

    def test_currency_voucher_atomic_reversal(self):
        lines = [
            {"account_code": "5001", "account_name": "Dyeing Expense", "debit": Decimal("25000.00"), "credit": Decimal("0.00")},
            {"account_code": "2001", "account_name": "Dyer Payable", "party_id": self.knitter.id, "debit": Decimal("0.00"), "credit": Decimal("25000.00")},
        ]
        voucher = CurrencyLedgerService.post_voucher(
            company_id=self.company.id,
            fy_id=self.fy.id,
            voucher_date="05/10/2026",
            voucher_type=VoucherTypes.JOURNAL,
            stage="DYEING",
            lines=lines,
            party_id=self.knitter.id,
            user=self.user,
        )

        reversal = CurrencyLedgerService.reverse_voucher(
            voucher_id=voucher.id,
            company_id=self.company.id,
            reversal_date="05/10/2026",
            user=self.user,
        )

        voucher.refresh_from_db()
        self.assertTrue(voucher.is_reversed)
        self.assertEqual(voucher.reversed_by_id, reversal.id)
        self.assertEqual(reversal.total_debit, Decimal("25000.00"))
        self.assertEqual(reversal.total_credit, Decimal("25000.00"))

        # Reversing again should raise ConflictError
        with self.assertRaises(ConflictError):
            CurrencyLedgerService.reverse_voucher(
                voucher_id=voucher.id,
                company_id=self.company.id,
                reversal_date="05/10/2026",
                user=self.user,
            )

    def test_party_ledger_statement_and_apis(self):
        # Post a debit note (Payment) and a credit note (Bill)
        # 1. Jobwork bill of 10000 Cr to knitter
        CurrencyLedgerService.post_voucher(
            company_id=self.company.id,
            fy_id=self.fy.id,
            voucher_date="05/10/2026",
            voucher_type=VoucherTypes.JOURNAL,
            stage="KNITTING",
            lines=[
                {"account_code": "5001", "account_name": "Expense", "debit": Decimal("10000.00"), "credit": Decimal("0.00")},
                {"account_code": "2001", "account_name": "Knitter Payable", "party_id": self.knitter.id, "debit": Decimal("0.00"), "credit": Decimal("10000.00")},
            ],
            party_id=self.knitter.id,
            user=self.user,
        )

        # 2. Payment of 6000 Dr to knitter
        CurrencyLedgerService.post_voucher(
            company_id=self.company.id,
            fy_id=self.fy.id,
            voucher_date="05/10/2026",
            voucher_type=VoucherTypes.PAYMENT,
            stage="KNITTING",
            lines=[
                {"account_code": "2001", "account_name": "Knitter Payable", "party_id": self.knitter.id, "debit": Decimal("6000.00"), "credit": Decimal("0.00")},
                {"account_code": "1001", "account_name": "Bank Account", "debit": Decimal("0.00"), "credit": Decimal("6000.00")},
            ],
            party_id=self.knitter.id,
            user=self.user,
        )

        # Query statement API
        res = self.client.get(f"/api/v1/ledger/vouchers/party-statement/?party_id={self.knitter.id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["data"]["total_debit"], "6000.00")
        self.assertEqual(res.data["data"]["total_credit"], "10000.00")
        self.assertEqual(res.data["data"]["net_balance"], "-4000.00")
        self.assertEqual(res.data["data"]["balance_type"], "PAYABLE")
