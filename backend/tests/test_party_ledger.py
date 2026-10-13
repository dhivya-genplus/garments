from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import User, Company, FinancialYear, Role, Privilege
from apps.masters.models import WarehouseMaster, PartyMaster, YarnCountMaster, UnitOfMeasurement
from apps.ledger.models import tl_voucher, tl_voucher_line
from apps.ledger.services import CurrencyLedgerService
from apps.sales.services import YarnSalesService
from apps.inventory.services import YarnInwardService
from core.constants import UserRoles, VoucherTypes, ModulePermissions, PartyTypes, WarehouseTypes, YarnCategory

class PartyLedgerMaintenanceTestCase(TestCase):
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

        # 2. Roles & User
        self.role = Role.objects.create(
            company=self.company,
            name="Ledger Accountant",
            code="LEDGER_ACC",
        )
        for mod in [
            ModulePermissions.LEDGER_STOCK,
            ModulePermissions.LEDGER_CURRENCY,
            ModulePermissions.SALES_YARN,
            ModulePermissions.INVENTORY_YARN_INWARD,
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
            username="accountant",
            email="accountant@texgarments.com",
            password="testpassword123",
            company=self.company,
            active_financial_year=self.fy,
            custom_role=self.role,
            role=UserRoles.COMPANY_USER,
        )

        # 3. Masters
        self.warehouse = WarehouseMaster.objects.create(
            company=self.company,
            name="Main Spinning Godown",
            warehouse_code="WH-SPIN-01",
            warehouse_type=WarehouseTypes.YARN_GODOWN,
        )
        self.uom = UnitOfMeasurement.objects.create(
            company=self.company, code="KGS", name="Kilograms"
        )
        self.yarn_count = YarnCountMaster.objects.create(
            company=self.company, count="30s"
        )

        # 4. Parties with opening balances
        self.customer = PartyMaster.objects.create(
            company=self.company,
            name="Premier Apparels Retail",
            code="CUST-001",
            party_type=PartyTypes.CUSTOMER,
            opening_balance=Decimal("25000.00"),  # Customer owes 25,000 Dr
        )
        self.mill = PartyMaster.objects.create(
            company=self.company,
            name="Lakshmi Spinning Mills Ltd",
            code="MILL-001",
            party_type=PartyTypes.MILL,
            opening_balance=Decimal("50000.00"),  # We owe mill 50,000 Cr
        )
        self.knitter = PartyMaster.objects.create(
            company=self.company,
            name="Annai Knitting Works",
            code="KNT-001",
            party_type=PartyTypes.KNITTING_UNIT,
            opening_balance=Decimal("10000.00"),  # We owe knitter 10,000 Cr
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_party_ledger_statement_includes_opening_balance(self):
        # 1. Customer statement must start with 25000 Dr
        res_cust = self.client.get(f"/api/v1/ledger/vouchers/party-statement/?party_id={self.customer.id}")
        self.assertEqual(res_cust.status_code, status.HTTP_200_OK)
        cust_data = res_cust.json()["data"]
        self.assertEqual(cust_data["opening_balance"], "25000.00")
        self.assertIn("RECEIVABLE", cust_data["opening_balance_type"])
        self.assertEqual(cust_data["closing_balance"], "25000.00")
        self.assertEqual(cust_data["balance_type"], "RECEIVABLE")

        # 2. Mill statement must start with -50000 Cr
        res_mill = self.client.get(f"/api/v1/ledger/vouchers/party-statement/?party_id={self.mill.id}")
        self.assertEqual(res_mill.status_code, status.HTTP_200_OK)
        mill_data = res_mill.json()["data"]
        self.assertEqual(mill_data["opening_balance"], "-50000.00")
        self.assertIn("PAYABLE", mill_data["opening_balance_type"])
        self.assertEqual(mill_data["closing_balance"], "-50000.00")
        self.assertEqual(mill_data["balance_type"], "PAYABLE")

    def test_date_range_accumulates_prior_movements_into_opening_balance(self):
        # Post a voucher on 05/04/2026: Bill of 15000 Cr to knitter
        CurrencyLedgerService.post_voucher(
            company_id=self.company.id,
            fy_id=self.fy.id,
            voucher_date="05/04/2026",
            voucher_type=VoucherTypes.JOURNAL,
            stage="KNITTING",
            lines=[
                {"account_code": "5001", "account_name": "Job Expense", "debit": Decimal("15000.00"), "credit": Decimal("0.00")},
                {"account_code": "2001", "account_name": "Knitter Payable", "party_id": self.knitter.id, "debit": Decimal("0.00"), "credit": Decimal("15000.00")},
            ],
            party_id=self.knitter.id,
            user=self.user,
        )

        # Post a payment voucher on 20/04/2026: Payment of 5000 Dr to knitter
        CurrencyLedgerService.record_party_payment(
            company_id=self.company.id,
            fy_id=self.fy.id,
            party_id=self.knitter.id,
            amount=Decimal("5000.00"),
            payment_date="20/04/2026",
            payment_mode="NEFT",
            user=self.user,
        )

        # Query statement from 10/04/2026 to 30/04/2026:
        # Opening balance before 10/04/2026 was: base (-10000) + voucher on 05/04 (-15000) = -25000.00
        res = self.client.get(
            f"/api/v1/ledger/vouchers/party-statement/?party_id={self.knitter.id}&from_date=10/04/2026&to_date=30/04/2026"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()["data"]

        self.assertEqual(data["opening_balance"], "-25000.00")
        self.assertEqual(len(data["transactions"]), 1)  # Only the payment on 20/04
        self.assertEqual(data["transactions"][0]["debit"], "5000.00")
        self.assertEqual(data["closing_balance"], "-20000.00")  # -25000 + 5000 = -20000

    def test_record_party_payment_api(self):
        # Post payment of 10000 to settle Knitter opening balance
        payload = {
            "party": self.knitter.id,
            "amount": "10000.00",
            "payment_date": "13/10/2026",
            "payment_mode": "RTGS",
            "reference_no": "UTR-998877",
            "narration": "Full settlement of opening balance",
        }
        res = self.client.post("/api/v1/ledger/vouchers/record-payment/", payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        voucher = res.json()["data"]
        self.assertEqual(voucher["voucher_type"], VoucherTypes.PAYMENT)
        self.assertEqual(voucher["total_debit"], "10000.00")
        self.assertEqual(voucher["total_credit"], "10000.00")

        # Statement should now show Knitter balance cleared to 0.00
        stmt = CurrencyLedgerService.get_party_ledger_statement(self.company.id, self.knitter.id)
        self.assertEqual(stmt["closing_balance"], "0.00")

    def test_record_party_receipt_api(self):
        # Customer pays 25000 to settle opening balance
        payload = {
            "party": self.customer.id,
            "amount": "25000.00",
            "receipt_date": "13/10/2026",
            "payment_mode": "CHEQUE",
            "reference_no": "CHQ-445566",
            "narration": "Customer advance & clearance",
        }
        res = self.client.post("/api/v1/ledger/vouchers/record-receipt/", payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        voucher = res.json()["data"]
        self.assertEqual(voucher["voucher_type"], VoucherTypes.RECEIPT)
        self.assertEqual(voucher["total_debit"], "25000.00")
        self.assertEqual(voucher["total_credit"], "25000.00")

        # Statement should now show Customer balance cleared to 0.00
        stmt = CurrencyLedgerService.get_party_ledger_statement(self.company.id, self.customer.id)
        self.assertEqual(stmt["closing_balance"], "0.00")

    def test_yarn_sales_automatically_updates_customer_ledger(self):
        # 1. Setup on-hand stock for Yarn Sales
        from apps.inventory.services import YarnStockService
        YarnStockService.add_inward_stock(
            company_id=self.company.id,
            warehouse_id=self.warehouse.id,
            yarn_type=YarnCategory.GREY,
            yarn_count_id=self.yarn_count.id,
            mill_id=self.mill.id,
            color_shade_id=None,
            lot_no="LOT-SALES-1",
            bag=50,
            quantity=Decimal("2500.000")
        )

        # 2. Issue Commercial Sales Invoice: 10 bags = 500 Kg @ 300 = 150,000 + 5% GST (7,500) = 157,500
        sales = YarnSalesService.create_sales(
            company_id=self.company.id,
            data={
                "yarn_type": YarnCategory.GREY,
                "customer_id": self.customer.id,
                "warehouse_id": self.warehouse.id,
                "yarn_count_id": self.yarn_count.id,
                "mill_id": self.mill.id,
                "lot_no": "LOT-SALES-1",
                "bag": 10,
                "per_bag": "50.000",
                "quantity": "500.000",
                "rate": "300.00",
                "tax_percent": "5.00",
                "invoice_number": "INV-TEST-001",
                "invoice_date": "13/10/2026",
            },
            user=self.user
        )
        self.assertIsNotNone(sales)

        # 3. Customer Ledger Statement must immediately reflect the 157,500 Dr invoice
        stmt = CurrencyLedgerService.get_party_ledger_statement(self.company.id, self.customer.id)
        # Opening (25,000) + New Invoice (157,500) = 182,500
        self.assertEqual(Decimal(stmt["closing_balance"]), Decimal("182500.00"))
        self.assertEqual(stmt["balance_type"], "RECEIVABLE")

        # 4. Cancel sales invoice -> verifies atomic reversal restores party ledger
        YarnSalesService.cancel_sales(sales.id, self.company.id, user=self.user)
        stmt_after = CurrencyLedgerService.get_party_ledger_statement(self.company.id, self.customer.id)
        # Should be restored back to opening balance (25,000)
        self.assertEqual(Decimal(stmt_after["closing_balance"]), Decimal("25000.00"))

    def test_party_ledger_transaction_against_and_filters(self):
        # 1. Record payment with explicit against_doc_number & against_doc_type
        pay_res = self.client.post("/api/v1/ledger/vouchers/record-payment/", {
            "party_id": self.mill.id,
            "amount": "30000.00",
            "payment_date": "13/10/2026",
            "payment_mode": "NEFT",
            "reference_no": "UTR99887766",
            "against_doc_type": "INWARD_GRN",
            "against_doc_number": "YIN-202610-0001",
            "narration": "Settlement of Inward GRN #0001",
        }, format="json")
        self.assertEqual(pay_res.status_code, status.HTTP_201_CREATED)

        # 2. Query party statement and verify 'transaction_against' field
        stmt_res = self.client.get(f"/api/v1/ledger/vouchers/party-statement/?party_id={self.mill.id}")
        self.assertEqual(stmt_res.status_code, status.HTTP_200_OK)
        stmt_data = stmt_res.json()["data"]
        txs = stmt_data["transactions"]
        self.assertTrue(len(txs) > 0)
        last_tx = txs[-1]
        self.assertIn("transaction_against", last_tx)
        self.assertEqual(last_tx["transaction_against"], "INWARD_GRN #YIN-202610-0001")
        self.assertEqual(last_tx["reference_no"], "YIN-202610-0001")

        # 3. Query party statement with reference_no filter
        filtered_res = self.client.get(f"/api/v1/ledger/vouchers/party-statement/?party_id={self.mill.id}&reference_no=YIN-202610-0001")
        self.assertEqual(filtered_res.status_code, status.HTTP_200_OK)
        filtered_data = filtered_res.json()["data"]
        self.assertEqual(len(filtered_data["transactions"]), 1)
        self.assertEqual(filtered_data["transactions"][0]["reference_no"], "YIN-202610-0001")

    def test_stock_ledger_party_filter_and_party_summary(self):
        from apps.ledger.services import StockLedgerService
        from core.constants import StockMovementTypes

        # 1. Record stock movements for Mill and Customer
        StockLedgerService.record_movement(
            company_id=self.company.id,
            fy_id=self.fy.id,
            movement_date="13/10/2026",
            stage="YARN",
            warehouse_id=self.warehouse.id,
            movement_type=StockMovementTypes.INWARD,
            doc_type="INWARD_GRN",
            doc_number="YIN-202610-9001",
            item_name="30s Combed Cotton Yarn",
            lot_or_batch_no="LOT-M9",
            in_units=20,
            in_qty=Decimal("1000.000"),
            party_id=self.mill.id,
            user=self.user,
        )

        StockLedgerService.record_movement(
            company_id=self.company.id,
            fy_id=self.fy.id,
            movement_date="13/10/2026",
            stage="YARN",
            warehouse_id=self.warehouse.id,
            movement_type=StockMovementTypes.SALES,
            doc_type="SALES_INVOICE",
            doc_number="YSI-202610-9001",
            item_name="30s Combed Cotton Yarn",
            lot_or_batch_no="LOT-M9",
            out_units=10,
            out_qty=Decimal("500.000"),
            party_id=self.customer.id,
            user=self.user,
        )

        # 2. Filter Stock Movements by party_id=self.mill.id
        mill_stock_res = self.client.get(f"/api/v1/ledger/stock-movements/?party_id={self.mill.id}")
        self.assertEqual(mill_stock_res.status_code, status.HTTP_200_OK)
        mill_data = mill_stock_res.json()["data"]
        self.assertTrue(len(mill_data) >= 1)
        for item in mill_data:
            self.assertEqual(item["party"], self.mill.id)

        # 3. Test Party Stock Summary endpoint for self.mill
        summary_res = self.client.get(f"/api/v1/ledger/stock-movements/party-summary/?party_id={self.mill.id}")
        self.assertEqual(summary_res.status_code, status.HTTP_200_OK)
        summary = summary_res.json()["data"]
        self.assertEqual(summary["party"]["id"], self.mill.id)
        self.assertEqual(Decimal(summary["total_inward_qty"]), Decimal("1000.000"))
        self.assertEqual(summary["total_inward_units"], 20)
        self.assertEqual(summary["movement_count"], 1)
        self.assertEqual(summary["movements"][0]["transaction_against"], "INWARD_GRN #YIN-202610-9001")
