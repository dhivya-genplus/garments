from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import User, Company
from apps.authentication.services import CompanyService, UserService
from apps.masters.models import UnitOfMeasurement, YarnCountMaster, ColorShadeMaster, YarnMaster
from core.constants import UserRoles, YarnCategory

class YarnMasterAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Super Admin
        self.superadmin = UserService.create_user({
            "email": "sa_yarn@test.com",
            "username": "sa_yarn",
            "password": "Password123!",
            "role": UserRoles.SUPER_ADMIN,
            "is_superadmin": True
        })

        # 2. Company & Company Admin
        self.company = CompanyService.create_company({
            "name": "Yarn Test Mills",
            "code": "YTM",
        }, creator=self.superadmin)

        self.company_admin = UserService.create_user({
            "email": "ca_yarn@test.com",
            "username": "ca_yarn",
            "password": "Password123!",
            "role": UserRoles.ADMIN_USER,
            "company": self.company,
            "is_company_admin": True
        }, creator=self.superadmin)

        # 3. Supporting Master records
        self.uom = UnitOfMeasurement.objects.create(
            company=self.company, code="KGS", name="Kilograms"
        )
        self.count_30s = YarnCountMaster.objects.create(
            company=self.company, count="30s", description="30s count"
        )
        self.count_40s = YarnCountMaster.objects.create(
            company=self.company, count="40s", description="40s count"
        )
        self.shade_navy = ColorShadeMaster.objects.create(
            company=self.company, shade_code="NVY-01", color_name="Navy Blue"
        )

        # 4. Existing Yarn record
        self.yarn_grey = YarnMaster.objects.create(
            company=self.company,
            yarn_code="YRN-30S-COT-GRY",
            yarn_count=self.count_30s,
            category=YarnCategory.GREY,
            uom=self.uom,
            hsn_code="5205",
            reorder_level=500.0,
            description="30s Grey Cotton Yarn"
        )

        self.client.force_authenticate(user=self.company_admin)

    def test_list_yarns(self):
        res = self.client.get("/api/v1/masters/yarns/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        body = res.json()
        self.assertTrue(body["success"])
        items = body["data"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["yarn_code"], "YRN-30S-COT-GRY")

    def test_filter_yarns_by_category_and_alias(self):
        # Create a second dyed yarn
        YarnMaster.objects.create(
            company=self.company,
            yarn_code="YRN-30S-COT-NVY",
            yarn_count=self.count_30s,
            category=YarnCategory.DYED,
            color_shade=self.shade_navy,
            uom=self.uom
        )

        # Filter by category
        res_cat = self.client.get("/api/v1/masters/yarns/?category=GREY")
        self.assertEqual(res_cat.status_code, status.HTTP_200_OK)
        items_cat = res_cat.json()["data"]
        self.assertEqual(len(items_cat), 1)
        self.assertEqual(items_cat[0]["category"], YarnCategory.GREY)

        # Filter by alias yarn_type
        res_alias = self.client.get("/api/v1/masters/yarns/?yarn_type=DYED")
        self.assertEqual(res_alias.status_code, status.HTTP_200_OK)
        items_alias = res_alias.json()["data"]
        self.assertEqual(len(items_alias), 1)
        self.assertEqual(items_alias[0]["category"], YarnCategory.DYED)

    def test_search_yarns(self):
        res = self.client.get("/api/v1/masters/yarns/?search=30s")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        items = res.json()["data"]
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["yarn_code"], "YRN-30S-COT-GRY")

    def test_create_grey_yarn(self):
        payload = {
            "yarn_code": "YRN-40S-COT-GRY",
            "yarn_count": self.count_40s.id,
            "category": YarnCategory.GREY,
            "uom": self.uom.id,
            "hsn_code": "5205",
            "reorder_level": "750.00",
            "description": "40s Grey Cotton Yarn",
            "is_active": True
        }
        res = self.client.post("/api/v1/masters/yarns/", payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.json()["data"]["yarn_code"], "YRN-40S-COT-GRY")
        self.assertTrue(YarnMaster.objects.filter(company=self.company, yarn_code="YRN-40S-COT-GRY").exists())

    def test_create_dyed_yarn_requires_color_shade(self):
        # Attempt to create dyed yarn without color_shade -> must fail
        payload = {
            "yarn_code": "YRN-30S-COT-DYED-FAIL",
            "yarn_count": self.count_30s.id,
            "category": YarnCategory.DYED,
            "uom": self.uom.id,
        }
        res = self.client.post("/api/v1/masters/yarns/", payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # Provide color_shade -> must succeed
        payload["color_shade"] = self.shade_navy.id
        res_ok = self.client.post("/api/v1/masters/yarns/", payload)
        self.assertEqual(res_ok.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_ok.json()["data"]["category"], YarnCategory.DYED)

    def test_retrieve_and_update_yarn(self):
        # Retrieve
        res_get = self.client.get(f"/api/v1/masters/yarns/{self.yarn_grey.id}/")
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get.json()["data"]["yarn_code"], "YRN-30S-COT-GRY")

        # Partial update (PATCH)
        res_patch = self.client.patch(
            f"/api/v1/masters/yarns/{self.yarn_grey.id}/",
            {"description": "Updated Description"}
        )
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        self.yarn_grey.refresh_from_db()
        self.assertEqual(self.yarn_grey.description, "Updated Description")

    def test_soft_delete_yarn(self):
        res = self.client.delete(f"/api/v1/masters/yarns/{self.yarn_grey.id}/")
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        self.yarn_grey.refresh_from_db()
        self.assertTrue(self.yarn_grey.is_deleted)

        # List must now exclude the soft-deleted yarn
        res_list = self.client.get("/api/v1/masters/yarns/")
        self.assertEqual(len(res_list.json()["data"]), 0)
