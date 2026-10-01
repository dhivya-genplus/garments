from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from apps.authentication.models import User, Company, FinancialYear, Role, Privilege
from apps.authentication.services import CompanyService, FinancialYearService, UserService
from apps.masters.models import UnitOfMeasurement, YarnTypeMaster, YarnCountMaster, YarnMaster
from core.constants import UserRoles, ModulePermissions, YarnCategory

class AuthAndMastersTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

        # 1. Super Admin
        self.superadmin = UserService.create_user({
            "email": "sa@test.com",
            "username": "sa_test",
            "password": "Password123!",
            "role": UserRoles.SUPER_ADMIN,
            "is_superadmin": True
        })

        # 2. Company & Company Admin
        self.company = CompanyService.create_company({
            "name": "Test Garments",
            "code": "TG",
        }, creator=self.superadmin)

        self.company_admin = UserService.create_user({
            "email": "ca@test.com",
            "username": "ca_test",
            "password": "Password123!",
            "role": UserRoles.ADMIN_USER,
            "company": self.company,
            "is_company_admin": True
        }, creator=self.superadmin)

        # 3. Company User (Employee)
        self.employee = UserService.create_user({
            "email": "emp@test.com",
            "username": "emp_test",
            "password": "Password123!",
            "role": UserRoles.COMPANY_USER,
            "company": self.company,
            "employee_code": "EMP-999"
        }, creator=self.company_admin)

        # 4. Master Data
        self.uom = UnitOfMeasurement.objects.create(
            company=self.company, code="KGS", name="Kilograms"
        )
        self.yarn_type = YarnTypeMaster.objects.create(
            company=self.company, code="COTTON", name="Cotton"
        )
        self.yarn_count = YarnCountMaster.objects.create(
            company=self.company, count="30s"
        )

    def test_login_and_financial_year_in_response(self):
        response = self.client.post('/api/v1/auth/auth/login/', {
            "email": "ca@test.com",
            "password": "Password123!"
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('access', data['data'])
        self.assertEqual(data['data']['user']['role'], UserRoles.ADMIN_USER)
        self.assertIsNotNone(data['data']['user']['active_financial_year'])

    def test_superadmin_access_to_all_modules(self):
        # Authenticate as Super Admin
        login_res = self.client.post('/api/v1/auth/auth/login/', {
            "email": "sa@test.com",
            "password": "Password123!"
        })
        token = login_res.json()['data']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # 1. Access Companies
        res_comp = self.client.get('/api/v1/administration/companies/')
        self.assertEqual(res_comp.status_code, status.HTTP_200_OK)

        # 2. Access Financial Years
        res_fy = self.client.get('/api/v1/administration/financial-years/')
        self.assertEqual(res_fy.status_code, status.HTTP_200_OK)

        # 3. Access Admin Users
        res_admin = self.client.get('/api/v1/administration/admin-users/')
        self.assertEqual(res_admin.status_code, status.HTTP_200_OK)

        # 4. Access Employees / Company Users
        res_emp = self.client.get('/api/v1/administration/employees/')
        self.assertEqual(res_emp.status_code, status.HTTP_200_OK)

    def test_admin_user_creates_financial_year_and_employee(self):
        # Authenticate as Company Admin
        login_res = self.client.post('/api/v1/auth/auth/login/', {
            "email": "ca@test.com",
            "password": "Password123!"
        })
        token = login_res.json()['data']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Create new Financial Year
        fy_res = self.client.post('/api/v1/administration/financial-years/', {
            "name": "FY 2027-2028",
            "code": "2027-2028",
            "start_date": "2027-04-01",
            "end_date": "2028-03-31",
            "is_current": True
        })
        self.assertEqual(fy_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(fy_res.json()['success'])

        # Create new Employee
        emp_res = self.client.post('/api/v1/administration/employees/', {
            "email": "new_emp@test.com",
            "username": "new_emp",
            "password": "Password123!",
            "employee_code": "EMP-002",
            "department": "Knitting",
            "designation": "Supervisor"
        })
        self.assertEqual(emp_res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(emp_res.json()['success'])
        self.assertEqual(emp_res.json()['data']['role'], UserRoles.COMPANY_USER)

    def test_employee_cannot_manage_companies_or_admin_users(self):
        # Authenticate as Employee
        login_res = self.client.post('/api/v1/auth/auth/login/', {
            "email": "emp@test.com",
            "password": "Password123!"
        })
        token = login_res.json()['data']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

        # Should be forbidden on company creation / admin user endpoint
        res = self.client.get('/api/v1/administration/companies/')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

        res_admin = self.client.get('/api/v1/administration/admin-users/')
        self.assertEqual(res_admin.status_code, status.HTTP_403_FORBIDDEN)
