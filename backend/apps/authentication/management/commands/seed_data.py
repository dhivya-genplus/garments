from datetime import date
from django.core.management.base import BaseCommand
from apps.authentication.models import User, Company, FinancialYear, Role, Privilege
from apps.authentication.services import CompanyService, FinancialYearService, UserService
from apps.masters.models import (
    UnitOfMeasurement, PartyMaster, YarnCountMaster, YarnTypeMaster,
    ColorShadeMaster, YarnMaster, FabricTypeMaster, FabricMaster,
    ProcessMaster, WarehouseMaster
)
from core.constants import (
    UserRoles, PartyTypes, YarnCategory, FabricCategory,
    ProcessTypes, WarehouseTypes
)

class Command(BaseCommand):
    help = 'Seeds initial superadmin, company, financial years, admin user, company users/employees, and garment master data.'

    def handle(self, *args, **options):
        self.stdout.write("Starting database seeding...")

        # 1. Super Admin (Global System Admin)
        super_admin_email = "superadmin@gmail.com"
        superadmin = User.objects.filter(email=super_admin_email).first() or User.objects.filter(username="superadmin").first()
        if not superadmin:
            superadmin = UserService.create_user({
                "email": super_admin_email,
                "username": "superadmin",
                "password": "123456",
                "first_name": "Super",
                "last_name": "Admin",
                "role": UserRoles.SUPER_ADMIN,
                "is_superadmin": True,
            })
            self.stdout.write(self.style.SUCCESS(f"Created Super Admin: {super_admin_email} / 123456"))
        else:
            superadmin.email = super_admin_email
            superadmin.username = "superadmin"
            superadmin.set_password("123456")
            superadmin.is_superadmin = True
            superadmin.role = UserRoles.SUPER_ADMIN
            superadmin.save()
            self.stdout.write(self.style.SUCCESS(f"Updated Super Admin: {super_admin_email} / 123456"))

        # 2. Demo Company
        company_code = "APEX"
        company = Company.objects.filter(code=company_code).first()
        if not company:
            company = CompanyService.create_company({
                "name": "Apex Garments & Textiles Ltd",
                "code": company_code,
                "legal_name": "Apex Garments Private Limited",
                "gst_number": "33AAACA1234A1Z5",
                "pan_number": "AAACA1234A",
                "email": "contact@apexgarments.com",
                "phone": "+91 9876543210",
                "city": "Tirupur",
                "state": "Tamil Nadu",
                "pincode": "641601",
                "address_line1": "123, Avinashi Road, Tirupur",
            }, creator=superadmin)
            self.stdout.write(self.style.SUCCESS(f"Created Company: {company.name} ({company.code})"))
        else:
            self.stdout.write(f"Company already exists: {company.name}")

        # 3. Additional Financial Year for Company
        past_fy_code = "2024-2025"
        if not FinancialYear.objects.filter(company=company, code=past_fy_code).exists():
            FinancialYear.objects.create(
                company=company,
                name=f"FY {past_fy_code}",
                code=past_fy_code,
                start_date=date(2024, 4, 1),
                end_date=date(2025, 3, 31),
                is_current=False,
                is_closed=True,
                created_by=superadmin
            )
            self.stdout.write(self.style.SUCCESS(f"Created Past FY: {past_fy_code}"))

        # 4. Admin User (Company Admin)
        admin_email = "admin@gmail.com"
        admin_role = Role.objects.filter(company=company, code="ADMIN").first()
        company_admin = User.objects.filter(email=admin_email).first() or User.objects.filter(username="company_admin").first() or User.objects.filter(username="apex_admin").first()
        if not company_admin:
            company_admin = UserService.create_user({
                "email": admin_email,
                "username": "company_admin",
                "password": "123456",
                "first_name": "Company",
                "last_name": "Admin",
                "designation": "General Manager",
                "role": UserRoles.ADMIN_USER,
                "company": company,
                "custom_role_id": admin_role.id if admin_role else None,
                "is_company_admin": True,
            }, creator=superadmin)
            self.stdout.write(self.style.SUCCESS(f"Created Admin User: {admin_email} / 123456"))
        else:
            company_admin.email = admin_email
            company_admin.username = "company_admin"
            company_admin.company = company
            company_admin.role = UserRoles.ADMIN_USER
            company_admin.is_company_admin = True
            company_admin.custom_role = admin_role
            company_admin.set_password("123456")
            company_admin.save()
            self.stdout.write(self.style.SUCCESS(f"Updated Admin User: {admin_email} / 123456"))

        # 5. Company User / Employee
        employee_email = "employee@gmail.com"
        op_role = Role.objects.filter(company=company, code="OPERATOR").first()
        employee = User.objects.filter(email=employee_email).first() or User.objects.filter(username="employee_user").first() or User.objects.filter(username="apex_operator").first()
        if not employee:
            employee = UserService.create_user({
                "email": employee_email,
                "username": "employee_user",
                "password": "123456",
                "first_name": "Company",
                "last_name": "Employee",
                "employee_code": "EMP-001",
                "department": "Yarn & Knitting Production",
                "designation": "Master Data Entry Operator",
                "role": UserRoles.COMPANY_USER,
                "company": company,
                "custom_role_id": op_role.id if op_role else None,
            }, creator=company_admin)
            self.stdout.write(self.style.SUCCESS(f"Created Employee User: {employee_email} / 123456"))
        else:
            employee.email = employee_email
            employee.username = "employee_user"
            employee.company = company
            employee.role = UserRoles.COMPANY_USER
            employee.custom_role = op_role
            employee.set_password("123456")
            employee.save()
            self.stdout.write(self.style.SUCCESS(f"Updated Employee User: {employee_email} / 123456"))

        # 6. Masters Data
        uom_data = [
            {"code": "KGS", "name": "Kilograms", "symbol": "kg"},
            {"code": "MTR", "name": "Meters", "symbol": "m"},
            {"code": "BAG", "name": "Bags", "symbol": "bag"},
            {"code": "ROLL", "name": "Rolls", "symbol": "roll"},
            {"code": "PCS", "name": "Pieces", "symbol": "pcs"},
        ]
        uom_map = {}
        for u in uom_data:
            obj, _ = UnitOfMeasurement.objects.get_or_create(
                company=company, code=u["code"],
                defaults={"name": u["name"], "symbol": u["symbol"], "created_by": company_admin}
            )
            uom_map[u["code"]] = obj

        count_data = ["30s", "34s", "40s", "24s", "2/40s"]
        count_map = {}
        for c in count_data:
            obj, _ = YarnCountMaster.objects.get_or_create(
                company=company, count=c,
                defaults={"description": f"{c} Combed/Carded yarn count", "created_by": company_admin}
            )
            count_map[c] = obj

        type_data = [
            {"code": "COMBED_COTTON", "name": "100% Combed Cotton"},
            {"code": "CARDED_COTTON", "name": "100% Carded Cotton"},
            {"code": "PC_BLEND", "name": "65/35 Poly Cotton Blend"},
            {"code": "VISCOSE", "name": "100% Viscose"},
        ]
        type_map = {}
        for t in type_data:
            obj, _ = YarnTypeMaster.objects.get_or_create(
                company=company, code=t["code"],
                defaults={"name": t["name"], "created_by": company_admin}
            )
            type_map[t["code"]] = obj

        color_data = [
            {"shade_code": "WHT-001", "color_name": "Bleached White", "hex_code": "#FFFFFF"},
            {"shade_code": "BLK-001", "color_name": "Jet Black", "hex_code": "#000000"},
            {"shade_code": "NVY-002", "color_name": "Navy Blue", "hex_code": "#000080"},
            {"shade_code": "MEL-003", "color_name": "Grey Melange", "hex_code": "#808080"},
            {"shade_code": "RED-004", "color_name": "Crimson Red", "hex_code": "#DC143C"},
        ]
        color_map = {}
        for col in color_data:
            obj, _ = ColorShadeMaster.objects.get_or_create(
                company=company, shade_code=col["shade_code"],
                defaults={"color_name": col["color_name"], "hex_code": col["hex_code"], "created_by": company_admin}
            )
            color_map[col["shade_code"]] = obj

        yarn_grey, _ = YarnMaster.objects.get_or_create(
            company=company, yarn_code="YRN-30S-COT-GRY",
            defaults={
                "yarn_type": type_map["COMBED_COTTON"],
                "yarn_count": count_map["30s"],
                "category": YarnCategory.GREY,
                "uom": uom_map["KGS"],
                "hsn_code": "5205",
                "reorder_level": 500,
                "description": "30s Combed Cotton Grey Yarn for Knitting",
                "created_by": company_admin
            }
        )

        yarn_dyed, _ = YarnMaster.objects.get_or_create(
            company=company, yarn_code="YRN-30S-COT-NVY",
            defaults={
                "yarn_type": type_map["COMBED_COTTON"],
                "yarn_count": count_map["30s"],
                "category": YarnCategory.DYED,
                "color_shade": color_map["NVY-002"],
                "uom": uom_map["KGS"],
                "hsn_code": "5205",
                "reorder_level": 300,
                "description": "30s Combed Cotton Dyed Yarn - Navy Blue",
                "created_by": company_admin
            }
        )

        fab_types = [
            {"code": "SJ", "name": "Single Jersey"},
            {"code": "RIB", "name": "1x1 Rib"},
            {"code": "INTERLOCK", "name": "Interlock"},
            {"code": "FLEECE", "name": "2-Thread Fleece"},
        ]
        fab_type_map = {}
        for ft in fab_types:
            obj, _ = FabricTypeMaster.objects.get_or_create(
                company=company, code=ft["code"],
                defaults={"name": ft["name"], "created_by": company_admin}
            )
            fab_type_map[ft["code"]] = obj

        fabric_grey, _ = FabricMaster.objects.get_or_create(
            company=company, fabric_code="FAB-SJ-30S-GRY",
            defaults={
                "fabric_name": "Single Jersey 30s Cotton Grey Fabric",
                "fabric_type": fab_type_map["SJ"],
                "category": FabricCategory.GREY,
                "yarn": yarn_grey,
                "gsm": 160,
                "dia": '30" Tubular',
                "gauge": "24 GG",
                "uom": uom_map["KGS"],
                "hsn_code": "6006",
                "min_stock_alert": 200,
                "created_by": company_admin
            }
        )

        fabric_dyed, _ = FabricMaster.objects.get_or_create(
            company=company, fabric_code="FAB-SJ-30S-NVY",
            defaults={
                "fabric_name": "Single Jersey 30s Cotton Dyed Fabric - Navy Blue",
                "fabric_type": fab_type_map["SJ"],
                "category": FabricCategory.DYED,
                "yarn": yarn_dyed,
                "color_shade": color_map["NVY-002"],
                "gsm": 160,
                "dia": '30" Tubular',
                "gauge": "24 GG",
                "uom": uom_map["KGS"],
                "hsn_code": "6006",
                "min_stock_alert": 100,
                "created_by": company_admin
            }
        )

        processes = [
            {"code": "KNIT-01", "name": "Knitting Process", "type": ProcessTypes.KNITTING, "loss": 1.5, "rate": 15.0},
            {"code": "DYE-01", "name": "Cotton Reactive Dyeing", "type": ProcessTypes.DYEING, "loss": 3.0, "rate": 65.0},
            {"code": "COMP-01", "name": "Felt Compacting", "type": ProcessTypes.COMPACTING, "loss": 0.5, "rate": 10.0},
            {"code": "PRINT-01", "name": "Rotary Screen Printing", "type": ProcessTypes.PRINTING, "loss": 2.0, "rate": 45.0},
        ]
        for p in processes:
            ProcessMaster.objects.get_or_create(
                company=company, process_code=p["code"],
                defaults={
                    "process_name": p["name"],
                    "process_type": p["type"],
                    "default_loss_percentage": p["loss"],
                    "standard_rate_per_kg": p["rate"],
                    "created_by": company_admin
                }
            )

        warehouses = [
            {"code": "WH-YARN-01", "name": "Main Yarn Warehouse", "type": WarehouseTypes.YARN_GODOWN},
            {"code": "WH-GREY-01", "name": "Grey Fabric Godown", "type": WarehouseTypes.GREY_FABRIC_GODOWN},
            {"code": "WH-DYED-01", "name": "Dyed Fabric Godown", "type": WarehouseTypes.DYED_FABRIC_GODOWN},
        ]
        for wh in warehouses:
            WarehouseMaster.objects.get_or_create(
                company=company, warehouse_code=wh["code"],
                defaults={"name": wh["name"], "warehouse_type": wh["type"], "created_by": company_admin}
            )

        parties = [
            {"code": "MILL-001", "name": "Lakshmi Spinning Mills Ltd", "type": PartyTypes.MILL, "city": "Coimbatore", "phone": "0422-223344"},
            {"code": "TRD-001", "name": "Sri Balaji Yarn Traders", "type": PartyTypes.TRADER, "city": "Tirupur", "phone": "0421-224466"},
            {"code": "KNIT-001", "name": "Annai Knitting Works", "type": PartyTypes.KNITTING_UNIT, "city": "Tirupur", "phone": "0421-235577"},
            {"code": "DYE-001", "name": "Rainbow Dyeing & Processing Mills", "type": PartyTypes.DYEING_UNIT, "city": "Perundurai", "phone": "04294-223311"},
            {"code": "CUST-001", "name": "Classic Polo Retail Brands", "type": PartyTypes.CUSTOMER, "city": "Chennai", "phone": "044-245678"},
        ]
        for pt in parties:
            PartyMaster.objects.get_or_create(
                company=company, code=pt["code"],
                defaults={
                    "name": pt["name"],
                    "party_type": pt["type"],
                    "city": pt["city"],
                    "phone": pt["phone"],
                    "credit_days": 30,
                    "created_by": company_admin
                }
            )

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
