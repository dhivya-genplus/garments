from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.authentication.models import User, Company, FinancialYear, Role, Privilege
from apps.masters.models import WarehouseMaster, PartyMaster, YarnCountMaster
from apps.inventory.models import parent_yarn_inward_table, yarn_stock_table
from apps.purchase.models import parent_po_table, parent_yarn_po_return_table, child_yarn_po_return_table
from apps.purchase.services import YarnPoReturnService
from apps.ledger.models import tl_voucher
from core.constants import UserRoles, ModulePermissions, PartyTypes, WarehouseTypes, YarnCategory, YarnDefectReasons, VoucherTypes
from core.exceptions import ValidationError, PermissionDeniedError, ResourceNotFound


class YarnPoReturnTestCase(TestCase):
    def setUp(self):
        # 1. Company & FY Setup (Active FY 2026-2027)
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
            is_closed=False,
        )

        # 2. Roles & Privileges
        self.role = Role.objects.create(
            company=self.company,
            name="Purchase Return Manager",
            code="PUR_RET_MGR",
        )
        for mod in [ModulePermissions.PURCHASE_YARN_PO, ModulePermissions.PURCHASE_YARN_PO_RETURN, ModulePermissions.INVENTORY_YARN_STOCK]:
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
            username="purchasemanager",
            email="purchase@texgarments.com",
            password="testpassword123",
            company=self.company,
            active_financial_year=self.fy,
            custom_role=self.role,
            role=UserRoles.COMPANY_USER,
        )

        # 4. Master Fixtures
        self.warehouse = WarehouseMaster.objects.create(
            company=self.company,
            name="Main Yarn Godown",
            warehouse_type=WarehouseTypes.YARN_GODOWN,
        )
        self.mill = PartyMaster.objects.create(
            company=self.company,
            name="Lakshmi Spinning Mills Ltd",
            code="LAK01",
            party_type=PartyTypes.MILL,
            state="Tamil Nadu",
            gst_number="33AABCL1234F1Z1",
        )
        self.yarn_count = YarnCountMaster.objects.create(
            company=self.company,
            count="30s Combed Cotton",
        )

        # 5. Upstream Authorized PO
        self.po = parent_po_table.objects.create(
            po_number="YPO-202610-0001",
            po_date="2026-10-05",
            company=self.company,
            cfyear=self.fy,
            party=self.mill,
            mill=self.mill,
            yarn_type=YarnCategory.GREY,
            bag=50,
            per_bag=Decimal("45.360"),
            quantity=Decimal("2268.000"),
            rate=Decimal("265.00"),
            amount=Decimal("601020.000"),
            is_authorized=1,
            status=1,
        )

        # 6. Upstream Authorized Inward GRN with unconsumed stock
        self.inward = parent_yarn_inward_table.objects.create(
            inward_number="YIN-202610-0001",
            inward_date="2026-10-10",
            dc_number="DC-MILL-441",
            dc_date="2026-10-09",
            yarn_type=YarnCategory.GREY,
            po=self.po,
            company=self.company,
            cfyear=self.fy,
            party=self.mill,
            mill=self.mill,
            warehouse=self.warehouse,
            yarn_count=self.yarn_count,
            lot_no="L-8802",
            bag=50,
            per_bag=Decimal("45.360"),
            net_wt=Decimal("2268.000"),
            rate=Decimal("265.00"),
            amount=Decimal("601020.000"),
            is_authorized=1,
            status=1,
        )

        # 7. Seed Initial Live Yarn Stock in Warehouse
        self.stock = yarn_stock_table.objects.create(
            company=self.company,
            warehouse=self.warehouse,
            yarn_type=YarnCategory.GREY,
            yarn_count=self.yarn_count,
            mill=self.mill,
            lot_no="L-8802",
            inward_bag=50,
            inward_quantity=Decimal("2268.000"),
            outward_bag=0,
            outward_quantity=Decimal("0.000"),
            sales_bag=0,
            sales_quantity=Decimal("0.000"),
            sales_return_bag=0,
            sales_return_quantity=Decimal("0.000"),
            balance_bag=50,
            balance_quantity=Decimal("2268.000"),
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_create_yarn_po_return_success(self):
        """Test successful Yarn PO Return with atomic stock deduction and balanced debit note."""
        payload = {
            "po_id": self.po.id,
            "inward_id": self.inward.id,
            "party_id": self.mill.id,
            "warehouse_id": self.warehouse.id,
            "yarn_count_id": self.yarn_count.id,
            "yarn_type": YarnCategory.GREY,
            "lot_no": "L-8802",
            "defect_reason": YarnDefectReasons.LOW_CSP,
            "defect_notes": "Tested CSP 2450 is below required 3000 contractual minimum.",
            "bag": 20,
            "per_bag": "45.360",
            "quantity": "907.200",
            "rate": "265.00",
            "tax_percent": "5.00",
            "return_date": "17/10/2026",
            "transporter_name": "VRL Logistics Ltd",
            "vehicle_no": "TN-39-BZ-1290",
            "lr_number": "LR-998821034",
        }

        po_return = YarnPoReturnService.create_po_return(payload, company_id=self.company.id, user=self.user)

        self.assertIsNotNone(po_return.id)
        self.assertTrue(po_return.return_number.startswith("YPR-"))
        self.assertTrue(po_return.debit_note_number.startswith("DN-"))
        self.assertEqual(po_return.bag, 20)
        self.assertEqual(po_return.quantity, Decimal("907.200"))
        self.assertEqual(po_return.subtotal, Decimal("240408.000"))
        self.assertEqual(po_return.total_debit_amount, Decimal("252428.400"))

        # Verify stock was deducted atomically from live ledger
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.outward_bag, 20)
        self.assertEqual(self.stock.outward_quantity, Decimal("907.200"))
        self.assertEqual(self.stock.balance_bag, 30)
        self.assertEqual(self.stock.balance_quantity, Decimal("1360.800"))

        # Verify balanced Debit Note voucher was created in tl_voucher
        self.assertIsNotNone(po_return.voucher_id)
        voucher = tl_voucher.objects.get(id=po_return.voucher_id)
        self.assertEqual(voucher.voucher_type, VoucherTypes.DEBIT_NOTE)
        self.assertTrue(voucher.is_posted)
        self.assertEqual(voucher.total_debit, Decimal("252428.40"))
        self.assertEqual(voucher.total_credit, Decimal("252428.40"))

    # -----------------------------------------------------------------
    # RESTRICTION 1: Stock & Inventory Safeguards (Zero Negative Stock)
    # -----------------------------------------------------------------
    def test_restriction_1_insufficient_stock_fails(self):
        """Test returning more yarn than available physical stock violates Requested Return Weight <= Available Godown Stock."""
        # Ensure Inward GRN has plenty of unconsumed balance (5000 Kg) so the failure is specifically at the live physical godown stock check
        self.inward.net_wt = Decimal("5000.000")
        self.inward.save()

        payload = {
            "po_id": self.po.id,
            "inward_id": self.inward.id,
            "party_id": self.mill.id,
            "warehouse_id": self.warehouse.id,
            "yarn_count_id": self.yarn_count.id,
            "yarn_type": YarnCategory.GREY,
            "lot_no": "L-8802",
            "defect_reason": YarnDefectReasons.COUNT_VARIATION,
            "defect_notes": "Count deviation observed: tested 34s Ne instead of 30s contractual.",
            "bag": 70,  # Available is only 50 bags (2268 Kg)
            "per_bag": "45.360",
            "quantity": "3175.200",
            "rate": "265.00",
        }

        with self.assertRaises(ValidationError) as ctx:
            YarnPoReturnService.create_po_return(payload, company_id=self.company.id, user=self.user)
        self.assertIn("Insufficient stock", str(ctx.exception))
        self.assertIn("invariant violated", str(ctx.exception))

    def test_restriction_1_zero_stock_lot_fails(self):
        """Test returning against a non-existent stock lot raises Zero Physical Stock error."""
        # Create an authorized inward for another lot that has NO physical stock
        other_inward = parent_yarn_inward_table.objects.create(
            inward_number="YIN-202610-0099",
            inward_date="2026-10-10",
            dc_number="DC-MILL-999",
            dc_date="2026-10-09",
            yarn_type=YarnCategory.GREY,
            po=self.po,
            company=self.company,
            cfyear=self.fy,
            party=self.mill,
            mill=self.mill,
            warehouse=self.warehouse,
            yarn_count=self.yarn_count,
            lot_no="L-NOSTOCK",
            bag=10,
            per_bag=Decimal("45.360"),
            net_wt=Decimal("453.600"),
            rate=Decimal("265.00"),
            amount=Decimal("120204.000"),
            is_authorized=1,
            status=1,
        )
        payload = {
            "po_id": self.po.id,
            "inward_id": other_inward.id,
            "party_id": self.mill.id,
            "warehouse_id": self.warehouse.id,
            "yarn_count_id": self.yarn_count.id,
            "yarn_type": YarnCategory.GREY,
            "lot_no": "L-NOSTOCK",
            "defect_reason": YarnDefectReasons.DAMAGED_CONES,
            "defect_notes": "Crushed cones in transit.",
            "bag": 10,
            "per_bag": "45.360",
            "quantity": "453.600",
            "rate": "265.00",
        }
        with self.assertRaises(ValidationError) as ctx:
            YarnPoReturnService.create_po_return(payload, company_id=self.company.id, user=self.user)
        self.assertIn("Zero Physical Stock", str(ctx.exception))

    # -----------------------------------------------------------------
    # RESTRICTION 2: Upstream Source Document Binding
    # -----------------------------------------------------------------
    def test_restriction_2_missing_upstream_po_or_grn_fails(self):
        """Test that missing po_id or inward_id raises ValidationError."""
        payload_no_po = {
            "inward_id": self.inward.id,
            "party_id": self.mill.id,
            "defect_reason": YarnDefectReasons.LOW_CSP,
            "defect_notes": "Substandard strength.",
            "quantity": "100.000",
        }
        with self.assertRaises(ValidationError) as ctx:
            YarnPoReturnService.create_po_return(payload_no_po, company_id=self.company.id, user=self.user)
        self.assertIn("Upstream Binding Required", str(ctx.exception))
        self.assertIn("po_id", str(ctx.exception))

        payload_no_inward = {
            "po_id": self.po.id,
            "party_id": self.mill.id,
            "defect_reason": YarnDefectReasons.LOW_CSP,
            "defect_notes": "Substandard strength.",
            "quantity": "100.000",
        }
        with self.assertRaises(ValidationError) as ctx:
            YarnPoReturnService.create_po_return(payload_no_inward, company_id=self.company.id, user=self.user)
        self.assertIn("Upstream Binding Required", str(ctx.exception))
        self.assertIn("inward_id", str(ctx.exception))

    def test_restriction_2_unauthorized_po_or_grn_fails(self):
        """Test that referencing a draft (unauthorized) PO or GRN is strictly rejected."""
        draft_po = parent_po_table.objects.create(
            po_number="YPO-DRAFT-0001",
            po_date="2026-10-05",
            company=self.company,
            cfyear=self.fy,
            party=self.mill,
            mill=self.mill,
            is_authorized=0,
            status=1,
        )
        payload = {
            "po_id": draft_po.id,
            "inward_id": self.inward.id,
            "party_id": self.mill.id,
            "defect_reason": YarnDefectReasons.LOW_CSP,
            "defect_notes": "Substandard strength.",
            "quantity": "100.000",
        }
        with self.assertRaises(ValidationError) as ctx:
            YarnPoReturnService.create_po_return(payload, company_id=self.company.id, user=self.user)
        self.assertIn("draft status", str(ctx.exception))

    def test_restriction_2_party_mismatch_fails(self):
        """Test that spinning mill vendor selected must match the exact party associated with PO and GRN."""
        other_mill = PartyMaster.objects.create(
            company=self.company,
            name="Sri Ranga Spinning Mills Ltd",
            code="SRI01",
            party_type=PartyTypes.MILL,
            state="Tamil Nadu",
        )
        payload = {
            "po_id": self.po.id,
            "inward_id": self.inward.id,
            "party_id": other_mill.id,
            "defect_reason": YarnDefectReasons.LOW_CSP,
            "defect_notes": "Substandard strength.",
            "quantity": "100.000",
        }
        with self.assertRaises(ValidationError) as ctx:
            YarnPoReturnService.create_po_return(payload, company_id=self.company.id, user=self.user)
        self.assertIn("Party Mismatch", str(ctx.exception))

    def test_restriction_2_lot_mismatch_fails(self):
        """Test that return lot must match the specific inward lot."""
        payload = {
            "po_id": self.po.id,
            "inward_id": self.inward.id,
            "party_id": self.mill.id,
            "lot_no": "L-DIFFERENT-9999",
            "defect_reason": YarnDefectReasons.LOW_CSP,
            "defect_notes": "Substandard strength.",
            "quantity": "100.000",
        }
        with self.assertRaises(ValidationError) as ctx:
            YarnPoReturnService.create_po_return(payload, company_id=self.company.id, user=self.user)
        self.assertIn("Lot Mismatch", str(ctx.exception))

    def test_restriction_2_exceeds_unconsumed_grn_balance_fails(self):
        """Test that return quantity cannot exceed unconsumed balance of inward GRN."""
        payload = {
            "po_id": self.po.id,
            "inward_id": self.inward.id,
            "party_id": self.mill.id,
            "warehouse_id": self.warehouse.id,
            "yarn_count_id": self.yarn_count.id,
            "yarn_type": YarnCategory.GREY,
            "lot_no": "L-8802",
            "defect_reason": YarnDefectReasons.LOW_CSP,
            "defect_notes": "Substandard strength.",
            "bag": 60,
            "per_bag": "45.360",
            "quantity": "2721.600",  # inward net_wt is 2268.000
            "rate": "265.00",
        }
        with self.assertRaises(ValidationError) as ctx:
            YarnPoReturnService.create_po_return(payload, company_id=self.company.id, user=self.user)
        self.assertIn("exceeds unconsumed balance", str(ctx.exception))

    # -----------------------------------------------------------------
    # RESTRICTION 3: Role-Based Access Control (RBAC) & Privileges
    # -----------------------------------------------------------------
    def test_restriction_3_rbac_unauthorized_user_forbidden(self):
        """Test regular unauthorized user without purchase_return.can_create receives PermissionDeniedError."""
        unauth_role = Role.objects.create(
            company=self.company,
            name="Junior Operator",
            code="JR_OPERATOR",
        )
        # Give read-only privilege
        Privilege.objects.create(
            role=unauth_role,
            module=ModulePermissions.PURCHASE_YARN_PO_RETURN,
            can_create=False,
            can_read=True,
            can_update=False,
            can_delete=False,
            can_approve=False,
        )
        unauth_user = User.objects.create_user(
            username="juniorop",
            email="junior@texgarments.com",
            password="testpassword123",
            company=self.company,
            custom_role=unauth_role,
            role=UserRoles.COMPANY_USER,
        )

        payload = {
            "po_id": self.po.id,
            "inward_id": self.inward.id,
            "party_id": self.mill.id,
            "warehouse_id": self.warehouse.id,
            "yarn_count_id": self.yarn_count.id,
            "yarn_type": YarnCategory.GREY,
            "lot_no": "L-8802",
            "defect_reason": YarnDefectReasons.LOW_CSP,
            "defect_notes": "Substandard strength.",
            "bag": 5,
            "per_bag": "45.360",
            "quantity": "226.800",
            "rate": "265.00",
        }
        with self.assertRaises(PermissionDeniedError) as ctx:
            YarnPoReturnService.create_po_return(payload, company_id=self.company.id, user=unauth_user)
        self.assertIn("purchase_return.can_create", str(ctx.exception))

        # Check API endpoint returns HTTP 403 Forbidden
        unauth_client = APIClient()
        unauth_client.force_authenticate(user=unauth_user)
        response = unauth_client.post("/api/v1/purchase/yarn-po-returns/", payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # -----------------------------------------------------------------
    # RESTRICTION 4: Mandatory Quality Defect Codification
    # -----------------------------------------------------------------
    def test_restriction_4_mandatory_quality_defect_codification(self):
        """Test defect_reason must be an industry code and defect_notes must be >= 5 chars."""
        payload_bad_defect = {
            "po_id": self.po.id,
            "inward_id": self.inward.id,
            "party_id": self.mill.id,
            "defect_reason": "GENERIC_BAD_QUALITY",
            "defect_notes": "Some defect.",
        }
        with self.assertRaises(ValidationError) as ctx:
            YarnPoReturnService.create_po_return(payload_bad_defect, company_id=self.company.id, user=self.user)
        self.assertIn("Invalid defect code", str(ctx.exception))

        payload_bad_notes = {
            "po_id": self.po.id,
            "inward_id": self.inward.id,
            "party_id": self.mill.id,
            "defect_reason": YarnDefectReasons.HIGH_HAIRINESS,
            "defect_notes": "bad",  # less than 5 characters
        }
        with self.assertRaises(ValidationError) as ctx:
            YarnPoReturnService.create_po_return(payload_bad_notes, company_id=self.company.id, user=self.user)
        self.assertIn("Mandatory Defect Findings", str(ctx.exception))

    # -----------------------------------------------------------------
    # RESTRICTION 5: Multi-Tenant & Fiscal Period Constraints
    # -----------------------------------------------------------------
    def test_restriction_5_tenant_isolation_fails(self):
        """Test cross-tenant PO or GRN access is blocked at the database level."""
        other_company = Company.objects.create(
            name="Other Textile Mills Pvt Ltd",
            code="OTH01",
        )
        payload = {
            "po_id": self.po.id,
            "inward_id": self.inward.id,
            "party_id": self.mill.id,
            "defect_reason": YarnDefectReasons.LOW_CSP,
            "defect_notes": "Substandard strength.",
            "quantity": "100.000",
        }
        with self.assertRaises(ValidationError) as ctx:
            # Querying self.po from other_company
            YarnPoReturnService.create_po_return(payload, company_id=other_company.id, user=self.user)
        self.assertIn("does not belong to active company", str(ctx.exception))

    def test_restriction_5_closed_financial_year_fails(self):
        """Test returns cannot be posted within a closed financial year."""
        self.fy.is_closed = True
        self.fy.save()

        payload = {
            "po_id": self.po.id,
            "inward_id": self.inward.id,
            "party_id": self.mill.id,
            "warehouse_id": self.warehouse.id,
            "yarn_count_id": self.yarn_count.id,
            "yarn_type": YarnCategory.GREY,
            "lot_no": "L-8802",
            "defect_reason": YarnDefectReasons.LOW_CSP,
            "defect_notes": "Tested CSP 2450 is below required 3000 contractual minimum.",
            "bag": 10,
            "per_bag": "45.360",
            "quantity": "453.600",
            "rate": "265.00",
            "cfyear_id": self.fy.id,
        }
        with self.assertRaises(ValidationError) as ctx:
            YarnPoReturnService.create_po_return(payload, company_id=self.company.id, user=self.user)
        self.assertIn("Financial Year Lockdown", str(ctx.exception))
        self.assertIn("is closed", str(ctx.exception))

    def test_restriction_5_return_date_outside_fy_fails(self):
        """Test return date outside the FY period is blocked."""
        payload = {
            "po_id": self.po.id,
            "inward_id": self.inward.id,
            "party_id": self.mill.id,
            "warehouse_id": self.warehouse.id,
            "yarn_count_id": self.yarn_count.id,
            "yarn_type": YarnCategory.GREY,
            "lot_no": "L-8802",
            "defect_reason": YarnDefectReasons.LOW_CSP,
            "defect_notes": "Tested CSP 2450 is below required 3000 contractual minimum.",
            "bag": 10,
            "per_bag": "45.360",
            "quantity": "453.600",
            "rate": "265.00",
            "return_date": "15/01/2025",  # Outside FY 2026-2027
        }
        with self.assertRaises(ValidationError) as ctx:
            YarnPoReturnService.create_po_return(payload, company_id=self.company.id, user=self.user)
        self.assertIn("Financial Year Lockdown", str(ctx.exception))
        self.assertIn("outside the active Financial Year period", str(ctx.exception))

    # -----------------------------------------------------------------
    # RESTRICTION 6: Double-Entry Accounting Immutability & Reversals
    # -----------------------------------------------------------------
    def test_restriction_6_double_entry_interstate_igst(self):
        """Test interstate return automatically generates 5.0% IGST reversal in Debit Note voucher."""
        out_state_mill = PartyMaster.objects.create(
            company=self.company,
            name="Bangalore Spun Cottons Ltd",
            code="BLR01",
            party_type=PartyTypes.MILL,
            state="Karnataka",  # Company is Tamil Nadu -> Interstate
            gst_number="29AABCB1234F1Z1",
        )
        out_state_po = parent_po_table.objects.create(
            po_number="YPO-202610-0088",
            po_date="2026-10-05",
            company=self.company,
            cfyear=self.fy,
            party=out_state_mill,
            mill=out_state_mill,
            yarn_type=YarnCategory.GREY,
            is_authorized=1,
            status=1,
        )
        out_state_inward = parent_yarn_inward_table.objects.create(
            inward_number="YIN-202610-0088",
            inward_date="2026-10-10",
            dc_number="DC-BLR-88",
            dc_date="2026-10-09",
            yarn_type=YarnCategory.GREY,
            po=out_state_po,
            company=self.company,
            cfyear=self.fy,
            party=out_state_mill,
            mill=out_state_mill,
            warehouse=self.warehouse,
            yarn_count=self.yarn_count,
            lot_no="L-BLR-11",
            bag=20,
            per_bag=Decimal("45.360"),
            net_wt=Decimal("907.200"),
            rate=Decimal("280.00"),
            is_authorized=1,
            status=1,
        )
        yarn_stock_table.objects.create(
            company=self.company,
            warehouse=self.warehouse,
            yarn_type=YarnCategory.GREY,
            yarn_count=self.yarn_count,
            mill=out_state_mill,
            lot_no="L-BLR-11",
            inward_bag=20,
            inward_quantity=Decimal("907.200"),
            balance_bag=20,
            balance_quantity=Decimal("907.200"),
        )

        payload = {
            "po_id": out_state_po.id,
            "inward_id": out_state_inward.id,
            "party_id": out_state_mill.id,
            "warehouse_id": self.warehouse.id,
            "yarn_count_id": self.yarn_count.id,
            "yarn_type": YarnCategory.GREY,
            "lot_no": "L-BLR-11",
            "defect_reason": YarnDefectReasons.EXCESS_MOISTURE,
            "defect_notes": "Moisture regain measured at 11.2% exceeding standard 8.5%.",
            "bag": 10,
            "per_bag": "45.360",
            "quantity": "453.600",
            "rate": "280.00",
            "tax_percent": "5.00",
        }
        po_return = YarnPoReturnService.create_po_return(payload, company_id=self.company.id, user=self.user)

        self.assertEqual(po_return.igst_percent, Decimal("5.00"))
        self.assertGreater(po_return.igst_amount, Decimal("0.000"))
        self.assertEqual(po_return.cgst_amount, Decimal("0.000"))
        self.assertEqual(po_return.sgst_amount, Decimal("0.000"))

        # Verify voucher lines in tl_voucher
        voucher = tl_voucher.objects.get(id=po_return.voucher_id)
        account_codes = list(voucher.lines.values_list("account_code", flat=True))
        self.assertIn("1008", account_codes)  # IGST Input Tax Reversal

    def test_restriction_6_read_only_immutability_blocks_direct_update_delete(self):
        """Test posted return cannot be directly modified (PUT/PATCH) or deleted (DELETE)."""
        payload = {
            "po_id": self.po.id,
            "inward_id": self.inward.id,
            "party_id": self.mill.id,
            "warehouse_id": self.warehouse.id,
            "yarn_count_id": self.yarn_count.id,
            "yarn_type": YarnCategory.GREY,
            "lot_no": "L-8802",
            "defect_reason": YarnDefectReasons.DAMAGED_CONES,
            "defect_notes": "Transit damage and crushed cones.",
            "bag": 5,
            "per_bag": "45.360",
            "quantity": "226.800",
            "rate": "265.00",
            "tax_percent": "5.00",
        }
        po_return = YarnPoReturnService.create_po_return(payload, company_id=self.company.id, user=self.user)

        # PUT should be blocked with 400 IMMUTABLE_RECORD
        put_resp = self.client.put(f"/api/v1/purchase/yarn-po-returns/{po_return.id}/", {"rate": "300.00"}, format="json")
        self.assertEqual(put_resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(put_resp.data["error"]["code"], "IMMUTABLE_RECORD")

        # PATCH should be blocked with 400 IMMUTABLE_RECORD
        patch_resp = self.client.patch(f"/api/v1/purchase/yarn-po-returns/{po_return.id}/", {"rate": "300.00"}, format="json")
        self.assertEqual(patch_resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(patch_resp.data["error"]["code"], "IMMUTABLE_RECORD")

        # DELETE should be blocked with 400 IMMUTABLE_RECORD
        del_resp = self.client.delete(f"/api/v1/purchase/yarn-po-returns/{po_return.id}/")
        self.assertEqual(del_resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(del_resp.data["error"]["code"], "IMMUTABLE_RECORD")

    def test_restriction_6_formal_cancellation_restores_stock_and_reverses_voucher(self):
        """Test formal cancellation via /cancel/ endpoint atomically restores stock and posts contra-voucher."""
        payload = {
            "po_id": self.po.id,
            "inward_id": self.inward.id,
            "party_id": self.mill.id,
            "warehouse_id": self.warehouse.id,
            "yarn_count_id": self.yarn_count.id,
            "yarn_type": YarnCategory.GREY,
            "lot_no": "L-8802",
            "defect_reason": YarnDefectReasons.COLOR_SHADE_DEFECT,
            "defect_notes": "Color delta E deviation of 1.4 exceeds acceptable 0.8.",
            "bag": 10,
            "per_bag": "45.360",
            "quantity": "453.600",
            "rate": "265.00",
            "tax_percent": "5.00",
        }
        po_return = YarnPoReturnService.create_po_return(payload, company_id=self.company.id, user=self.user)
        voucher_id = po_return.voucher_id

        # Cancel return via API endpoint
        cancel_resp = self.client.post(f"/api/v1/purchase/yarn-po-returns/{po_return.id}/cancel/")
        self.assertEqual(cancel_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(cancel_resp.data["success"])

        # Stock should be restored
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.outward_bag, 0)
        self.assertEqual(self.stock.outward_quantity, Decimal("0.000"))
        self.assertEqual(self.stock.balance_bag, 50)
        self.assertEqual(self.stock.balance_quantity, Decimal("2268.000"))

        # Reversal voucher should be generated and original voucher marked is_reversed
        orig_voucher = tl_voucher.objects.get(id=voucher_id)
        self.assertTrue(orig_voucher.is_reversed)
