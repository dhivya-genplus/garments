from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.authentication.models import User, Company, FinancialYear, Role, Privilege
from apps.authentication.services import CompanyService, UserService
from apps.masters.models import (
    PartyMaster, PartyRole, PartyContact, PartyAddress,
    PartyBankDetail, PartyCapability, PartyDocument,
    UnitOfMeasurement, YarnCountMaster, FabricTypeMaster, ProcessMaster
)
from apps.masters.services import PartyService
from apps.masters.repositories import PartyRepository
from apps.pricing.models import PriceList
from apps.ledger.models import tl_voucher, tl_voucher_line
from core.constants import (
    UserRoles, ModulePermissions, PartyTypes, PartyCategory,
    AddressTypes, GstRegistrationType, PaymentModes, VoucherTypes,
    PriceListType
)
from core.exceptions import ValidationError, ConflictError, ResourceNotFound


class PartyMasterCompleteTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Super Admin
        self.superadmin = UserService.create_user({
            "email": "sa_party_test@test.com",
            "username": "sa_party_test",
            "password": "Password123!",
            "role": UserRoles.SUPER_ADMIN,
            "is_superadmin": True
        })

        # 2. Company 1 & Admin User
        self.company1 = CompanyService.create_company({
            "name": "Tex Garments Mills Ltd",
            "code": "TEX01",
            "city": "Tirupur",
            "state": "Tamil Nadu"
        }, creator=self.superadmin)

        self.fy1 = FinancialYear.objects.create(
            company=self.company1,
            name="FY 2026-2027",
            code="FY2627",
            start_date="2026-04-01",
            end_date="2027-03-31",
            is_current=True
        )

        self.admin_user = UserService.create_user({
            "email": "admin_party@texgarments.com",
            "username": "admin_party",
            "password": "Password123!",
            "role": UserRoles.ADMIN_USER,
            "company": self.company1,
            "is_company_admin": True,
            "active_financial_year": self.fy1
        }, creator=self.superadmin)

        # 3. Standard Non-Admin User (for bank masking tests)
        self.std_role = Role.objects.create(
            company=self.company1,
            name="Standard Operator",
            code="STD_OP",
        )
        Privilege.objects.create(
            role=self.std_role,
            module=ModulePermissions.MASTERS_PARTY,
            can_create=True,
            can_read=True,
            can_update=True,
            can_delete=True,
            can_approve=False
        )

        self.standard_user = UserService.create_user({
            "email": "operator_party@texgarments.com",
            "username": "operator_party",
            "password": "Password123!",
            "role": UserRoles.COMPANY_USER,
            "company": self.company1,
            "is_company_admin": False,
            "custom_role": self.std_role,
            "active_financial_year": self.fy1
        }, creator=self.superadmin)

        # 4. Company 2 (for multi-tenant isolation verification)
        self.company2 = CompanyService.create_company({
            "name": "Coimbatore Spinning Corp",
            "code": "CSC02",
            "city": "Coimbatore",
            "state": "Tamil Nadu"
        }, creator=self.superadmin)

        # 5. Supporting Master Records
        self.uom_kgs = UnitOfMeasurement.objects.create(company=self.company1, code="KGS", name="Kilograms")
        self.count_30s = YarnCountMaster.objects.create(company=self.company1, count="30s", description="30s Combed Cotton")
        self.fabric_sj = FabricTypeMaster.objects.create(company=self.company1, code="SJ", name="Single Jersey")
        self.process_knit = ProcessMaster.objects.create(company=self.company1, process_code="KNIT", process_name="Circular Knitting")

    def test_multi_role_party_creation_and_filtering(self):
        """Verify creating a party with multiple business roles and querying by role."""
        payload = {
            "code": "MILL-KNIT-01",
            "name": "Kongu Composite Mills Pvt Ltd",
            "display_name": "Kongu Mills",
            "party_category": PartyCategory.MANUFACTURER,
            "party_type": PartyTypes.MILL,
            "roles": [
                {"role": PartyTypes.MILL, "is_primary": True},
                {"role": PartyTypes.KNITTING_UNIT, "is_primary": False},
                {"role": PartyTypes.SUPPLIER, "is_primary": False}
            ],
            "city": "Tirupur",
            "state": "Tamil Nadu"
        }

        party = PartyService.create_party(self.company1.id, payload, self.admin_user)
        self.assertEqual(party.code, "MILL-KNIT-01")
        self.assertEqual(party.roles.count(), 3)
        self.assertTrue(party.roles.filter(role=PartyTypes.KNITTING_UNIT).exists())
        self.assertTrue(party.roles.filter(role=PartyTypes.MILL, is_primary=True).exists())

        # Test Repository list by role
        knitters = PartyRepository.list_by_role(self.company1.id, PartyTypes.KNITTING_UNIT)
        self.assertIn(party, knitters)

        # Test API filtering by role (?role=KNITTING_UNIT)
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(f"/api/v1/masters/parties/?role={PartyTypes.KNITTING_UNIT}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        codes = [item["code"] for item in res.json()["data"]]
        self.assertIn("MILL-KNIT-01", codes)

        # Querying an unassigned role should exclude this party
        res_dyer = self.client.get(f"/api/v1/masters/parties/?role={PartyTypes.DYEING_UNIT}")
        self.assertEqual(res_dyer.status_code, status.HTTP_200_OK)
        dyer_codes = [item["code"] for item in res_dyer.json()["data"]]
        self.assertNotIn("MILL-KNIT-01", dyer_codes)

    def test_company_scoped_duplicate_code_validation(self):
        """Verify duplicate codes are prevented within the same company but allowed across different companies."""
        # 1. Create in Company 1
        PartyService.create_party(self.company1.id, {
            "code": "DUP-CODE-01",
            "name": "First Instance Ltd",
            "party_type": PartyTypes.SUPPLIER,
            "city": "Tirupur"
        }, self.admin_user)

        # 2. Duplicate in Company 1 must raise ConflictError
        with self.assertRaises(ConflictError):
            PartyService.create_party(self.company1.id, {
                "code": "DUP-CODE-01",
                "name": "Second Instance Ltd",
                "party_type": PartyTypes.SUPPLIER,
                "city": "Tirupur"
            }, self.admin_user)

        # 3. Same code in Company 2 must SUCCEED
        party_c2 = PartyService.create_party(self.company2.id, {
            "code": "DUP-CODE-01",
            "name": "Company Two Instance Ltd",
            "party_type": PartyTypes.SUPPLIER,
            "city": "Coimbatore"
        }, self.superadmin)
        self.assertEqual(party_c2.code, "DUP-CODE-01")
        self.assertEqual(party_c2.company_id, self.company2.id)

    def test_multi_contact_and_address_creation_with_flat_syncing(self):
        """Verify multi-contact and multi-address creation auto-synchronizes flat fields for backward compatibility."""
        payload = {
            "code": "SYNC-001",
            "name": "Synchronized Enterprises",
            "party_type": PartyTypes.CUSTOMER,
            "contacts": [
                {
                    "contact_person": "P. Ramesh (Primary)",
                    "designation": "Commercial Director",
                    "mobile": "+91 9842211999",
                    "email": "ramesh@sync.com",
                    "is_primary": True
                },
                {
                    "contact_person": "S. Suresh (Accounts)",
                    "designation": "Finance Manager",
                    "mobile": "+91 9842222888",
                    "email": "accounts@sync.com",
                    "is_primary": False
                }
            ],
            "addresses": [
                {
                    "address_type": AddressTypes.REGISTERED,
                    "address_line1": "100 Avinashi Main Road",
                    "city": "Tirupur",
                    "state": "Tamil Nadu",
                    "pincode": "641602",
                    "is_default": True
                },
                {
                    "address_type": AddressTypes.DELIVERY,
                    "address_line1": "Warehouse Plot 45, SIPCOT",
                    "city": "Perundurai",
                    "state": "Tamil Nadu",
                    "pincode": "638052",
                    "is_default": False
                }
            ]
        }

        party = PartyService.create_party(self.company1.id, payload, self.admin_user)
        self.assertEqual(party.contacts.count(), 2)
        self.assertEqual(party.addresses.count(), 2)

        # Verify synchronized flat fields
        self.assertEqual(party.contact_person, "P. Ramesh (Primary)")
        self.assertEqual(party.phone, "+91 9842211999")
        self.assertEqual(party.email, "ramesh@sync.com")
        self.assertEqual(party.city, "Tirupur")
        self.assertEqual(party.state, "Tamil Nadu")
        self.assertEqual(party.pincode, "641602")

    def test_gstin_validation_and_auto_pan_extraction(self):
        """Verify statutory validation rules: format checking, auto-PAN extraction, and unregistered tolerance."""
        # 1. Invalid GSTIN format raises ValidationError
        with self.assertRaises(ValidationError):
            PartyService.create_party(self.company1.id, {
                "code": "INVALID-GST",
                "name": "Bad GST Party",
                "party_type": PartyTypes.SUPPLIER,
                "gst_registration_type": GstRegistrationType.REGULAR,
                "gst_number": "INVALID12345"
            }, self.admin_user)

        # 2. Valid GSTIN auto-extracts PAN if PAN not provided
        valid_gstin = "33AABCT1234F1Z8"
        party = PartyService.create_party(self.company1.id, {
            "code": "AUTO-PAN-01",
            "name": "Auto PAN Extracted Ltd",
            "party_type": PartyTypes.MILL,
            "gst_registration_type": GstRegistrationType.REGULAR,
            "gst_number": valid_gstin
        }, self.admin_user)
        self.assertEqual(party.gst_number, valid_gstin)
        self.assertEqual(party.pan_number, "AABCT1234F")

        # 3. Conflicting PAN raises ValidationError
        with self.assertRaises(ValidationError):
            PartyService.create_party(self.company1.id, {
                "code": "PAN-CONFLICT",
                "name": "Conflicting PAN Party",
                "party_type": PartyTypes.MILL,
                "gst_registration_type": GstRegistrationType.REGULAR,
                "gst_number": valid_gstin,
                "pan_number": "ZZZZZ9999Z"
            }, self.admin_user)

        # 4. Unregistered party without GSTIN succeeds
        unreg_party = PartyService.create_party(self.company1.id, {
            "code": "UNREG-001",
            "name": "Local Jobworker (Unregistered)",
            "party_type": PartyTypes.JOB_WORKER,
            "gst_registration_type": GstRegistrationType.UNREGISTERED,
            "pan_number": "AABCP5678Q"
        }, self.admin_user)
        self.assertEqual(unreg_party.gst_registration_type, GstRegistrationType.UNREGISTERED)
        self.assertEqual(unreg_party.gst_number, "")

    def test_encrypted_bank_account_storage_and_api_masking(self):
        """Verify bank account numbers are stored encrypted and masked in API for standard users."""
        party = PartyService.create_party(self.company1.id, {
            "code": "BANK-TEST-01",
            "name": "Secure Banking Corp",
            "party_type": PartyTypes.SUPPLIER,
            "bank_details": [
                {
                    "bank_name": "State Bank of India",
                    "branch_name": "Kumaran Road, Tirupur",
                    "account_holder_name": "Secure Banking Corp",
                    "account_number": "12345678901234",
                    "ifsc_code": "SBIN0001234",
                    "preferred_payment_mode": PaymentModes.NEFT_RTGS,
                    "is_default": True
                }
            ]
        }, self.admin_user)

        # Verify DB storage decrypts cleanly via model property
        bank_obj = party.bank_details.first()
        self.assertEqual(bank_obj.account_number, "12345678901234")
        self.assertEqual(bank_obj.masked_account_number, "XXXXXXXXXX1234")

        # Verify standard user sees masked account number
        self.client.force_authenticate(user=self.standard_user)
        res_std = self.client.get(f"/api/v1/masters/parties/{party.id}/")
        self.assertEqual(res_std.status_code, status.HTTP_200_OK)
        std_bank = res_std.json()["data"]["bank_details"][0]
        self.assertEqual(std_bank["account_number"], bank_obj.masked_account_number)

        # Verify company admin sees unmasked raw account number
        self.client.force_authenticate(user=self.admin_user)
        res_adm = self.client.get(f"/api/v1/masters/parties/{party.id}/")
        self.assertEqual(res_adm.status_code, status.HTTP_200_OK)
        adm_bank = res_adm.json()["data"]["bank_details"][0]
        self.assertEqual(adm_bank["account_number"], "12345678901234")

    def test_price_list_linking_and_company_scoping(self):
        """Verify commercial price lists must belong to the same company and match expected type."""
        # 1. Price list in Company 1
        pl_c1 = PriceList.objects.create(
            company_id=self.company1.id,
            price_list_code="PL-YARN-C1",
            price_list_name="Yarn Price List C1",
            list_type=PriceListType.PURCHASE,
            valid_from=timezone.now().date(),
            valid_to=timezone.now().date() + timezone.timedelta(days=365),
            record_status="A"
        )

        # 2. Price list in Company 2
        pl_c2 = PriceList.objects.create(
            company_id=self.company2.id,
            price_list_code="PL-YARN-C2",
            price_list_name="Yarn Price List C2",
            list_type=PriceListType.PURCHASE,
            valid_from=timezone.now().date(),
            valid_to=timezone.now().date() + timezone.timedelta(days=365),
            record_status="A"
        )

        # Linking Company 2's price list to Company 1's party must fail
        with self.assertRaises(ValidationError):
            PartyService.create_party(self.company1.id, {
                "code": "PL-SCOPING-FAIL",
                "name": "Scoping Test Party",
                "party_type": PartyTypes.MILL,
                "default_purchase_price_list": pl_c2
            }, self.admin_user)

        # Linking Company 1's price list succeeds
        party = PartyService.create_party(self.company1.id, {
            "code": "PL-SCOPING-PASS",
            "name": "Scoping Test Party Success",
            "party_type": PartyTypes.MILL,
            "default_purchase_price_list": pl_c1
        }, self.admin_user)
        self.assertEqual(party.default_purchase_price_list_id, pl_c1.id)

    def test_textile_capabilities_mapping(self):
        """Verify textile and job-work processing capabilities mapping."""
        party = PartyService.create_party(self.company1.id, {
            "code": "CAP-001",
            "name": "Modern Knitting & Finishing",
            "party_type": PartyTypes.KNITTING_UNIT,
            "capability": {
                "machine_types": "24GG 30-inch circular knit machines (12 machines)",
                "production_capacity": Decimal("4500.000"),
                "capacity_uom": self.uom_kgs,
                "standard_processing_days": 3,
                "quality_certifications": "OEKO-TEX Standard 100",
                "processes_performed": [self.process_knit.id],
                "yarn_counts_handled": [self.count_30s.id],
                "fabric_types_handled": [self.fabric_sj.id]
            }
        }, self.admin_user)

        self.assertIsNotNone(party.capability)
        self.assertEqual(party.capability.machine_types, "24GG 30-inch circular knit machines (12 machines)")
        self.assertEqual(party.capability.production_capacity, Decimal("4500.000"))
        self.assertIn(self.process_knit, party.capability.processes_performed.all())
        self.assertIn(self.count_30s, party.capability.yarn_counts_handled.all())
        self.assertIn(self.fabric_sj, party.capability.fabric_types_handled.all())

        # Test API serialization
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(f"/api/v1/masters/parties/{party.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        cap_data = res.json()["data"]["capability"]
        self.assertIsNotNone(cap_data)
        self.assertEqual(cap_data["standard_processing_days"], 3)
        self.assertIn("Circular Knitting", cap_data["processes_performed_names"])

    def test_live_double_entry_ledger_balance_calculation(self):
        """Verify party financial balance is dynamically computed from tl_voucher_line without stored duplicates."""
        # Party with initial Credit opening balance of 100,000.00 (Payable)
        party = PartyService.create_party(self.company1.id, {
            "code": "LEDGER-TEST-01",
            "name": "Ledger Balance Mills",
            "party_type": PartyTypes.MILL,
            "opening_balance": Decimal("100000.00"),
            "opening_balance_type": "CR",
            "credit_limit": Decimal("500000.00")
        }, self.admin_user)

        # Create posted double-entry voucher
        vch1 = tl_voucher.objects.create(
            company=self.company1,
            cfyear=self.fy1,
            voucher_number="VCH-P-001",
            voucher_date=timezone.now().date(),
            voucher_type=VoucherTypes.PURCHASE,
            narration="Purchase invoice",
            total_debit=Decimal("40000.00"),
            total_credit=Decimal("40000.00"),
            is_posted=True
        )

        # Debit: Expense / Credit: Party 40,000.00 (Increases payable)
        tl_voucher_line.objects.create(
            voucher=vch1,
            account_code="2001",
            account_name="Party Payable",
            party=party,
            debit=Decimal("0.00"),
            credit=Decimal("40000.00"),
            narration="Party credit line"
        )
        tl_voucher_line.objects.create(
            voucher=vch1,
            account_code="5001",
            account_name="Yarn Purchase Account",
            party=None,
            debit=Decimal("40000.00"),
            credit=Decimal("0.00"),
            narration="Contra expense line"
        )

        # Payment voucher: Debit Party 15,000.00 (Reduces payable)
        vch2 = tl_voucher.objects.create(
            company=self.company1,
            cfyear=self.fy1,
            voucher_number="VCH-P-002",
            voucher_date=timezone.now().date(),
            voucher_type=VoucherTypes.PAYMENT,
            narration="Payment voucher",
            total_debit=Decimal("15000.00"),
            total_credit=Decimal("15000.00"),
            is_posted=True
        )
        tl_voucher_line.objects.create(
            voucher=vch2,
            account_code="2001",
            account_name="Party Payable",
            party=party,
            debit=Decimal("15000.00"),
            credit=Decimal("0.00"),
            narration="Party payment debit line"
        )
        tl_voucher_line.objects.create(
            voucher=vch2,
            account_code="1001",
            account_name="Bank Account",
            party=None,
            debit=Decimal("0.00"),
            credit=Decimal("15000.00"),
            narration="Contra bank line"
        )

        # Compute summary: net = total_dr (15,000) - (opening_cr 100,000 + voucher_cr 40,000) = -125,000.00
        summary = PartyService.get_party_financial_summary(party.id, self.company1.id)
        self.assertEqual(summary["total_debit"], Decimal("15000.00"))
        self.assertEqual(summary["total_credit"], Decimal("40000.00"))
        self.assertEqual(summary["net_outstanding_balance"], Decimal("-125000.00"))
        self.assertEqual(summary["balance_type"], "PAYABLE")

        # Test API action /api/v1/masters/parties/{id}/ledger-summary/
        self.client.force_authenticate(user=self.admin_user)
        res = self.client.get(f"/api/v1/masters/parties/{party.id}/ledger-summary/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.json()["data"] if "data" in res.json() else res.json()
        self.assertEqual(Decimal(str(data["net_outstanding_balance"])), Decimal("-125000.00"))

    def test_controlled_deactivation_preserving_history(self):
        """Verify controlled deactivation sets is_active=False without deleting historical transactions."""
        party = PartyService.create_party(self.company1.id, {
            "code": "DEACT-001",
            "name": "Deactivation Test Unit",
            "party_type": PartyTypes.CUSTOMER
        }, self.admin_user)

        self.assertTrue(party.is_active)
        self.assertIn(party, PartyRepository.list_active(self.company1.id))

        # Perform controlled deactivation
        deactivated = PartyService.deactivate_party(party.id, self.company1.id, self.admin_user)
        self.assertFalse(deactivated.is_active)
        self.assertNotIn(deactivated, PartyRepository.list_active(self.company1.id))

        # Direct retrieval still works and record is intact
        fetched = PartyRepository.get_by_id_and_company(party.id, self.company1.id)
        self.assertIsNotNone(fetched)
        self.assertFalse(fetched.is_active)
