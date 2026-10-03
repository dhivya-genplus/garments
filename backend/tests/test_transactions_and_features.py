from decimal import Decimal
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.authentication.models import User, Company, FinancialYear
from apps.authentication.services import CompanyService, UserService
from apps.masters.models import (
    UnitOfMeasurement, PartyMaster, YarnCountMaster, YarnTypeMaster,
    ColorShadeMaster, WarehouseMaster, quality_program_table
)
from apps.purchase.models import parent_po_table, child_po_table
from apps.purchase.services import YarnPOService
from apps.inventory.models import yarn_stock_table, parent_yarn_inward_table, parent_yarn_outward_table
from apps.inventory.services import YarnInwardService, YarnOutwardService
from apps.sales.models import parent_yarn_sales_table, parent_yarn_sales_return_table
from apps.sales.services import YarnSalesService, YarnSalesReturnService
from core.constants import UserRoles, YarnCategory, YarnOutwardTypes, PartyTypes, WarehouseTypes


class TransactionsAndFeaturesTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Super Admin
        self.superadmin = UserService.create_user({
            "email": "superadmin@test.com",
            "username": "superadmin_test",
            "password": "Password123!",
            "role": UserRoles.SUPER_ADMIN,
            "is_superadmin": True
        })

        # 2. Company & Company Admin
        self.company = CompanyService.create_company({
            "name": "Sovereign Garments Ltd",
            "code": "SGL",
        }, creator=self.superadmin)
        self.fy = self.company.current_financial_year

        self.company_admin = UserService.create_user({
            "email": "admin@sovereign.com",
            "username": "sovereign_admin",
            "password": "Password123!",
            "role": UserRoles.ADMIN_USER,
            "company": self.company,
            "is_company_admin": True
        }, creator=self.superadmin)

        # 3. Master records
        self.uom = UnitOfMeasurement.objects.create(
            company=self.company, code="KGS", name="Kilograms"
        )
        self.yarn_count = YarnCountMaster.objects.create(
            company=self.company, count="30s"
        )
        self.mill = PartyMaster.objects.create(
            company=self.company, party_type=PartyTypes.MILL, code="MILL-01", name="Lakshmi Mills"
        )
        self.supplier = PartyMaster.objects.create(
            company=self.company, party_type=PartyTypes.SUPPLIER, code="SUP-01", name="Sri Yarn Traders"
        )
        self.customer = PartyMaster.objects.create(
            company=self.company, party_type=PartyTypes.CUSTOMER, code="CUST-01", name="Prime Retailers"
        )
        self.knitter = PartyMaster.objects.create(
            company=self.company, party_type=PartyTypes.KNITTING_UNIT, code="KNIT-01", name="Annai Knitting"
        )
        self.warehouse = WarehouseMaster.objects.create(
            company=self.company, warehouse_code="WH-01", name="Main Yarn Warehouse", warehouse_type=WarehouseTypes.YARN_GODOWN
        )
        self.color_shade = ColorShadeMaster.objects.create(
            company=self.company, shade_code="NVY-01", color_name="Navy Blue"
        )

        # Authenticate client as company admin
        login_res = self.client.post('/api/v1/auth/login/', {
            "email": "admin@sovereign.com",
            "password": "Password123!"
        })
        self.token = login_res.json()['data']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_direct_and_prefixed_auth_routes(self):
        # Test direct /api/v1/auth/login/
        direct_res = self.client.post('/api/v1/auth/login/', {
            "email": "admin@sovereign.com",
            "password": "Password123!"
        })
        self.assertEqual(direct_res.status_code, status.HTTP_200_OK)
        self.assertTrue(direct_res.json()['success'])

        # Test prefixed /api/v1/auth/auth/login/
        prefixed_res = self.client.post('/api/v1/auth/auth/login/', {
            "email": "admin@sovereign.com",
            "password": "Password123!"
        })
        self.assertEqual(prefixed_res.status_code, status.HTTP_200_OK)
        self.assertTrue(prefixed_res.json()['success'])

    def test_po_lifecycle_authorization_lock_and_child_lines(self):
        # 1. Create PO via API without explicit cfyear (should auto-resolve)
        po_res = self.client.post('/api/v1/purchase/yarn-pos/', {
            "yarn_type": YarnCategory.GREY,
            "party": self.supplier.id,
            "mill": self.mill.id,
            "yarn_count": self.yarn_count.id,
            "bag": 100,
            "per_bag": "45.360",
            "rate": "280.00",
            "discount": "5.00"
        }, format='json')
        self.assertEqual(po_res.status_code, status.HTTP_201_CREATED)
        po_data = po_res.json()['data']
        po_id = po_data['id']
        self.assertEqual(po_data['is_authorized'], 0)
        self.assertEqual(len(po_data['line_items']), 1)
        self.assertEqual(po_data['line_items'][0]['remaining_bag'], 100)

        # 2. Authorize PO
        auth_res = self.client.post(f'/api/v1/purchase/yarn-pos/{po_id}/authorize/')
        self.assertEqual(auth_res.status_code, status.HTTP_200_OK)
        self.assertEqual(auth_res.json()['data']['is_authorized'], 1)

        # 3. Attempting to update authorized PO must fail
        update_res = self.client.put(f'/api/v1/purchase/yarn-pos/{po_id}/', {
            "rate": "300.00"
        }, format='json')
        self.assertEqual(update_res.status_code, status.HTTP_400_BAD_REQUEST)

        # 4. Attempting to delete authorized PO must fail
        del_res = self.client.delete(f'/api/v1/purchase/yarn-pos/{po_id}/')
        self.assertEqual(del_res.status_code, status.HTTP_400_BAD_REQUEST)

        # 5. Unauthorize PO
        unauth_res = self.client.post(f'/api/v1/purchase/yarn-pos/{po_id}/unauthorize/')
        self.assertEqual(unauth_res.status_code, status.HTTP_200_OK)
        self.assertEqual(unauth_res.json()['data']['is_authorized'], 0)

    def test_inward_grn_child_lines_and_atomic_cancellation(self):
        # 1. Create and Authorize PO
        po = YarnPOService.create_yarn_po(
            company_id=self.company.id,
            data={
                "yarn_type": YarnCategory.GREY,
                "party_id": self.supplier.id,
                "mill_id": self.mill.id,
                "yarn_count_id": self.yarn_count.id,
                "bag": 50,
                "per_bag": Decimal("45.360"),
                "rate": Decimal("250.00"),
            },
            user=self.company_admin
        )
        YarnPOService.authorize_yarn_po(po.id, self.company.id, self.company_admin)

        # 2. Create Inward GRN
        inw_res = self.client.post('/api/v1/inventory/yarn-inwards/', {
            "po": po.id,
            "warehouse": self.warehouse.id,
            "dc_number": "DC-101",
            "dc_date": str(timezone.now().date()),
            "lot_no": "LOT-A1",
            "bag": 50,
            "per_bag": "45.360",
            "rate": "250.00"
        }, format='json')
        self.assertEqual(inw_res.status_code, status.HTTP_201_CREATED)
        inw_data = inw_res.json()['data']
        inw_id = inw_data['id']
        self.assertEqual(len(inw_data['line_items']), 1)

        # Verify stock was created and credited
        stock = yarn_stock_table.objects.get(
            company=self.company, warehouse=self.warehouse, lot_no="LOT-A1"
        )
        self.assertEqual(stock.balance_bag, 50)
        self.assertEqual(stock.balance_quantity, Decimal("2268.000"))

        # Verify PO was marked complete
        po.refresh_from_db()
        self.assertEqual(po.is_complete, 1)

        # 3. Cancel Inward (DELETE endpoint)
        del_inw = self.client.delete(f'/api/v1/inventory/yarn-inwards/{inw_id}/')
        self.assertEqual(del_inw.status_code, status.HTTP_204_NO_CONTENT)

        # Verify stock was atomically reversed back to zero
        stock.refresh_from_db()
        self.assertEqual(stock.balance_bag, 0)
        self.assertEqual(stock.balance_quantity, Decimal("0.000"))

        # Verify PO remaining balance restored and is_complete reset to 0
        po.refresh_from_db()
        self.assertEqual(po.is_complete, 0)
        line = po.line_items.first()
        self.assertEqual(line.remaining_bag, 50)

    def test_outward_dispatch_stock_validation_and_cancellation(self):
        # 1. Inward stock directly into warehouse
        inward = YarnInwardService.create_inward(
            company_id=self.company.id,
            data={
                "warehouse_id": self.warehouse.id,
                "party_id": self.supplier.id,
                "mill_id": self.mill.id,
                "yarn_type": YarnCategory.GREY,
                "yarn_count_id": self.yarn_count.id,
                "lot_no": "LOT-OUT-TEST",
                "bag": 20,
                "per_bag": Decimal("45.360"),
                "net_wt": Decimal("907.200"),
                "rate": Decimal("250.00")
            },
            user=self.company_admin
        )

        # 2. Attempt outward exceeding available stock (must fail)
        excess_res = self.client.post('/api/v1/inventory/yarn-outwards/', {
            "outward_type": YarnOutwardTypes.KNITTING,
            "warehouse": self.warehouse.id,
            "destination_party": self.knitter.id,
            "yarn_type": YarnCategory.GREY,
            "yarn_count": self.yarn_count.id,
            "mill": self.mill.id,
            "lot_no": "LOT-OUT-TEST",
            "bag": 30,
            "quantity": "1360.800"
        }, format='json')
        self.assertEqual(excess_res.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Valid outward
        valid_res = self.client.post('/api/v1/inventory/yarn-outwards/', {
            "outward_type": YarnOutwardTypes.KNITTING,
            "warehouse": self.warehouse.id,
            "destination_party": self.knitter.id,
            "yarn_type": YarnCategory.GREY,
            "yarn_count": self.yarn_count.id,
            "mill": self.mill.id,
            "lot_no": "LOT-OUT-TEST",
            "bag": 10,
            "quantity": "453.600"
        }, format='json')
        self.assertEqual(valid_res.status_code, status.HTTP_201_CREATED)
        out_id = valid_res.json()['data']['id']
        self.assertEqual(len(valid_res.json()['data']['line_items']), 1)

        # Verify stock deducted
        stock = yarn_stock_table.objects.get(
            company=self.company, warehouse=self.warehouse, lot_no="LOT-OUT-TEST"
        )
        self.assertEqual(stock.balance_bag, 10)
        self.assertEqual(stock.balance_quantity, Decimal("453.600"))

        # 4. Cancel Outward
        del_out = self.client.delete(f'/api/v1/inventory/yarn-outwards/{out_id}/')
        self.assertEqual(del_out.status_code, status.HTTP_204_NO_CONTENT)

        # Verify stock restored
        stock.refresh_from_db()
        self.assertEqual(stock.balance_bag, 20)
        self.assertEqual(stock.balance_quantity, Decimal("907.200"))

    def test_sales_and_sales_return_flow(self):
        # 1. Put stock in place
        YarnInwardService.create_inward(
            company_id=self.company.id,
            data={
                "warehouse_id": self.warehouse.id,
                "party_id": self.supplier.id,
                "mill_id": self.mill.id,
                "yarn_type": YarnCategory.GREY,
                "yarn_count_id": self.yarn_count.id,
                "lot_no": "LOT-SALES",
                "bag": 20,
                "per_bag": Decimal("45.360"),
                "net_wt": Decimal("907.200"),
                "rate": Decimal("250.00")
            },
            user=self.company_admin
        )

        # 2. Sales invoice
        sal_res = self.client.post('/api/v1/sales/yarn-sales/', {
            "warehouse": self.warehouse.id,
            "customer": self.customer.id,
            "yarn_type": YarnCategory.GREY,
            "yarn_count": self.yarn_count.id,
            "mill": self.mill.id,
            "lot_no": "LOT-SALES",
            "bag": 10,
            "per_bag": "45.360",
            "quantity": "453.600",
            "rate": "300.00"
        }, format='json')
        self.assertEqual(sal_res.status_code, status.HTTP_201_CREATED)
        sal_data = sal_res.json()['data']
        sal_id = sal_data['id']
        self.assertEqual(len(sal_data['line_items']), 1)

        # Stock balance check (20 - 10 = 10)
        stock = yarn_stock_table.objects.get(
            company=self.company, warehouse=self.warehouse, lot_no="LOT-SALES"
        )
        self.assertEqual(stock.balance_bag, 10)

        # 3. Sales Return
        ret_res = self.client.post('/api/v1/sales/yarn-sales-returns/', {
            "sales_invoice": sal_id,
            "warehouse": self.warehouse.id,
            "customer": self.customer.id,
            "yarn_type": YarnCategory.GREY,
            "yarn_count": self.yarn_count.id,
            "mill": self.mill.id,
            "lot_no": "LOT-SALES",
            "bag": 2,
            "quantity": "90.720",
            "rate": "300.00",
            "return_reason": "Excess Yarn"
        }, format='json')
        self.assertEqual(ret_res.status_code, status.HTTP_201_CREATED)
        ret_data = ret_res.json()['data']
        self.assertEqual(len(ret_data['line_items']), 1)

        # Stock balance check (10 + 2 = 12)
        stock.refresh_from_db()
        self.assertEqual(stock.balance_bag, 12)

    def test_quality_program_nested_sizes(self):
        # Create Quality Program with nested sizes
        res = self.client.post('/api/v1/masters/quality-programs/', {
            "quality": "COMBED COTTON INTERLOCK",
            "style": "WOMENS-CREW-01",
            "fabric_id": "FAB-INT-01",
            "sizes": [
                {"size_id": 1, "position": 1, "per_box": 12},
                {"size_id": 2, "position": 2, "per_box": 24},
                {"size_id": 3, "position": 3, "per_box": 12},
            ]
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        data = res.json()
        payload = data.get('data', data)
        self.assertEqual(len(payload['sizes']), 3)

        qp_id = payload['id']
        qp = quality_program_table.objects.get(id=qp_id)
        self.assertEqual(qp.sizes.count(), 3)
