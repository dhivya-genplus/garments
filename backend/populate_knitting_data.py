import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.utils import timezone
from apps.authentication.models import Company, FinancialYear, User
from apps.masters.models import (
    PartyMaster, YarnCountMaster, ColorShadeMaster,
    WarehouseMaster, UnitOfMeasurement, FabricTypeMaster, FabricMaster
)
from apps.knitting.models import (
    parent_knitting_program_table,
    grey_fabric_stock_table,
    parent_grey_fabric_inward_table,
    parent_grey_fabric_outward_table,
    parent_grey_po_table,
    parent_grey_fabric_sales_table,
    parent_grey_fabric_sales_return_table,
)
from apps.knitting.services import (
    KnittingProgramService,
    GreyFabricStockService,
    GreyFabricInwardService,
    GreyFabricOutwardService,
    GreyPOService,
    GreyFabricSalesService,
    GreyFabricSalesReturnService,
)
from core.constants import (
    PartyTypes, WarehouseTypes, FabricCategory,
    KnittingProgramStatus, GreyFabricInwardSources, GreyFabricOutwardTypes
)

print("================ POPULATING KNITTING & GREY FABRIC DEMO DATA ================")

company = Company.objects.first()
fy = FinancialYear.objects.filter(company=company).first()
admin_user = User.objects.filter(is_superuser=True).first()

if not company or not fy:
    print("Error: Company or Financial Year not found. Please run seed_data first.")
    exit(1)

print(f"Company: {company.name} | Active FY: {fy.name}")

# 1. Master Data Setup
knitter = PartyMaster.objects.filter(party_type=PartyTypes.KNITTING_UNIT).first()
if not knitter:
    knitter = PartyMaster.objects.create(
        company=company,
        party_type=PartyTypes.KNITTING_UNIT,
        code="KNIT-001",
        name="Annai Knitting Works",
        contact_person="M. Ramasamy",
        phone="0421-2478901",
        city="Tirupur",
        state="Tamil Nadu",
    )

dyer = PartyMaster.objects.filter(party_type=PartyTypes.DYEING_UNIT).first()
if not dyer:
    dyer = PartyMaster.objects.create(
        company=company,
        party_type=PartyTypes.DYEING_UNIT,
        code="DYE-001",
        name="Rainbow Dyeing & Processing Mills",
        contact_person="S. Karthik",
        phone="0421-2589012",
        city="Tirupur",
        state="Tamil Nadu",
    )

trader = PartyMaster.objects.filter(party_type=PartyTypes.TRADER).first()
if not trader:
    trader = PartyMaster.objects.create(
        company=company,
        party_type=PartyTypes.TRADER,
        code="TRD-001",
        name="Sri Balaji Fabric Traders",
        contact_person="R. Balaji",
        phone="0421-2690123",
        city="Tirupur",
        state="Tamil Nadu",
    )

customer = PartyMaster.objects.filter(company=company, party_type=PartyTypes.CUSTOMER).first()
if not customer:
    customer = PartyMaster.objects.create(
        company=company,
        party_type=PartyTypes.CUSTOMER,
        code="CUST-001",
        name="Classic Apparel Exports Pvt Ltd",
        contact_person="V. Senthilkumar",
        phone="0421-2789012",
        city="Tirupur",
        state="Tamil Nadu",
    )

wh_grey = WarehouseMaster.objects.filter(warehouse_type=WarehouseTypes.GREY_FABRIC_GODOWN).first()
if not wh_grey:
    wh_grey = WarehouseMaster.objects.create(
        company=company,
        warehouse_code="WH-GREY-01",
        name="Main Grey Fabric Godown",
        warehouse_type=WarehouseTypes.GREY_FABRIC_GODOWN,
        address="124 Palladam Road, Tirupur",
    )

uom_kgs = UnitOfMeasurement.objects.filter(code="KGS").first()
if not uom_kgs:
    uom_kgs = UnitOfMeasurement.objects.create(
        company=company,
        code="KGS",
        name="Kilograms",
    )

count_30s = YarnCountMaster.objects.filter(count="30s").first()
if not count_30s:
    count_30s = YarnCountMaster.objects.create(company=company, count="30s")

count_34s = YarnCountMaster.objects.filter(count="34s").first()
if not count_34s:
    count_34s = YarnCountMaster.objects.create(company=company, count="34s")

ft_sj, _ = FabricTypeMaster.objects.get_or_create(
    company=company,
    code="SJ-01",
    defaults={"name": "Single Jersey 100% Cotton"}
)
ft_rib, _ = FabricTypeMaster.objects.get_or_create(
    company=company,
    code="RIB-01",
    defaults={"name": "1x1 Rib Cotton"}
)
ft_interlock, _ = FabricTypeMaster.objects.get_or_create(
    company=company,
    code="INT-01",
    defaults={"name": "Interlock Premium"}
)

fab_sj, _ = FabricMaster.objects.get_or_create(
    company=company,
    fabric_code="FAB-SJ-30S-GREY",
    defaults={
        "fabric_name": "30s Combed Cotton Single Jersey Grey",
        "fabric_type": ft_sj,
        "category": FabricCategory.GREY,
        "gsm": 160,
        "dia": "24",
        "gauge": "24GG",
        "uom": uom_kgs,
    }
)

fab_rib, _ = FabricMaster.objects.get_or_create(
    company=company,
    fabric_code="FAB-RIB-30S-GREY",
    defaults={
        "fabric_name": "30s 1x1 Rib Cotton Grey",
        "fabric_type": ft_rib,
        "category": FabricCategory.GREY,
        "gsm": 220,
        "dia": "30",
        "gauge": "18GG",
        "uom": uom_kgs,
    }
)

fab_interlock, _ = FabricMaster.objects.get_or_create(
    company=company,
    fabric_code="FAB-INT-34S-GREY",
    defaults={
        "fabric_name": "34s Interlock Cotton Grey",
        "fabric_type": ft_interlock,
        "category": FabricCategory.GREY,
        "gsm": 200,
        "dia": "32",
        "gauge": "28GG",
        "uom": uom_kgs,
    }
)

print(f"Masters verified: Knitter={knitter.name}, Godown={wh_grey.name}")


# 2. Knitting Programs (Job Cards)
print("\n--- 1. Creating Knitting Programs ---")
# Clean up prior demo knitting programs to avoid duplicate numbers
parent_knitting_program_table.objects.filter(company=company, program_number__startswith="KP-DEMO-").delete()

kp1_data = {
    "program_number": "KP-DEMO-202610-0001",
    "program_date": timezone.now().date(),
    "delivery_date": timezone.now().date() + timezone.timedelta(days=7),
    "knitter_id": knitter.id,
    "warehouse_id": wh_grey.id,
    "fabric_id": fab_sj.id,
    "fabric_type_id": ft_sj.id,
    "dia": "24",
    "gauge": "24GG",
    "gsm": 160,
    "loop_length": "2.75",
    "planned_rolls": 60,
    "planned_fabric_quantity": Decimal("1200.000"),
    "expected_loss_percent": Decimal("2.00"),
    "knitting_rate": Decimal("18.50"),
    "remarks": "Priority order for Summer T-Shirts Collection",
    "yarn_lines": [
        {
            "yarn_count_id": count_30s.id,
            "yarn_type": "GREY",
            "blend_ratio_percent": "100.00",
            "planned_quantity": "1224.000",
        }
    ],
}
kp1 = KnittingProgramService.create_program(company.id, fy.id, kp1_data, admin_user)
KnittingProgramService.authorize_program(kp1.id, company.id, admin_user)
print(f"Knitting Program 1: {kp1.program_number} | Planned: {kp1.planned_fabric_quantity} Kg ({kp1.planned_rolls} Rolls) | Req Yarn: {kp1.total_yarn_required} Kg [AUTHORIZED]")

kp2_data = {
    "program_number": "KP-DEMO-202610-0002",
    "program_date": timezone.now().date(),
    "delivery_date": timezone.now().date() + timezone.timedelta(days=10),
    "knitter_id": knitter.id,
    "warehouse_id": wh_grey.id,
    "fabric_id": fab_rib.id,
    "fabric_type_id": ft_rib.id,
    "dia": "30",
    "gauge": "18GG",
    "gsm": 220,
    "loop_length": "2.90",
    "planned_rolls": 25,
    "planned_fabric_quantity": Decimal("500.000"),
    "expected_loss_percent": Decimal("2.50"),
    "knitting_rate": Decimal("22.00"),
    "remarks": "Neck rib and cuff rib batch",
    "yarn_lines": [
        {
            "yarn_count_id": count_30s.id,
            "yarn_type": "GREY",
            "blend_ratio_percent": "100.00",
            "planned_quantity": "512.500",
        }
    ],
}
kp2 = KnittingProgramService.create_program(company.id, fy.id, kp2_data, admin_user)
KnittingProgramService.authorize_program(kp2.id, company.id, admin_user)
print(f"Knitting Program 2: {kp2.program_number} | Planned: {kp2.planned_fabric_quantity} Kg ({kp2.planned_rolls} Rolls) | Req Yarn: {kp2.total_yarn_required} Kg [AUTHORIZED]")

kp3_data = {
    "program_number": "KP-DEMO-202610-0003",
    "program_date": timezone.now().date(),
    "delivery_date": timezone.now().date() + timezone.timedelta(days=14),
    "knitter_id": knitter.id,
    "warehouse_id": wh_grey.id,
    "fabric_id": fab_interlock.id,
    "fabric_type_id": ft_interlock.id,
    "dia": "32",
    "gauge": "28GG",
    "gsm": 200,
    "loop_length": "2.65",
    "planned_rolls": 40,
    "planned_fabric_quantity": Decimal("800.000"),
    "expected_loss_percent": Decimal("1.80"),
    "knitting_rate": Decimal("25.00"),
    "remarks": "Interlock fabric batch - draft stage",
    "yarn_lines": [
        {
            "yarn_count_id": count_34s.id,
            "yarn_type": "GREY",
            "blend_ratio_percent": "100.00",
            "planned_quantity": "814.400",
        }
    ],
}
kp3 = KnittingProgramService.create_program(company.id, fy.id, kp3_data, admin_user)
print(f"Knitting Program 3: {kp3.program_number} | Planned: {kp3.planned_fabric_quantity} Kg ({kp3.planned_rolls} Rolls) [DRAFT]")


# 3. Grey Fabric Inward GRN (Receipt from Knitter & Trader)
print("\n--- 2. Populating Grey Fabric Inward (GRN) ---")
parent_grey_fabric_inward_table.objects.filter(company=company, inward_number__startswith="GFIN-DEMO-").delete()

# Inward Batch 1: First 30 rolls received for Program 1
inw1_rolls = []
for i in range(1, 31):
    inw1_rolls.append({
        "roll_no": f"R-SJ-{i:03d}",
        "gross_wt": "20.800",
        "tare_wt": "0.800",
        "net_wt": "20.000",
        "remarks": "Pass QA"
    })

inw1 = GreyFabricInwardService.post_inward(
    company_id=company.id,
    fy_id=fy.id,
    data={
        "inward_number": "GFIN-DEMO-202610-0001",
        "inward_date": timezone.now().date(),
        "dc_number": "DC-KNT-1011",
        "dc_date": timezone.now().date(),
        "vehicle_no": "TN-39-AB-1234",
        "inward_source": GreyFabricInwardSources.KNITTING,
        "knitting_program_id": kp1.id,
        "party_id": knitter.id,
        "warehouse_id": wh_grey.id,
        "fabric_id": fab_sj.id,
        "fabric_type_id": ft_sj.id,
        "dia": "24",
        "gsm": 160,
        "gauge": "24GG",
        "lot_no": "LOT-SJ-KNT01",
        "total_rolls": 30,
        "gross_wt": Decimal("624.000"),
        "tare_wt": Decimal("24.000"),
        "net_wt": Decimal("600.000"),
        "yarn_consumed_wt": Decimal("612.000"),
        "knitting_rate": Decimal("18.50"),
        "remarks": "Part 1 delivery against Program 1",
        "line_items": inw1_rolls,
    },
    user=admin_user
)
print(f"Grey Inward 1: {inw1.inward_number} | Received: {inw1.total_rolls} Rolls, {inw1.net_wt} Kg | Loss: {inw1.process_loss_wt} Kg ({inw1.process_loss_percent}%) | Charges: INR {inw1.knitting_charges}")

# Inward Batch 2: Second 30 rolls received for Program 1 (Completes Program 1!)
inw2_rolls = []
for i in range(31, 61):
    inw2_rolls.append({
        "roll_no": f"R-SJ-{i:03d}",
        "gross_wt": "20.800",
        "tare_wt": "0.800",
        "net_wt": "20.000",
        "remarks": "Pass QA"
    })

inw2 = GreyFabricInwardService.post_inward(
    company_id=company.id,
    fy_id=fy.id,
    data={
        "inward_number": "GFIN-DEMO-202610-0002",
        "inward_date": timezone.now().date(),
        "dc_number": "DC-KNT-1015",
        "dc_date": timezone.now().date(),
        "vehicle_no": "TN-39-CD-5678",
        "inward_source": GreyFabricInwardSources.KNITTING,
        "knitting_program_id": kp1.id,
        "party_id": knitter.id,
        "warehouse_id": wh_grey.id,
        "fabric_id": fab_sj.id,
        "fabric_type_id": ft_sj.id,
        "dia": "24",
        "gsm": 160,
        "gauge": "24GG",
        "lot_no": "LOT-SJ-KNT01",
        "total_rolls": 30,
        "gross_wt": Decimal("624.000"),
        "tare_wt": Decimal("24.000"),
        "net_wt": Decimal("600.000"),
        "yarn_consumed_wt": Decimal("612.000"),
        "knitting_rate": Decimal("18.50"),
        "remarks": "Part 2 delivery - Order Fulfilled",
        "line_items": inw2_rolls,
    },
    user=admin_user
)
print(f"Grey Inward 2: {inw2.inward_number} | Received: {inw2.total_rolls} Rolls, {inw2.net_wt} Kg | Program 1 Status: {kp1.get_status_display()}")

# Inward Batch 3: Direct Trader Purchase
inw3_rolls = []
for i in range(1, 21):
    inw3_rolls.append({
        "roll_no": f"R-RIB-{i:03d}",
        "gross_wt": "20.500",
        "tare_wt": "0.500",
        "net_wt": "20.000",
        "remarks": "Direct purchase"
    })

inw3 = GreyFabricInwardService.post_inward(
    company_id=company.id,
    fy_id=fy.id,
    data={
        "inward_number": "GFIN-DEMO-202610-0003",
        "inward_date": timezone.now().date(),
        "dc_number": "INV-TRD-4455",
        "dc_date": timezone.now().date(),
        "vehicle_no": "TN-38-EF-9012",
        "inward_source": GreyFabricInwardSources.PURCHASE_PO,
        "party_id": trader.id,
        "warehouse_id": wh_grey.id,
        "fabric_id": fab_rib.id,
        "fabric_type_id": ft_rib.id,
        "dia": "30",
        "gsm": 220,
        "gauge": "18GG",
        "lot_no": "LOT-RIB-TRD01",
        "total_rolls": 20,
        "gross_wt": Decimal("410.000"),
        "tare_wt": Decimal("10.000"),
        "net_wt": Decimal("400.000"),
        "remarks": "Ready Rib fabric purchased from Trader",
        "line_items": inw3_rolls,
    },
    user=admin_user
)
print(f"Grey Inward 3: {inw3.inward_number} | Received from Trader: {inw3.total_rolls} Rolls, {inw3.net_wt} Kg")


# 4. Grey Fabric Outward DC (Dispatched to Dyeing & Return)
print("\n--- 3. Populating Grey Fabric Outward (DC) ---")
parent_grey_fabric_outward_table.objects.filter(company=company, outward_number__startswith="GFOUT-DEMO-").delete()

# Outward 1: 35 rolls (700 Kg) dispatched to Rainbow Dyeing & Processing
outw1_rolls = []
for i in range(1, 36):
    outw1_rolls.append({
        "roll_no": f"R-SJ-{i:03d}",
        "gross_wt": "20.800",
        "net_wt": "20.000",
        "remarks": "Dispatched to Dyeing"
    })

outw1 = GreyFabricOutwardService.post_outward(
    company_id=company.id,
    fy_id=fy.id,
    data={
        "outward_number": "GFOUT-DEMO-202610-0001",
        "outward_date": timezone.now().date(),
        "outward_type": GreyFabricOutwardTypes.DYEING,
        "warehouse_id": wh_grey.id,
        "destination_party_id": dyer.id,
        "fabric_id": fab_sj.id,
        "fabric_type_id": ft_sj.id,
        "dia": "24",
        "gsm": 160,
        "gauge": "24GG",
        "lot_no": "LOT-SJ-KNT01",
        "rolls": 35,
        "quantity": Decimal("700.000"),
        "vehicle_no": "TN-39-DYE-9999",
        "driver_name": "Velusamy",
        "remarks": "Dispatched for Navy Blue & White Dyeing Batch",
        "line_items": outw1_rolls,
    },
    user=admin_user
)
print(f"Grey Outward 1: {outw1.outward_number} -> {dyer.name} | Dispatched: {outw1.rolls} Rolls, {outw1.quantity} Kg [DYEING]")

# Outward 2: 2 rolls (40 Kg) returned back to Knitter due to oil stain/needle cut
outw2_rolls = [
    {"roll_no": "R-SJ-059", "gross_wt": "20.800", "net_wt": "20.000", "remarks": "Needle cut defect"},
    {"roll_no": "R-SJ-060", "gross_wt": "20.800", "net_wt": "20.000", "remarks": "Oil stain on crease"},
]
outw2 = GreyFabricOutwardService.post_outward(
    company_id=company.id,
    fy_id=fy.id,
    data={
        "outward_number": "GFOUT-DEMO-202610-0002",
        "outward_date": timezone.now().date(),
        "outward_type": GreyFabricOutwardTypes.RETURN,
        "warehouse_id": wh_grey.id,
        "destination_party_id": knitter.id,
        "fabric_id": fab_sj.id,
        "fabric_type_id": ft_sj.id,
        "dia": "24",
        "gsm": 160,
        "gauge": "24GG",
        "lot_no": "LOT-SJ-KNT01",
        "rolls": 2,
        "quantity": Decimal("40.000"),
        "vehicle_no": "TN-39-RET-1111",
        "driver_name": "Shanmugam",
        "remarks": "Knitting defect rejection return",
        "line_items": outw2_rolls,
    },
    user=admin_user
)
print(f"Grey Outward 2: {outw2.outward_number} -> {knitter.name} | Returned: {outw2.rolls} Rolls, {outw2.quantity} Kg [RETURN]")


# 5. Grey Fabric Purchase Order (Trader PO)
print("\n--- 4. Populating Grey Fabric Purchase Order (Trader PO) ---")
parent_grey_po_table.objects.filter(company=company, po_number__startswith="GFPO-DEMO-").delete()

po1 = GreyPOService.create_po(
    company_id=company.id,
    fy_id=fy.id,
    data={
        "po_number": "GFPO-DEMO-202610-0001",
        "po_date": timezone.now().date(),
        "delivery_date": timezone.now().date() + timezone.timedelta(days=5),
        "party_id": trader.id,
        "warehouse_id": wh_grey.id,
        "tax_percent": Decimal("5.00"),
        "remarks": "Urgent procurement of Cotton Single Jersey for export run",
        "line_items": [
            {
                "fabric_id": fab_sj.id,
                "fabric_type_id": ft_sj.id,
                "dia": "24",
                "gsm": 160,
                "gauge": "24GG",
                "rolls": 50,
                "quantity": Decimal("1000.000"),
                "rate": Decimal("265.00"),
            }
        ]
    },
    user=admin_user
)
GreyPOService.authorize_po(po1.id, company.id, admin_user)
print(f"Grey PO 1: {po1.po_number} -> {trader.name} | Total: {po1.total_rolls} Rolls, {po1.total_quantity} Kg | INR {po1.total_amount} [AUTHORIZED]")


# 6. Commercial Grey Fabric Sales & Customer Sales Return
print("\n--- 5. Populating Grey Fabric Commercial Sales & Return ---")
parent_grey_fabric_sales_table.objects.filter(company=company, invoice_number__startswith="GFSAL-DEMO-").delete()
parent_grey_fabric_sales_return_table.objects.filter(company=company, return_number__startswith="GFSRET-DEMO-").delete()

sales_rolls = []
for i in range(36, 41):
    sales_rolls.append({
        "roll_no": f"R-SJ-{i:03d}",
        "gross_wt": "20.800",
        "net_wt": "20.000",
        "rate": "240.00",
        "amount": "4800.00",
        "remarks": "Commercial sale to Classic Apparel"
    })

sales1 = GreyFabricSalesService.create_sales_invoice(
    company_id=company.id,
    fy_id=fy.id,
    data={
        "invoice_number": "GFSAL-DEMO-202610-0001",
        "invoice_date": timezone.now().date(),
        "customer_id": customer.id,
        "warehouse_id": wh_grey.id,
        "fabric_id": fab_sj.id,
        "fabric_type_id": ft_sj.id,
        "dia": "24",
        "gsm": 160,
        "gauge": "24GG",
        "lot_no": "LOT-SJ-KNT01",
        "rolls": 5,
        "quantity": Decimal("100.000"),
        "rate": Decimal("240.00"),
        "tax_percent": Decimal("5.00"),
        "payment_terms": "Immediate NEFT / 7 Days",
        "remarks": "Commercial spot sale of excess Grey Single Jersey",
        "line_items": sales_rolls,
    },
    user=admin_user
)
print(f"Grey Sales 1: {sales1.invoice_number} -> {customer.name} | Sold: {sales1.rolls} Rolls, {sales1.quantity} Kg @ INR {sales1.rate}/Kg | Total: INR {sales1.total_amount} [INVOICED]")

# Customer Sales Return: 1 roll returned due to width / GSM tolerance issue
return_rolls = [
    {
        "roll_no": "R-SJ-040",
        "gross_wt": "20.800",
        "net_wt": "20.000",
        "rate": "240.00",
        "amount": "4800.00",
        "remarks": "Rejection return - GSM variation"
    }
]
ret1 = GreyFabricSalesReturnService.create_sales_return(
    company_id=company.id,
    fy_id=fy.id,
    data={
        "return_number": "GFSRET-DEMO-202610-0001",
        "return_date": timezone.now().date(),
        "sales_invoice_id": sales1.id,
        "customer_id": customer.id,
        "warehouse_id": wh_grey.id,
        "fabric_id": fab_sj.id,
        "fabric_type_id": ft_sj.id,
        "dia": "24",
        "gsm": 160,
        "gauge": "24GG",
        "lot_no": "LOT-SJ-KNT01",
        "rolls": 1,
        "quantity": Decimal("20.000"),
        "rate": Decimal("240.00"),
        "tax_percent": Decimal("5.00"),
        "return_reason": "GSM variation beyond permissible +/- 5% tolerance",
        "remarks": "Received back into godown and re-credited to stock",
        "line_items": return_rolls,
    },
    user=admin_user
)
print(f"Grey Return 1: {ret1.return_number} <- {customer.name} | Returned: {ret1.rolls} Rolls, {ret1.quantity} Kg | Credit: INR {ret1.total_amount} [RESTOCKED]")


# 7. Live Grey Fabric Stock Summary
print("\n================ LIVE GREY FABRIC STOCK LEDGER ================")
for st in grey_fabric_stock_table.objects.filter(company=company):
    print(f"[{st.fabric.fabric_name}] Dia: {st.dia} | GSM: {st.gsm} | Gauge: {st.gauge} | Lot: {st.lot_no}")
    print(f"  + Inward:         {st.inward_quantity} Kg ({st.inward_rolls} rolls)")
    print(f"  - Outward:        {st.outward_quantity} Kg ({st.outward_rolls} rolls) [Dyeing & Knitter Return]")
    print(f"  - Comm. Sales:    {st.sales_quantity} Kg ({st.sales_rolls} rolls) [Direct Buyer Sale]")
    print(f"  + Sales Return:   {st.sales_return_quantity} Kg ({st.sales_return_rolls} rolls) [Customer Return]")
    print(f"  ===> LIVE BALANCE: {st.balance_quantity} Kg ({st.balance_rolls} rolls)\n")

print("================ DEMO DATA POPULATION COMPLETED SUCCESSFULLY ================")
