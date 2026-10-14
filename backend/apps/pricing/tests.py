from decimal import Decimal
import datetime
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.authentication.models import User, Company, FinancialYear, Role, Privilege
from apps.masters.models import PartyMaster, YarnCountMaster, ColorShadeMaster, UnitOfMeasurement, FabricTypeMaster
from apps.process.models import parent_process_stage_table
from apps.pricing.models import PriceList, PriceListItem, PriceListJobRule, PricingAudit
from apps.pricing.services import PriceListService, PricingResolutionService
from apps.pricing.repositories import PriceListRepository, PriceListItemRepository, PriceListJobRuleRepository
from core.constants import (
    UserRoles,
    ModulePermissions,
    PartyTypes,
    PriceListType,
    PriceListScope,
    PriceListItemType,
    YarnCategory
)   
from core.exceptions import ValidationError, ResourceNotFound


class PricingEngineTestCase(TestCase):
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
            name="Pricing Manager",
            code="PRICING_MGR",
        )
        for mod in [ModulePermissions.PRICING_MANAGE, ModulePermissions.PRICING_VIEW]:
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
            username="pricing_officer",
            email="pricing@texgarments.com",
            password="testpassword123",
            company=self.company,
            active_financial_year=self.fy,
            custom_role=self.role,
            role=UserRoles.COMPANY_USER,
        )

        # 4. Master Fixtures
        self.mill_a = PartyMaster.objects.create(
            company=self.company,
            name="SVT Spinning Mills Ltd",
            code="MILL-SVT",
            party_type=PartyTypes.MILL,
            state="Tamil Nadu"
        )
        self.mill_b = PartyMaster.objects.create(
            company=self.company,
            name="Annamalaiar Spinning Mills",
            code="MILL-ANNAMALAI",
            party_type=PartyTypes.MILL,
            state="Tamil Nadu"
        )
        self.customer = PartyMaster.objects.create(
            company=self.company,
            name="Zudio Fashion Brands",
            code="CUST-ZUDIO",
            party_type=PartyTypes.CUSTOMER,
            state="Karnataka"
        )

        self.uom_kg = UnitOfMeasurement.objects.create(
            company=self.company,
            code="KGS",
            name="Kilograms"
        )
        self.count_30s = YarnCountMaster.objects.create(
            company=self.company,
            count="30s Combed",
            description="30s 100% Combed Cotton"
        )
        self.count_40s = YarnCountMaster.objects.create(
            company=self.company,
            count="40s Combed",
            description="40s 100% Combed Cotton"
        )
        self.shade_navy = ColorShadeMaster.objects.create(
            company=self.company,
            shade_code="NAVY-01",
            color_name="Navy Blue"
        )
        self.knitter = PartyMaster.objects.create(
            company=self.company,
            name="Annai Knitting Works",
            code="KNIT-ANNAI",
            party_type=PartyTypes.KNITTING_UNIT,
            state="Tamil Nadu"
        )
        self.fabric_sj = FabricTypeMaster.objects.create(
            company=self.company,
            name="Single Jersey",
            description="100% Cotton Single Jersey"
        )
        self.stage_knit = parent_process_stage_table.objects.create(
            company=self.company,
            name="Knitting",
            code="KNITTING",
            standard_rate=Decimal("17.00"),
            standard_loss_percent=Decimal("2.00")
        )
        self.stage_dye = parent_process_stage_table.objects.create(
            company=self.company,
            name="Dyeing",
            code="DYEING",
            standard_rate=Decimal("40.00"),
            standard_loss_percent=Decimal("4.00")
        )

        # 5. API Client
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.client.credentials(HTTP_X_COMPANY_ID=str(self.company.id))

    def test_create_and_validate_price_list_service(self):
        """Test creating General and Party-Specific price lists with validations."""
        today = datetime.date(2026, 10, 15)

        # Valid General Purchase Price List
        gen_list = PriceListService.create_price_list({
            "price_list_code": "PL-PUR-GEN-2026",
            "price_list_name": "Standard Yarn Purchase Price List 2026",
            "list_type": PriceListType.PURCHASE,
            "scope": PriceListScope.GENERAL,
            "valid_from": datetime.date(2026, 10, 1),
            "valid_to": datetime.date(2026, 12, 31),
            "is_default": True
        }, company_id=self.company.id, user_id=self.user.id)

        self.assertEqual(gen_list.price_list_code, "PL-PUR-GEN-2026")
        self.assertEqual(gen_list.record_status, "A")
        self.assertTrue(gen_list.is_default)

        # Duplicate code rejected
        with self.assertRaises(ValidationError):
            PriceListService.create_price_list({
                "price_list_code": "PL-PUR-GEN-2026",
                "price_list_name": "Duplicate List",
                "list_type": PriceListType.PURCHASE,
                "scope": PriceListScope.GENERAL,
                "valid_from": datetime.date(2026, 10, 1),
                "valid_to": datetime.date(2026, 12, 31),
            }, company_id=self.company.id)

        # Invalid date range rejected
        with self.assertRaises(ValidationError):
            PriceListService.create_price_list({
                "price_list_code": "PL-ERR-DATES",
                "price_list_name": "Invalid Dates",
                "list_type": PriceListType.PURCHASE,
                "scope": PriceListScope.GENERAL,
                "valid_from": datetime.date(2026, 12, 31),
                "valid_to": datetime.date(2026, 10, 1),
            }, company_id=self.company.id)

        # Party-specific requires party_id
        with self.assertRaises(ValidationError):
            PriceListService.create_price_list({
                "price_list_code": "PL-ERR-NOPARTY",
                "price_list_name": "Missing Party",
                "list_type": PriceListType.PURCHASE,
                "scope": PriceListScope.PARTY_SPECIFIC,
                "valid_from": datetime.date(2026, 10, 1),
                "valid_to": datetime.date(2026, 12, 31),
            }, company_id=self.company.id)

    def test_add_items_and_discount_calculation(self):
        """Test adding line items with discount and automatic net_rate calculation."""
        pl = PriceListService.create_price_list({
            "price_list_code": "PL-PUR-SVT",
            "price_list_name": "SVT Mills Yarn Contract",
            "list_type": PriceListType.PURCHASE,
            "scope": PriceListScope.PARTY_SPECIFIC,
            "party_id": self.mill_a.id,
            "valid_from": datetime.date(2026, 10, 1),
            "valid_to": datetime.date(2026, 12, 31),
        }, company_id=self.company.id, user_id=self.user.id)

        # Add 30s Combed line with base rate 280.00 and 5% discount
        item = PriceListService.add_item(pl.id, {
            "item_type": PriceListItemType.YARN,
            "yarn_count_id": self.count_30s.id,
            "yarn_type": YarnCategory.GREY,
            "uom_id": self.uom_kg.id,
            "min_quantity": Decimal("0.000"),
            "max_quantity": Decimal("1000.000"),
            "base_rate": Decimal("280.0000"),
            "discount_percent": Decimal("5.00"),
        }, company_id=self.company.id, user_id=self.user.id)

        # 280.00 * (1 - 0.05) = 266.0000
        self.assertEqual(item.net_rate, Decimal("266.0000"))

    def test_rate_determination_party_priority_over_general(self):
        """Test that Party-Specific price list takes precedence over General Base list."""
        doc_date = datetime.date(2026, 10, 15)

        # 1. Setup General List: 30s Combed @ ₹275.00/Kg
        gen_pl = PriceListService.create_price_list({
            "price_list_code": "PL-GEN-BASE",
            "price_list_name": "General Base List",
            "list_type": PriceListType.PURCHASE,
            "scope": PriceListScope.GENERAL,
            "valid_from": datetime.date(2026, 10, 1),
            "valid_to": datetime.date(2026, 12, 31),
            "is_default": True
        }, company_id=self.company.id)
        PriceListService.add_item(gen_pl.id, {
            "item_type": PriceListItemType.YARN,
            "yarn_count_id": self.count_30s.id,
            "base_rate": Decimal("275.0000"),
            "discount_percent": Decimal("0.00"),
        }, company_id=self.company.id)

        # 2. Setup Party List for Mill A: 30s Combed @ ₹260.00/Kg
        mill_pl = PriceListService.create_price_list({
            "price_list_code": "PL-SVT-CONTRACT",
            "price_list_name": "SVT Special Rate",
            "list_type": PriceListType.PURCHASE,
            "scope": PriceListScope.PARTY_SPECIFIC,
            "party_id": self.mill_a.id,
            "valid_from": datetime.date(2026, 10, 1),
            "valid_to": datetime.date(2026, 12, 31),
        }, company_id=self.company.id)
        PriceListService.add_item(mill_pl.id, {
            "item_type": PriceListItemType.YARN,
            "yarn_count_id": self.count_30s.id,
            "base_rate": Decimal("260.0000"),
            "discount_percent": Decimal("0.00"),
        }, company_id=self.company.id)

        # 3. Resolve for Mill A -> Must resolve party contract rate (₹260.00)
        res_a = PricingResolutionService.resolve_yarn_rate(
            company_id=self.company.id,
            context_type=PriceListType.PURCHASE,
            doc_date=doc_date,
            party_id=self.mill_a.id,
            yarn_count_id=self.count_30s.id,
            quantity=Decimal("500.000")
        )
        self.assertTrue(res_a["is_resolved"])
        self.assertEqual(res_a["pricing_source"], "PARTY_SPECIFIC")
        self.assertEqual(res_a["resolved_rate"], "260.0000")
        self.assertEqual(res_a["price_list_id"], mill_pl.id)

        # 4. Resolve for Mill B (No party contract) -> Must fall back to General Base rate (₹275.00)
        res_b = PricingResolutionService.resolve_yarn_rate(
            company_id=self.company.id,
            context_type=PriceListType.PURCHASE,
            doc_date=doc_date,
            party_id=self.mill_b.id,
            yarn_count_id=self.count_30s.id,
            quantity=Decimal("500.000")
        )
        self.assertTrue(res_b["is_resolved"])
        self.assertEqual(res_b["pricing_source"], "GENERAL")
        self.assertEqual(res_b["resolved_rate"], "275.0000")
        self.assertEqual(res_b["price_list_id"], gen_pl.id)

    def test_volume_break_slabs(self):
        """Test tiered quantity slab matching (e.g. 0-1000 Kg vs 1001-5000 Kg vs 5001+ Kg)."""
        doc_date = datetime.date(2026, 10, 15)

        pl = PriceListService.create_price_list({
            "price_list_code": "PL-SLABS-DEMO",
            "price_list_name": "Slabs Demo Price List",
            "list_type": PriceListType.PURCHASE,
            "scope": PriceListScope.GENERAL,
            "valid_from": datetime.date(2026, 10, 1),
            "valid_to": datetime.date(2026, 12, 31),
            "is_default": True
        }, company_id=self.company.id)

        # Slab 1: 0 to 1,000 Kg @ ₹270.00
        PriceListService.add_item(pl.id, {
            "item_type": PriceListItemType.YARN,
            "yarn_count_id": self.count_30s.id,
            "min_quantity": Decimal("0.000"),
            "max_quantity": Decimal("1000.000"),
            "base_rate": Decimal("270.0000"),
        }, company_id=self.company.id)

        # Slab 2: 1,001 to 5,000 Kg @ ₹262.00
        PriceListService.add_item(pl.id, {
            "item_type": PriceListItemType.YARN,
            "yarn_count_id": self.count_30s.id,
            "min_quantity": Decimal("1001.000"),
            "max_quantity": Decimal("5000.000"),
            "base_rate": Decimal("262.0000"),
        }, company_id=self.company.id)

        # Slab 3: 5,001+ Kg @ ₹255.00 (Unbounded upper limit)
        PriceListService.add_item(pl.id, {
            "item_type": PriceListItemType.YARN,
            "yarn_count_id": self.count_30s.id,
            "min_quantity": Decimal("5001.000"),
            "max_quantity": None,
            "base_rate": Decimal("255.0000"),
        }, company_id=self.company.id)

        # Query 1: 800 Kg -> Slab 1 (₹270.00)
        res_800 = PricingResolutionService.resolve_yarn_rate(
            company_id=self.company.id,
            context_type=PriceListType.PURCHASE,
            doc_date=doc_date,
            yarn_count_id=self.count_30s.id,
            quantity=Decimal("800.000")
        )
        self.assertEqual(res_800["resolved_rate"], "270.0000")
        self.assertTrue(res_800["is_slab_applied"])

        # Query 2: 3,500 Kg -> Slab 2 (₹262.00)
        res_3500 = PricingResolutionService.resolve_yarn_rate(
            company_id=self.company.id,
            context_type=PriceListType.PURCHASE,
            doc_date=doc_date,
            yarn_count_id=self.count_30s.id,
            quantity=Decimal("3500.000")
        )
        self.assertEqual(res_3500["resolved_rate"], "262.0000")
        self.assertTrue(res_3500["is_slab_applied"])

        # Query 3: 12,000 Kg -> Slab 3 (₹255.00)
        res_12000 = PricingResolutionService.resolve_yarn_rate(
            company_id=self.company.id,
            context_type=PriceListType.PURCHASE,
            doc_date=doc_date,
            yarn_count_id=self.count_30s.id,
            quantity=Decimal("12000.000")
        )
        self.assertEqual(res_12000["resolved_rate"], "255.0000")
        self.assertTrue(res_12000["is_slab_applied"])

    def test_date_validity_boundaries(self):
        """Test that transactions dated outside validity window do not match."""
        pl = PriceListService.create_price_list({
            "price_list_code": "PL-OCTOBER-ONLY",
            "price_list_name": "October Only Rates",
            "list_type": PriceListType.PURCHASE,
            "scope": PriceListScope.GENERAL,
            "valid_from": datetime.date(2026, 10, 1),
            "valid_to": datetime.date(2026, 10, 31),
            "is_default": True
        }, company_id=self.company.id)
        PriceListService.add_item(pl.id, {
            "item_type": PriceListItemType.YARN,
            "yarn_count_id": self.count_30s.id,
            "base_rate": Decimal("270.0000"),
        }, company_id=self.company.id)

        # In window: 2026-10-15 -> Resolved
        res_in = PricingResolutionService.resolve_yarn_rate(
            company_id=self.company.id,
            context_type=PriceListType.PURCHASE,
            doc_date=datetime.date(2026, 10, 15),
            yarn_count_id=self.count_30s.id
        )
        self.assertTrue(res_in["is_resolved"])

        # Expired: 2026-11-05 -> Unresolved
        res_out = PricingResolutionService.resolve_yarn_rate(
            company_id=self.company.id,
            context_type=PriceListType.PURCHASE,
            doc_date=datetime.date(2026, 11, 5),
            yarn_count_id=self.count_30s.id
        )
        self.assertFalse(res_out["is_resolved"])
        self.assertEqual(res_out["pricing_source"], "MANUAL")

    def test_audit_override_logging(self):
        """Test logging manual rate override to ta_pricing_audit and REST API."""
        audit = PricingResolutionService.record_override_audit(
            company_id=self.company.id,
            document_type="YARN_PO",
            document_id=101,
            system_rate=Decimal("270.0000"),
            actual_rate=Decimal("265.0000"),
            override_reason="Director agreed spot discount",
            approved_by=self.user.id,
            created_by=self.user.id,
            line_item_id=1
        )
        self.assertTrue(audit.is_override)
        self.assertEqual(audit.system_rate, Decimal("270.0000"))
        self.assertEqual(audit.actual_rate, Decimal("265.0000"))

        # Test GET /api/v1/pricing/audit/ without query params (lists company audit records)
        list_resp = self.client.get("/api/v1/pricing/audit/")
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(list_resp.data["data"]), 1)

        # Test POST /api/v1/pricing/audit/
        post_resp = self.client.post("/api/v1/pricing/audit/", {
            "document_type": "YARN_PO",
            "document_id": 102,
            "system_rate": "280.0000",
            "actual_rate": "275.0000",
            "override_reason": "Spot concession",
            "approved_by": self.user.id
        }, format="json")
        self.assertEqual(post_resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(post_resp.data["success"])
        self.assertTrue(post_resp.data["data"]["is_override"])

    def test_pricing_rest_api_endpoints(self):
        """Test REST API endpoints for price list management and rate resolution."""
        # 1. Create Price List via API
        payload = {
            "price_list_code": "PL-API-TEST",
            "price_list_name": "API Test Price List",
            "list_type": "PURCHASE",
            "scope": "GENERAL",
            "valid_from": "2026-10-01",
            "valid_to": "2026-12-31",
            "is_default": True,
            "items": [
                {
                    "item_type": "YARN",
                    "yarn_count_id": self.count_40s.id,
                    "min_quantity": "0.000",
                    "max_quantity": "2000.000",
                    "base_rate": "310.0000",
                    "discount_percent": "3.00"
                }
            ]
        }
        resp = self.client.post("/api/v1/pricing/lists/", payload, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resp.data["success"])
        list_id = resp.data["data"]["id"]

        # 2. List Price Lists via API
        list_resp = self.client.get("/api/v1/pricing/lists/")
        self.assertEqual(list_resp.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(list_resp.data["data"]), 1)

        # 3. Retrieve Price List Detail
        detail_resp = self.client.get(f"/api/v1/pricing/lists/{list_id}/")
        self.assertEqual(detail_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(detail_resp.data["data"]["price_list_code"], "PL-API-TEST")
        self.assertEqual(len(detail_resp.data["data"]["items"]), 1)

        # 4. Resolve Rate via API endpoint
        resolve_payload = {
            "context_type": "PURCHASE",
            "doc_date": "2026-10-15",
            "yarn_count_id": self.count_40s.id,
            "quantity": "1500.000"
        }
        res_resp = self.client.post("/api/v1/pricing/resolve/", resolve_payload, format="json")
        self.assertEqual(res_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(res_resp.data["success"])
        self.assertTrue(res_resp.data["data"]["is_resolved"])
        # 310 * (1 - 0.03) = 300.7000
        self.assertEqual(res_resp.data["data"]["resolved_rate"], "300.7000")

    def test_seed_default_price_lists(self):
        """Test seeding realistic price lists via API endpoint."""
        resp = self.client.post("/api/v1/pricing/seed-defaults/", format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(resp.data["success"])
        self.assertGreaterEqual(len(resp.data["data"]), 2)

    def test_job_work_knitting_rate_resolution_with_lycra(self):
        """Test Knitting job work rate resolution with base rate and lycra attachment surcharge."""
        doc_date = datetime.date(2026, 10, 15)

        pl = PriceListService.create_price_list({
            "price_list_code": "PL-JOB-KNIT-TEST",
            "price_list_name": "Knitting Rates Test",
            "list_type": PriceListType.JOB_WORK,
            "scope": PriceListScope.GENERAL,
            "valid_from": datetime.date(2026, 10, 1),
            "valid_to": datetime.date(2026, 12, 31),
            "is_default": True
        }, company_id=self.company.id)

        # Base Single Jersey @ 18.00 with 4.00 Lycra surcharge and 2.50% loss allowance
        PriceListService.add_job_rule(pl.id, {
            "process_stage_id": self.stage_knit.id,
            "fabric_type_id": self.fabric_sj.id,
            "machine_gauge": "24GG",
            "job_rate": Decimal("18.0000"),
            "allowed_loss_percent": Decimal("2.50"),
            "lycra_surcharge": Decimal("4.0000"),
            "min_quantity": Decimal("0.000")
        }, company_id=self.company.id)

        # 1. Plain Knitting (No Lycra) -> 18.0000
        res_plain = PricingResolutionService.resolve_job_work_rate(
            company_id=self.company.id,
            process_stage_id=self.stage_knit.id,
            doc_date=doc_date,
            fabric_type_id=self.fabric_sj.id,
            machine_gauge="24GG",
            is_lycra_plated=False
        )
        self.assertTrue(res_plain["is_resolved"])
        self.assertEqual(res_plain["resolved_rate"], "18.0000")
        self.assertEqual(res_plain["allowed_loss_percent"], "2.50")
        self.assertEqual(res_plain["lycra_surcharge"], "0.0000")

        # 2. Lycra Plated Knitting -> 18.0000 + 4.0000 = 22.0000
        res_lycra = PricingResolutionService.resolve_job_work_rate(
            company_id=self.company.id,
            process_stage_id=self.stage_knit.id,
            doc_date=doc_date,
            fabric_type_id=self.fabric_sj.id,
            machine_gauge="24GG",
            is_lycra_plated=True
        )
        self.assertTrue(res_lycra["is_resolved"])
        self.assertEqual(res_lycra["resolved_rate"], "22.0000")
        self.assertEqual(res_lycra["allowed_loss_percent"], "2.50")
        self.assertEqual(res_lycra["lycra_surcharge"], "4.0000")
        self.assertEqual(res_lycra["rate_breakdown"]["total_effective_rate"], "22.0000")

    def test_job_work_party_knitter_priority_over_general(self):
        """Test that Party-Specific knitter contract takes precedence over General Job Work list."""
        doc_date = datetime.date(2026, 10, 15)

        # General list @ 18.00
        gen_pl = PriceListService.create_price_list({
            "price_list_code": "PL-JOB-KNIT-GEN",
            "price_list_name": "General Knitting Rates",
            "list_type": PriceListType.JOB_WORK,
            "scope": PriceListScope.GENERAL,
            "valid_from": datetime.date(2026, 10, 1),
            "valid_to": datetime.date(2026, 12, 31),
            "is_default": True
        }, company_id=self.company.id)
        PriceListService.add_job_rule(gen_pl.id, {
            "process_stage_id": self.stage_knit.id,
            "fabric_type_id": self.fabric_sj.id,
            "job_rate": Decimal("18.0000"),
            "allowed_loss_percent": Decimal("2.50"),
        }, company_id=self.company.id)

        # Party list for Annai Knitter @ 16.00
        party_pl = PriceListService.create_price_list({
            "price_list_code": "PL-JOB-KNIT-ANNAI",
            "price_list_name": "Annai Knitting Contract",
            "list_type": PriceListType.JOB_WORK,
            "scope": PriceListScope.PARTY_SPECIFIC,
            "party_id": self.knitter.id,
            "valid_from": datetime.date(2026, 10, 1),
            "valid_to": datetime.date(2026, 12, 31),
        }, company_id=self.company.id)
        PriceListService.add_job_rule(party_pl.id, {
            "process_stage_id": self.stage_knit.id,
            "fabric_type_id": self.fabric_sj.id,
            "job_rate": Decimal("16.0000"),
            "allowed_loss_percent": Decimal("2.00"),
        }, company_id=self.company.id)

        # Query for Annai Knitter -> Gets 16.00
        res_annai = PricingResolutionService.resolve_job_work_rate(
            company_id=self.company.id,
            process_stage_id=self.stage_knit.id,
            party_id=self.knitter.id,
            doc_date=doc_date,
            fabric_type_id=self.fabric_sj.id
        )
        self.assertTrue(res_annai["is_resolved"])
        self.assertEqual(res_annai["pricing_source"], "PARTY_SPECIFIC")
        self.assertEqual(res_annai["resolved_rate"], "16.0000")
        self.assertEqual(res_annai["allowed_loss_percent"], "2.00")
        self.assertEqual(res_annai["price_list_id"], party_pl.id)

        # Query without party -> Gets 18.00
        res_other = PricingResolutionService.resolve_job_work_rate(
            company_id=self.company.id,
            process_stage_id=self.stage_knit.id,
            party_id=None,
            doc_date=doc_date,
            fabric_type_id=self.fabric_sj.id
        )
        self.assertTrue(res_other["is_resolved"])
        self.assertEqual(res_other["pricing_source"], "GENERAL")
        self.assertEqual(res_other["resolved_rate"], "18.0000")
        self.assertEqual(res_other["price_list_id"], gen_pl.id)

    def test_job_work_dyeing_rate_by_shade_depth(self):
        """Test Dyeing rate resolution based on shade depth category and bio-wash finish surcharge."""
        doc_date = datetime.date(2026, 10, 15)

        dye_pl = PriceListService.create_price_list({
            "price_list_code": "PL-JOB-DYE-TEST",
            "price_list_name": "Dyeing Rates Test",
            "list_type": PriceListType.JOB_WORK,
            "scope": PriceListScope.GENERAL,
            "valid_from": datetime.date(2026, 10, 1),
            "valid_to": datetime.date(2026, 12, 31),
            "is_default": True
        }, company_id=self.company.id)

        # White: 35.00, loss 3.00%
        PriceListService.add_job_rule(dye_pl.id, {
            "process_stage_id": self.stage_dye.id,
            "shade_category": "WHITE",
            "job_rate": Decimal("35.0000"),
            "allowed_loss_percent": Decimal("3.00"),
            "special_finish_surcharge": Decimal("8.0000")
        }, company_id=self.company.id)

        # Dark: 65.00, loss 4.50%, special finish (bio-wash) 8.00
        PriceListService.add_job_rule(dye_pl.id, {
            "process_stage_id": self.stage_dye.id,
            "shade_category": "DARK",
            "job_rate": Decimal("65.0000"),
            "allowed_loss_percent": Decimal("4.50"),
            "special_finish_surcharge": Decimal("8.0000")
        }, company_id=self.company.id)

        # 1. Resolve WHITE without finish -> 35.0000
        res_white = PricingResolutionService.resolve_job_work_rate(
            company_id=self.company.id,
            process_stage_id=self.stage_dye.id,
            doc_date=doc_date,
            shade_category="WHITE",
            special_finish_requested=False
        )
        self.assertEqual(res_white["resolved_rate"], "35.0000")
        self.assertEqual(res_white["allowed_loss_percent"], "3.00")

        # 2. Resolve DARK without finish -> 65.0000
        res_dark_plain = PricingResolutionService.resolve_job_work_rate(
            company_id=self.company.id,
            process_stage_id=self.stage_dye.id,
            doc_date=doc_date,
            shade_category="DARK",
            special_finish_requested=False
        )
        self.assertEqual(res_dark_plain["resolved_rate"], "65.0000")
        self.assertEqual(res_dark_plain["allowed_loss_percent"], "4.50")

        # 3. Resolve DARK with Bio-wash finish -> 65.0000 + 8.0000 = 73.0000
        res_dark_finish = PricingResolutionService.resolve_job_work_rate(
            company_id=self.company.id,
            process_stage_id=self.stage_dye.id,
            doc_date=doc_date,
            shade_category="DARK",
            special_finish_requested=True
        )
        self.assertEqual(res_dark_finish["resolved_rate"], "73.0000")
        self.assertEqual(res_dark_finish["special_finish_surcharge"], "8.0000")
        self.assertEqual(res_dark_finish["allowed_loss_percent"], "4.50")

    def test_job_work_stage_master_standard_rate_fallback(self):
        """Test fallback to Process Stage Master standard rate when no price list matches."""
        # No price list configured for self.stage_knit in this test
        res = PricingResolutionService.resolve_job_work_rate(
            company_id=self.company.id,
            process_stage_id=self.stage_knit.id,
            doc_date=datetime.date(2026, 10, 15)
        )
        self.assertTrue(res["is_resolved"])
        self.assertEqual(res["pricing_source"], "STAGE_STANDARD")
        self.assertEqual(res["resolved_rate"], "17.00")
        self.assertEqual(res["allowed_loss_percent"], "2.00")

    def test_job_work_rest_api_crud_and_resolve(self):
        """Test REST API endpoints for Job Work rules CRUD and rate resolution."""
        # 1. Create Job Work Price List via API
        pl_payload = {
            "price_list_code": "PL-API-JOBWORK",
            "price_list_name": "API Job Work Test List",
            "list_type": "JOB_WORK",
            "scope": "GENERAL",
            "valid_from": "2026-10-01",
            "valid_to": "2026-12-31",
            "is_default": True
        }
        create_resp = self.client.post("/api/v1/pricing/lists/", pl_payload, format="json")
        self.assertEqual(create_resp.status_code, status.HTTP_201_CREATED)
        list_id = create_resp.data["data"]["id"]

        # 2. Add Job Rule via /api/v1/pricing/lists/{id}/job-rules/
        rule_payload = {
            "process_stage_id": self.stage_knit.id,
            "fabric_type_id": self.fabric_sj.id,
            "machine_gauge": "24GG",
            "job_rate": "19.5000",
            "allowed_loss_percent": "2.25",
            "lycra_surcharge": "4.5000"
        }
        rule_resp = self.client.post(f"/api/v1/pricing/lists/{list_id}/job-rules/", rule_payload, format="json")
        self.assertEqual(rule_resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(rule_resp.data["success"])
        rule_id = rule_resp.data["data"]["id"]
        self.assertEqual(rule_resp.data["data"]["job_rate"], "19.5000")

        # 3. List Job Rules for Price List
        list_rules_resp = self.client.get(f"/api/v1/pricing/lists/{list_id}/job-rules/")
        self.assertEqual(list_rules_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_rules_resp.data["data"]), 1)

        # 4. Update Job Rule via /api/v1/pricing/job-rules/{id}/
        update_resp = self.client.put(f"/api/v1/pricing/job-rules/{rule_id}/", {"job_rate": "20.0000"}, format="json")
        self.assertEqual(update_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(update_resp.data["data"]["job_rate"], "20.0000")

        # 5. Resolve Job Work Rate via /api/v1/pricing/resolve/
        res_payload = {
            "context_type": "JOB_WORK",
            "process_stage_id": self.stage_knit.id,
            "fabric_type_id": self.fabric_sj.id,
            "machine_gauge": "24GG",
            "is_lycra_plated": True,
            "doc_date": "2026-10-15"
        }
        res_resp = self.client.post("/api/v1/pricing/resolve/", res_payload, format="json")
        self.assertEqual(res_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(res_resp.data["success"])
        self.assertTrue(res_resp.data["data"]["is_resolved"])
        # 20.0000 + 4.5000 = 24.5000
        self.assertEqual(res_resp.data["data"]["resolved_rate"], "24.5000")
        self.assertEqual(res_resp.data["data"]["allowed_loss_percent"], "2.25")

        # 6. Delete Job Rule via /api/v1/pricing/job-rules/{id}/
        del_resp = self.client.delete(f"/api/v1/pricing/job-rules/{rule_id}/")
        self.assertEqual(del_resp.status_code, status.HTTP_200_OK)
        self.assertTrue(del_resp.data["success"])


