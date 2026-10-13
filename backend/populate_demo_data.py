import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.utils import timezone
from apps.authentication.models import Company, FinancialYear, User
from apps.masters.models import (
    PartyMaster, YarnCountMaster, ColorShadeMaster,
    WarehouseMaster, TaxMaster, quality_program_table, sub_quality_program_table
)
from apps.purchase.services import YarnPOService
from apps.purchase.models import parent_po_table, company_yarn_type_table
from apps.inventory.services import YarnInwardService, YarnOutwardService
from apps.inventory.models import parent_yarn_inward_table, parent_yarn_outward_table, yarn_stock_table
from apps.sales.services import YarnSalesService, YarnSalesReturnService
from apps.sales.models import parent_yarn_sales_table, parent_yarn_sales_return_table
from apps.ledger.models import tl_stock_movement, tm_stage_stock, tl_voucher, tl_voucher_line
from apps.ledger.services import CurrencyLedgerService, StockLedgerService
from core.constants import YarnCategory, YarnOutwardTypes

company = Company.objects.first()
fy = FinancialYear.objects.filter(company=company).first()
admin_user = User.objects.filter(is_superuser=True).first()

# Parties
mill = PartyMaster.objects.get(name='Lakshmi Spinning Mills Ltd')
trader = PartyMaster.objects.filter(party_type='TRADER').first() or PartyMaster.objects.get(name='Sri Yarn Traders')
knitter = PartyMaster.objects.get(name='Annai Knitting Works')
dyer = PartyMaster.objects.get(name='Rainbow Dyeing & Processing Mills')
customer = PartyMaster.objects.get(name='Classic Polo Retail Brands')

# Yarn Counts
count_24s = YarnCountMaster.objects.get(count='24s')
count_30s = YarnCountMaster.objects.get(count='30s')
count_34s = YarnCountMaster.objects.get(count='34s')
count_2_40s = YarnCountMaster.objects.get(count='2/40s')

# Color Shades
shade_navy = ColorShadeMaster.objects.get(shade_code='NVY-002')
shade_melange = ColorShadeMaster.objects.get(shade_code='MEL-003')

# Warehouse
wh_yarn = WarehouseMaster.objects.get(warehouse_code='WH-YARN-01')

# Tax
tax_5 = TaxMaster.objects.filter(company=company, tax_percent=Decimal('5.00'), is_deleted=False).first()

print("================================================================================")
print("   GARMENTS ERP: SEEDING ENTRIES FOR ALL 5 YARN PROCESS TYPES")
print("   (Grey, Dyed, Melange, Blended, Wound across PO, Inward, Outward, Sales, Return)")
print("================================================================================")

# Step 0: Ensure Company Yarn Types are Activated
print("\n--- 0. Activating Company Yarn Process Types ---")
YarnPOService.seed_company_yarn_types(company.id, admin_user)
company_yarn_type_table.objects.filter(
    company=company,
    yarn_type__in=[
        YarnCategory.GREY,
        YarnCategory.DYED,
        YarnCategory.MELANGE,
        YarnCategory.BLENDED,
        YarnCategory.WOUND,
    ]
).update(is_active=True)
for cyt in company_yarn_type_table.objects.filter(company=company, is_active=True):
    print(f"  [Active] {cyt.get_yarn_type_display()} (requires shade: {cyt.requires_color_shade}, blend: {cyt.requires_blend_ratio})")

# Step 1: Quality Programs
print("\n--- 1. Quality Programs ---")
qp1, _ = quality_program_table.objects.get_or_create(
    quality='SUPER COMBED 100% COTTON',
    style='MENS-CREW-NECK-BASIC',
    fabric_id='FAB-SJ-001',
    defaults={'is_active': 1, 'status': 1, 'created_by': 1, 'updated_by': 1}
)
sub_quality_program_table.objects.filter(tm=qp1).delete()
sub_quality_program_table.objects.bulk_create([
    sub_quality_program_table(tm=qp1, size_id=1, position=1, per_box=12, is_active=1, status=1, created_by=1, updated_by=1),
    sub_quality_program_table(tm=qp1, size_id=2, position=2, per_box=24, is_active=1, status=1, created_by=1, updated_by=1),
    sub_quality_program_table(tm=qp1, size_id=3, position=3, per_box=24, is_active=1, status=1, created_by=1, updated_by=1),
    sub_quality_program_table(tm=qp1, size_id=4, position=4, per_box=12, is_active=1, status=1, created_by=1, updated_by=1),
])
print(f"Created: {qp1} with 4 size breakdowns")

qp2, _ = quality_program_table.objects.get_or_create(
    quality='COTTON MODAL BLEND',
    style='POLO-COLLAR-LUXURY',
    fabric_id='FAB-PIQ-002',
    defaults={'is_active': 1, 'status': 1, 'created_by': 1, 'updated_by': 1}
)
sub_quality_program_table.objects.filter(tm=qp2).delete()
sub_quality_program_table.objects.bulk_create([
    sub_quality_program_table(tm=qp2, size_id=2, position=1, per_box=18, is_active=1, status=1, created_by=1, updated_by=1),
    sub_quality_program_table(tm=qp2, size_id=3, position=2, per_box=18, is_active=1, status=1, created_by=1, updated_by=1),
    sub_quality_program_table(tm=qp2, size_id=4, position=3, per_box=18, is_active=1, status=1, created_by=1, updated_by=1),
])
print(f"Created: {qp2} with 3 size breakdowns")

# Clean existing transaction tables
parent_yarn_sales_return_table.objects.filter(company=company).delete()
parent_yarn_sales_table.objects.filter(company=company).delete()
parent_yarn_outward_table.objects.filter(company=company).delete()
parent_yarn_inward_table.objects.filter(company=company).delete()
yarn_stock_table.objects.filter(company=company).delete()
parent_po_table.objects.filter(company=company, po_number__startswith='YPO-').delete()
tl_stock_movement.objects.filter(company=company, stage='YARN').delete()
tm_stage_stock.objects.filter(company=company, stage='YARN').delete()
tl_voucher.objects.filter(company=company, stage__in=['YARN', '']).delete()

# Ensure Parties have Opening Balances configured
trader.opening_balance = Decimal('150000.00') # Cr Payable opening
trader.credit_days = 30
trader.save(update_fields=['opening_balance', 'credit_days'])

customer.opening_balance = Decimal('250000.00') # Dr Receivable opening
customer.credit_days = 45
customer.save(update_fields=['opening_balance', 'credit_days'])

knitter.opening_balance = Decimal('0.00')
knitter.save(update_fields=['opening_balance'])

# ==============================================================================
# 2. YARN PURCHASE ORDERS WITH SPLIT DELIVERY SCHEDULES
# ==============================================================================
print("\n--- 2. Creating Yarn Purchase Orders with Split Deliveries ---")

# PO 1: GREY YARN
po1 = YarnPOService.create_yarn_po(
    company_id=company.id,
    data={
        'po_number': 'YPO-202610-0001',
        'po_date': timezone.now().date(),
        'yarn_type': YarnCategory.GREY,
        'party_id': trader.id,
        'mill_id': mill.id,
        'yarn_count_id': count_30s.id,
        'cfyear_id': fy.id,
        'bag': 100,
        'per_bag': Decimal('45.360'),
        'rate': Decimal('280.00'),
        'discount': Decimal('5.00'),
        'remarks': '100 Bags Grey 30s Combed Yarn for Summer Jersey'
    },
    deliveries_data=[
        {'party_id': knitter.id, 'delivery_date': timezone.now().date(), 'bag': 50, 'bag_wt': Decimal('45.360')},
        {'party_id': wh_yarn.id, 'delivery_date': timezone.now().date(), 'bag': 50, 'bag_wt': Decimal('45.360')},
    ],
    user=admin_user
)
YarnPOService.authorize_yarn_po(po1.id, company.id, admin_user)
print(f"  [PO 1 - GREY]    #{po1.po_number} | Count: 30s | Qty: {po1.quantity} Kg | Total: Rs. {po1.amount} | Deliveries: 2 schedules")

# PO 2: DYED YARN (Requires Color Shade)
po2 = YarnPOService.create_yarn_po(
    company_id=company.id,
    data={
        'po_number': 'YPO-202610-0002',
        'po_date': timezone.now().date(),
        'yarn_type': YarnCategory.DYED,
        'color_shade_id': shade_navy.id,
        'party_id': trader.id,
        'mill_id': mill.id,
        'yarn_count_id': count_34s.id,
        'cfyear_id': fy.id,
        'bag': 50,
        'per_bag': Decimal('50.000'),
        'rate': Decimal('360.00'),
        'discount': Decimal('10.00'),
        'remarks': '50 Bags Navy Blue 34s Cone Dyed Yarn'
    },
    deliveries_data=[
        {'party_id': wh_yarn.id, 'delivery_date': timezone.now().date(), 'bag': 50, 'bag_wt': Decimal('50.000')}
    ],
    user=admin_user
)
YarnPOService.authorize_yarn_po(po2.id, company.id, admin_user)
print(f"  [PO 2 - DYED]    #{po2.po_number} | Count: 34s | Shade: {shade_navy.color_name} | Qty: {po2.quantity} Kg | Total: Rs. {po2.amount}")

# PO 3: MELANGE YARN (Requires Color Shade & Blend Ratio)
po3 = YarnPOService.create_yarn_po(
    company_id=company.id,
    data={
        'po_number': 'YPO-202610-0003',
        'po_date': timezone.now().date(),
        'yarn_type': YarnCategory.MELANGE,
        'color_shade_id': shade_melange.id,
        'blend_ratio': '85/15',
        'party_id': trader.id,
        'mill_id': mill.id,
        'yarn_count_id': count_30s.id,
        'cfyear_id': fy.id,
        'bag': 60,
        'per_bag': Decimal('45.360'),
        'rate': Decimal('320.00'),
        'discount': Decimal('5.00'),
        'remarks': '60 Bags 30s Grey Melange 85/15 Fiber Blend'
    },
    deliveries_data=[
        {'party_id': knitter.id, 'delivery_date': timezone.now().date(), 'bag': 30, 'bag_wt': Decimal('45.360')},
        {'party_id': wh_yarn.id, 'delivery_date': timezone.now().date(), 'bag': 30, 'bag_wt': Decimal('45.360')}
    ],
    user=admin_user
)
YarnPOService.authorize_yarn_po(po3.id, company.id, admin_user)
print(f"  [PO 3 - MELANGE] #{po3.po_number} | Count: 30s | Blend: 85/15 | Shade: {shade_melange.color_name} | Qty: {po3.quantity} Kg | Total: Rs. {po3.amount}")

# PO 4: BLENDED YARN (Requires Blend Ratio)
po4 = YarnPOService.create_yarn_po(
    company_id=company.id,
    data={
        'po_number': 'YPO-202610-0004',
        'po_date': timezone.now().date(),
        'yarn_type': YarnCategory.BLENDED,
        'blend_ratio': '65/35 PC',
        'party_id': trader.id,
        'mill_id': mill.id,
        'yarn_count_id': count_24s.id,
        'cfyear_id': fy.id,
        'bag': 40,
        'per_bag': Decimal('45.360'),
        'rate': Decimal('240.00'),
        'discount': Decimal('0.00'),
        'remarks': '40 Bags 24s 65/35 Poly-Cotton Blended Yarn'
    },
    deliveries_data=[
        {'party_id': wh_yarn.id, 'delivery_date': timezone.now().date(), 'bag': 40, 'bag_wt': Decimal('45.360')}
    ],
    user=admin_user
)
YarnPOService.authorize_yarn_po(po4.id, company.id, admin_user)
print(f"  [PO 4 - BLENDED] #{po4.po_number} | Count: 24s | Blend: 65/35 PC | Qty: {po4.quantity} Kg | Total: Rs. {po4.amount}")

# PO 5: WOUND / DOUBLED YARN (Requires Ply Count & TPI)
po5 = YarnPOService.create_yarn_po(
    company_id=company.id,
    data={
        'po_number': 'YPO-202610-0005',
        'po_date': timezone.now().date(),
        'yarn_type': YarnCategory.WOUND,
        'ply_count': 2,
        'twists_per_inch': Decimal('18.50'),
        'party_id': trader.id,
        'mill_id': mill.id,
        'yarn_count_id': count_2_40s.id,
        'cfyear_id': fy.id,
        'bag': 30,
        'per_bag': Decimal('45.360'),
        'rate': Decimal('350.00'),
        'discount': Decimal('10.00'),
        'remarks': '30 Bags 2/40s Wound TFO Doubled Yarn (18.5 TPI)'
    },
    deliveries_data=[
        {'party_id': wh_yarn.id, 'delivery_date': timezone.now().date(), 'bag': 30, 'bag_wt': Decimal('45.360')}
    ],
    user=admin_user
)
YarnPOService.authorize_yarn_po(po5.id, company.id, admin_user)
print(f"  [PO 5 - WOUND]   #{po5.po_number} | Count: 2/40s | Ply: 2 | TPI: 18.50 | Qty: {po5.quantity} Kg | Total: Rs. {po5.amount}")


# ==============================================================================
# 3. YARN INWARDS (GRN) WITH GST TAX & SPECS MATCHING PO
# ==============================================================================
print("\n--- 3. Posting Yarn Inward Receipts (GRN) against POs ---")

# Inward 1: GREY against PO 1
inw1 = YarnInwardService.create_inward(
    company_id=company.id,
    data={
        'inward_number': 'YIN-202610-0001',
        'inward_date': timezone.now().date(),
        'dc_number': 'DC-LAK-8891',
        'dc_date': timezone.now().date(),
        'vehicle_no': 'TN-38-BZ-4412',
        'po_id': po1.id,
        'warehouse_id': wh_yarn.id,
        'yarn_type': YarnCategory.GREY,
        'yarn_count_id': count_30s.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-30S-01',
        'bag': 100,
        'per_bag': Decimal('45.360'),
        'rate': po1.net_rate,
        'tax_id': tax_5.id if tax_5 else None,
        'remarks': 'Full delivery inwarded from Mill against PO #1'
    },
    user=admin_user
)
print(f"  [Inward 1 - GREY]    #{inw1.inward_number} | Net: {inw1.net_wt} Kg | GST 5%: Rs. {inw1.tax_amount} | Total: Rs. {inw1.total_amount}")

# Inward 2: DYED against PO 2
inw2 = YarnInwardService.create_inward(
    company_id=company.id,
    data={
        'inward_number': 'YIN-202610-0002',
        'inward_date': timezone.now().date(),
        'dc_number': 'DC-LAK-8892',
        'dc_date': timezone.now().date(),
        'vehicle_no': 'TN-38-AX-9910',
        'po_id': po2.id,
        'warehouse_id': wh_yarn.id,
        'yarn_type': YarnCategory.DYED,
        'yarn_count_id': count_34s.id,
        'color_shade_id': shade_navy.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-34D-01',
        'bag': 50,
        'per_bag': Decimal('50.000'),
        'rate': po2.net_rate,
        'tax_id': tax_5.id if tax_5 else None,
        'remarks': 'Dyed Navy Yarn received against PO #2'
    },
    user=admin_user
)
print(f"  [Inward 2 - DYED]    #{inw2.inward_number} | Net: {inw2.net_wt} Kg | GST 5%: Rs. {inw2.tax_amount} | Total: Rs. {inw2.total_amount}")

# Inward 3: MELANGE against PO 3
inw3 = YarnInwardService.create_inward(
    company_id=company.id,
    data={
        'inward_number': 'YIN-202610-0003',
        'inward_date': timezone.now().date(),
        'dc_number': 'DC-LAK-8893',
        'dc_date': timezone.now().date(),
        'vehicle_no': 'TN-38-CD-1122',
        'po_id': po3.id,
        'warehouse_id': wh_yarn.id,
        'yarn_type': YarnCategory.MELANGE,
        'yarn_count_id': count_30s.id,
        'color_shade_id': shade_melange.id,
        'blend_ratio': '85/15',
        'mill_id': mill.id,
        'lot_no': 'LOT-30M-01',
        'bag': 60,
        'per_bag': Decimal('45.360'),
        'rate': po3.net_rate,
        'tax_id': tax_5.id if tax_5 else None,
        'remarks': 'Melange 85/15 yarn received against PO #3'
    },
    user=admin_user
)
print(f"  [Inward 3 - MELANGE] #{inw3.inward_number} | Net: {inw3.net_wt} Kg | GST 5%: Rs. {inw3.tax_amount} | Total: Rs. {inw3.total_amount}")

# Inward 4: BLENDED against PO 4
inw4 = YarnInwardService.create_inward(
    company_id=company.id,
    data={
        'inward_number': 'YIN-202610-0004',
        'inward_date': timezone.now().date(),
        'dc_number': 'DC-LAK-8894',
        'dc_date': timezone.now().date(),
        'vehicle_no': 'TN-38-EF-3344',
        'po_id': po4.id,
        'warehouse_id': wh_yarn.id,
        'yarn_type': YarnCategory.BLENDED,
        'yarn_count_id': count_24s.id,
        'blend_ratio': '65/35 PC',
        'mill_id': mill.id,
        'lot_no': 'LOT-24B-01',
        'bag': 40,
        'per_bag': Decimal('45.360'),
        'rate': po4.net_rate,
        'tax_id': tax_5.id if tax_5 else None,
        'remarks': '65/35 PC Blended yarn received against PO #4'
    },
    user=admin_user
)
print(f"  [Inward 4 - BLENDED] #{inw4.inward_number} | Net: {inw4.net_wt} Kg | GST 5%: Rs. {inw4.tax_amount} | Total: Rs. {inw4.total_amount}")

# Inward 5: WOUND against PO 5
inw5 = YarnInwardService.create_inward(
    company_id=company.id,
    data={
        'inward_number': 'YIN-202610-0005',
        'inward_date': timezone.now().date(),
        'dc_number': 'DC-LAK-8895',
        'dc_date': timezone.now().date(),
        'vehicle_no': 'TN-38-GH-5566',
        'po_id': po5.id,
        'warehouse_id': wh_yarn.id,
        'yarn_type': YarnCategory.WOUND,
        'yarn_count_id': count_2_40s.id,
        'ply_count': 2,
        'twists_per_inch': Decimal('18.50'),
        'mill_id': mill.id,
        'lot_no': 'LOT-240W-01',
        'bag': 30,
        'per_bag': Decimal('45.360'),
        'rate': po5.net_rate,
        'tax_id': tax_5.id if tax_5 else None,
        'remarks': '2/40s Wound 2-ply yarn received against PO #5'
    },
    user=admin_user
)
print(f"  [Inward 5 - WOUND]   #{inw5.inward_number} | Net: {inw5.net_wt} Kg | GST 5%: Rs. {inw5.tax_amount} | Total: Rs. {inw5.total_amount}")


# ==============================================================================
# 4. YARN OUTWARDS (DELIVERY CHALLANS - KNITTING & DYEING DISPATCH)
# ==============================================================================
print("\n--- 4. Issuing Yarn Delivery Challans (Outward to Processors) ---")

# Outward 1: GREY to Knitter
out1 = YarnOutwardService.create_outward(
    company_id=company.id,
    data={
        'outward_number': 'YKNT-202610-0001',
        'outward_date': timezone.now().date(),
        'outward_type': YarnOutwardTypes.KNITTING,
        'warehouse_id': wh_yarn.id,
        'destination_party_id': knitter.id,
        'yarn_type': YarnCategory.GREY,
        'yarn_count_id': count_30s.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-30S-01',
        'bag': 30,
        'quantity': Decimal('1360.800'),
        'vehicle_no': 'TN-38-BZ-4412',
        'driver_name': 'Murugan K',
        'remarks': 'Grey 30s yarn dispatched for Summer Jersey'
    },
    user=admin_user
)
print(f"  [Outward 1 - GREY KNIT]    #{out1.outward_number} | 30 bags (1,360.80 Kg) -> {knitter.name}")

# Outward 2: GREY to Dyer
out2 = YarnOutwardService.create_outward(
    company_id=company.id,
    data={
        'outward_number': 'YDYE-202610-0001',
        'outward_date': timezone.now().date(),
        'outward_type': YarnOutwardTypes.DYEING,
        'warehouse_id': wh_yarn.id,
        'destination_party_id': dyer.id,
        'yarn_type': YarnCategory.GREY,
        'yarn_count_id': count_30s.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-30S-01',
        'bag': 20,
        'quantity': Decimal('907.200'),
        'vehicle_no': 'TN-38-AX-9910',
        'driver_name': 'Ramesh S',
        'remarks': 'Grey 30s yarn dispatched for Cone Dyeing'
    },
    user=admin_user
)
print(f"  [Outward 2 - GREY DYE]     #{out2.outward_number} | 20 bags (907.20 Kg) -> {dyer.name}")

# Outward 3: DYED to Knitter
out3 = YarnOutwardService.create_outward(
    company_id=company.id,
    data={
        'outward_number': 'YKNT-202610-0002',
        'outward_date': timezone.now().date(),
        'outward_type': YarnOutwardTypes.KNITTING,
        'warehouse_id': wh_yarn.id,
        'destination_party_id': knitter.id,
        'yarn_type': YarnCategory.DYED,
        'yarn_count_id': count_34s.id,
        'color_shade_id': shade_navy.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-34D-01',
        'bag': 20,
        'quantity': Decimal('1000.000'),
        'vehicle_no': 'TN-38-CD-1122',
        'driver_name': 'Kannan M',
        'remarks': 'Navy Dyed 34s yarn dispatched for Feeder Stripes'
    },
    user=admin_user
)
print(f"  [Outward 3 - DYED KNIT]    #{out3.outward_number} | 20 bags (1,000.00 Kg) -> {knitter.name}")

# Outward 4: MELANGE to Knitter
out4 = YarnOutwardService.create_outward(
    company_id=company.id,
    data={
        'outward_number': 'YKNT-202610-0003',
        'outward_date': timezone.now().date(),
        'outward_type': YarnOutwardTypes.KNITTING,
        'warehouse_id': wh_yarn.id,
        'destination_party_id': knitter.id,
        'yarn_type': YarnCategory.MELANGE,
        'yarn_count_id': count_30s.id,
        'color_shade_id': shade_melange.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-30M-01',
        'bag': 25,
        'quantity': Decimal('1134.000'),
        'vehicle_no': 'TN-38-EF-3344',
        'driver_name': 'Velu P',
        'remarks': 'Melange 85/15 yarn dispatched for Heather Jersey'
    },
    user=admin_user
)
print(f"  [Outward 4 - MELANGE KNIT] #{out4.outward_number} | 25 bags (1,134.00 Kg) -> {knitter.name}")

# Outward 5: BLENDED to Knitter
out5 = YarnOutwardService.create_outward(
    company_id=company.id,
    data={
        'outward_number': 'YKNT-202610-0004',
        'outward_date': timezone.now().date(),
        'outward_type': YarnOutwardTypes.KNITTING,
        'warehouse_id': wh_yarn.id,
        'destination_party_id': knitter.id,
        'yarn_type': YarnCategory.BLENDED,
        'yarn_count_id': count_24s.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-24B-01',
        'bag': 15,
        'quantity': Decimal('680.400'),
        'vehicle_no': 'TN-38-GH-5566',
        'driver_name': 'Raja S',
        'remarks': '65/35 PC Blended yarn dispatched for Fleece'
    },
    user=admin_user
)
print(f"  [Outward 5 - BLENDED KNIT] #{out5.outward_number} | 15 bags (680.40 Kg) -> {knitter.name}")

# Outward 6: WOUND to Knitter
out6 = YarnOutwardService.create_outward(
    company_id=company.id,
    data={
        'outward_number': 'YKNT-202610-0005',
        'outward_date': timezone.now().date(),
        'outward_type': YarnOutwardTypes.KNITTING,
        'warehouse_id': wh_yarn.id,
        'destination_party_id': knitter.id,
        'yarn_type': YarnCategory.WOUND,
        'yarn_count_id': count_2_40s.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-240W-01',
        'bag': 12,
        'quantity': Decimal('544.320'),
        'vehicle_no': 'TN-38-JK-7788',
        'driver_name': 'Mani T',
        'remarks': '2/40s Wound yarn dispatched for 1x1 Collar Ribs'
    },
    user=admin_user
)
print(f"  [Outward 6 - WOUND KNIT]   #{out6.outward_number} | 12 bags (544.32 Kg) -> {knitter.name}")


# ==============================================================================
# 5. COMMERCIAL YARN SALES & CUSTOMER SALES RETURNS
# ==============================================================================
print("\n--- 5. Commercial Yarn Sales & Customer Sales Returns ---")

# Sales 1: GREY
sal1 = YarnSalesService.create_sales(
    company_id=company.id,
    data={
        'invoice_number': 'YSAL-202610-0001',
        'invoice_date': timezone.now().date(),
        'yarn_type': YarnCategory.GREY,
        'warehouse_id': wh_yarn.id,
        'customer_id': customer.id,
        'yarn_count_id': count_30s.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-30S-01',
        'bag': 10,
        'per_bag': Decimal('45.360'),
        'quantity': Decimal('453.600'),
        'rate': Decimal('295.00'),
        'payment_terms': 'Immediate 15 days',
        'remarks': 'Commercial Grey 30s Sale'
    },
    user=admin_user
)
print(f"  [Sales 1 - GREY]    #{sal1.invoice_number} | 10 bags (453.60 Kg) | Total: Rs. {sal1.total_amount}")

ret1 = YarnSalesReturnService.create_sales_return(
    company_id=company.id,
    data={
        'return_number': 'YSRET-202610-0001',
        'return_date': timezone.now().date(),
        'sales_invoice_id': sal1.id,
        'warehouse_id': wh_yarn.id,
        'customer_id': customer.id,
        'yarn_type': YarnCategory.GREY,
        'yarn_count_id': count_30s.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-30S-01',
        'bag': 2,
        'quantity': Decimal('90.720'),
        'rate': Decimal('295.00'),
        'return_reason': 'Surplus bags returned by customer'
    },
    user=admin_user
)
print(f"    -> [Return 1 - GREY]    #{ret1.return_number} | Re-credited 2 bags (90.72 Kg) into stock")

# Sales 2: DYED
sal2 = YarnSalesService.create_sales(
    company_id=company.id,
    data={
        'invoice_number': 'YSAL-202610-0002',
        'invoice_date': timezone.now().date(),
        'yarn_type': YarnCategory.DYED,
        'warehouse_id': wh_yarn.id,
        'customer_id': customer.id,
        'yarn_count_id': count_34s.id,
        'color_shade_id': shade_navy.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-34D-01',
        'bag': 10,
        'per_bag': Decimal('50.000'),
        'quantity': Decimal('500.000'),
        'rate': Decimal('380.00'),
        'payment_terms': 'Net 30 days',
        'remarks': 'Commercial Navy Dyed 34s Sale'
    },
    user=admin_user
)
print(f"  [Sales 2 - DYED]    #{sal2.invoice_number} | 10 bags (500.00 Kg) | Total: Rs. {sal2.total_amount}")

ret2 = YarnSalesReturnService.create_sales_return(
    company_id=company.id,
    data={
        'return_number': 'YSRET-202610-0002',
        'return_date': timezone.now().date(),
        'sales_invoice_id': sal2.id,
        'warehouse_id': wh_yarn.id,
        'customer_id': customer.id,
        'yarn_type': YarnCategory.DYED,
        'yarn_count_id': count_34s.id,
        'color_shade_id': shade_navy.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-34D-01',
        'bag': 1,
        'quantity': Decimal('50.000'),
        'rate': Decimal('380.00'),
        'return_reason': 'Minor lot variation on 1 bag'
    },
    user=admin_user
)
print(f"    -> [Return 2 - DYED]    #{ret2.return_number} | Re-credited 1 bag (50.00 Kg) into stock")

# Sales 3: MELANGE
sal3 = YarnSalesService.create_sales(
    company_id=company.id,
    data={
        'invoice_number': 'YSAL-202610-0003',
        'invoice_date': timezone.now().date(),
        'yarn_type': YarnCategory.MELANGE,
        'warehouse_id': wh_yarn.id,
        'customer_id': customer.id,
        'yarn_count_id': count_30s.id,
        'color_shade_id': shade_melange.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-30M-01',
        'bag': 10,
        'per_bag': Decimal('45.360'),
        'quantity': Decimal('453.600'),
        'rate': Decimal('340.00'),
        'payment_terms': 'Immediate 15 days',
        'remarks': 'Commercial Melange 85/15 Sale'
    },
    user=admin_user
)
print(f"  [Sales 3 - MELANGE] #{sal3.invoice_number} | 10 bags (453.60 Kg) | Total: Rs. {sal3.total_amount}")

ret3 = YarnSalesReturnService.create_sales_return(
    company_id=company.id,
    data={
        'return_number': 'YSRET-202610-0003',
        'return_date': timezone.now().date(),
        'sales_invoice_id': sal3.id,
        'warehouse_id': wh_yarn.id,
        'customer_id': customer.id,
        'yarn_type': YarnCategory.MELANGE,
        'yarn_count_id': count_30s.id,
        'color_shade_id': shade_melange.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-30M-01',
        'bag': 2,
        'quantity': Decimal('90.720'),
        'rate': Decimal('340.00'),
        'return_reason': 'Surplus melange from customer order'
    },
    user=admin_user
)
print(f"    -> [Return 3 - MELANGE] #{ret3.return_number} | Re-credited 2 bags (90.72 Kg) into stock")

# Sales 4: BLENDED
sal4 = YarnSalesService.create_sales(
    company_id=company.id,
    data={
        'invoice_number': 'YSAL-202610-0004',
        'invoice_date': timezone.now().date(),
        'yarn_type': YarnCategory.BLENDED,
        'warehouse_id': wh_yarn.id,
        'customer_id': customer.id,
        'yarn_count_id': count_24s.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-24B-01',
        'bag': 8,
        'per_bag': Decimal('45.360'),
        'quantity': Decimal('362.880'),
        'rate': Decimal('260.00'),
        'payment_terms': 'Net 30 days',
        'remarks': 'Commercial 65/35 PC Blended Sale'
    },
    user=admin_user
)
print(f"  [Sales 4 - BLENDED] #{sal4.invoice_number} | 8 bags (362.88 Kg) | Total: Rs. {sal4.total_amount}")

ret4 = YarnSalesReturnService.create_sales_return(
    company_id=company.id,
    data={
        'return_number': 'YSRET-202610-0004',
        'return_date': timezone.now().date(),
        'sales_invoice_id': sal4.id,
        'warehouse_id': wh_yarn.id,
        'customer_id': customer.id,
        'yarn_type': YarnCategory.BLENDED,
        'yarn_count_id': count_24s.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-24B-01',
        'bag': 1,
        'quantity': Decimal('45.360'),
        'rate': Decimal('260.00'),
        'return_reason': 'Customer requested 1 bag return'
    },
    user=admin_user
)
print(f"    -> [Return 4 - BLENDED] #{ret4.return_number} | Re-credited 1 bag (45.36 Kg) into stock")

# Sales 5: WOUND
sal5 = YarnSalesService.create_sales(
    company_id=company.id,
    data={
        'invoice_number': 'YSAL-202610-0005',
        'invoice_date': timezone.now().date(),
        'yarn_type': YarnCategory.WOUND,
        'warehouse_id': wh_yarn.id,
        'customer_id': customer.id,
        'yarn_count_id': count_2_40s.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-240W-01',
        'bag': 5,
        'per_bag': Decimal('45.360'),
        'quantity': Decimal('226.800'),
        'rate': Decimal('375.00'),
        'payment_terms': 'Immediate 15 days',
        'remarks': 'Commercial 2/40s Wound 2-ply Sale'
    },
    user=admin_user
)
print(f"  [Sales 5 - WOUND]   #{sal5.invoice_number} | 5 bags (226.80 Kg) | Total: Rs. {sal5.total_amount}")

ret5 = YarnSalesReturnService.create_sales_return(
    company_id=company.id,
    data={
        'return_number': 'YSRET-202610-0005',
        'return_date': timezone.now().date(),
        'sales_invoice_id': sal5.id,
        'warehouse_id': wh_yarn.id,
        'customer_id': customer.id,
        'yarn_type': YarnCategory.WOUND,
        'yarn_count_id': count_2_40s.id,
        'mill_id': mill.id,
        'lot_no': 'LOT-240W-01',
        'bag': 1,
        'quantity': Decimal('45.360'),
        'rate': Decimal('375.00'),
        'return_reason': 'Over-ordered 1 bag returned'
    },
    user=admin_user
)
print(f"    -> [Return 5 - WOUND]   #{ret5.return_number} | Re-credited 1 bag (45.36 Kg) into stock")


# ==============================================================================
# 6. SETTLEMENT: PARTY PAYMENTS & RECEIPTS (TRANSACTION AGAINST REFERENCES)
# ==============================================================================
print("\n--- 6. Recording Party Payments & Receipts against Specific Invoices ---")

# Payment 1: Bank Payment to Supplier (Sri Yarn Traders) against Inward GRN #YIN-202610-0001
pay1 = CurrencyLedgerService.record_party_payment(
    company_id=company.id,
    fy_id=fy.id,
    party_id=trader.id,
    amount=Decimal('800000.00'),
    payment_date=timezone.now().date(),
    payment_mode='BANK',
    reference_no='NEFT-HDFC-88910',
    against_doc_type='INWARD_GRN',
    against_doc_number=inw1.inward_number,
    bank_or_cash_account_code='1001',
    bank_or_cash_account_name='HDFC Bank Current A/c',
    narration=f'Part-payment via NEFT against Yarn Inward GRN #{inw1.inward_number}',
    user=admin_user,
)
print(f"  [Payment 1] #{pay1.voucher_number} | Paid Rs. 8,00,000.00 to {trader.name} against {inw1.inward_number}")

# Payment 2: Bank Payment to Supplier (Sri Yarn Traders) against Inward GRN #YIN-202610-0002
pay2 = CurrencyLedgerService.record_party_payment(
    company_id=company.id,
    fy_id=fy.id,
    party_id=trader.id,
    amount=Decimal('500000.00'),
    payment_date=timezone.now().date(),
    payment_mode='BANK',
    reference_no='RTGS-ICICI-22345',
    against_doc_type='INWARD_GRN',
    against_doc_number=inw2.inward_number,
    bank_or_cash_account_code='1001',
    bank_or_cash_account_name='HDFC Bank Current A/c',
    narration=f'Part-payment via RTGS against Dyed Yarn Inward #{inw2.inward_number}',
    user=admin_user,
)
print(f"  [Payment 2] #{pay2.voucher_number} | Paid Rs. 5,00,000.00 to {trader.name} against {inw2.inward_number}")

# Receipt 1: Customer Receipt from Classic Polo against Sales Invoice #YSAL-202610-0001
rec1 = CurrencyLedgerService.record_party_receipt(
    company_id=company.id,
    fy_id=fy.id,
    party_id=customer.id,
    amount=Decimal('100000.00'),
    receipt_date=timezone.now().date(),
    payment_mode='BANK',
    reference_no='NEFT-SBIN-77621',
    against_doc_type='SALES_INVOICE',
    against_doc_number=sal1.invoice_number,
    bank_or_cash_account_code='1001',
    bank_or_cash_account_name='HDFC Bank Current A/c',
    narration=f'Payment received via NEFT against Sales Invoice #{sal1.invoice_number}',
    user=admin_user,
)
print(f"  [Receipt 1] #{rec1.voucher_number} | Received Rs. 1,00,000.00 from {customer.name} against {sal1.invoice_number}")

# Receipt 2: Customer Receipt from Classic Polo against Sales Invoice #YSAL-202610-0002
rec2 = CurrencyLedgerService.record_party_receipt(
    company_id=company.id,
    fy_id=fy.id,
    party_id=customer.id,
    amount=Decimal('150000.00'),
    receipt_date=timezone.now().date(),
    payment_mode='BANK',
    reference_no='RTGS-AXIS-99120',
    against_doc_type='SALES_INVOICE',
    against_doc_number=sal2.invoice_number,
    bank_or_cash_account_code='1001',
    bank_or_cash_account_name='HDFC Bank Current A/c',
    narration=f'Payment received via RTGS against Sales Invoice #{sal2.invoice_number}',
    user=admin_user,
)
print(f"  [Receipt 2] #{rec2.voucher_number} | Received Rs. 1,50,000.00 from {customer.name} against {sal2.invoice_number}")


# ==============================================================================
# 7. VERIFY & PRINT LIVE YARN GODOWN STOCK LEDGER
# ==============================================================================
print("\n================================================================================")
print("              LIVE YARN GODOWN STOCK LEDGER (tm_yarn_stock)                     ")
print("================================================================================")
stock_qs = yarn_stock_table.objects.filter(company=company).order_by('yarn_type', 'yarn_count__count')
for st in stock_qs:
    shade_str = st.color_shade.color_name if st.color_shade else "RAW / NATURAL"
    print(f"\n[{st.get_yarn_type_display()}] Count: {st.yarn_count.count} | Shade: {shade_str} | Lot: {st.lot_no}")
    print(f"   + Inward GRN:     {st.inward_quantity:>10.3f} Kg  ({st.inward_bag:>3} bags)")
    print(f"   - Outward DC:     {st.outward_quantity:>10.3f} Kg  ({st.outward_bag:>3} bags)")
    print(f"   - Commercial Sale:{st.sales_quantity:>10.3f} Kg  ({st.sales_bag:>3} bags)")
    print(f"   + Sales Return:   {st.sales_return_quantity:>10.3f} Kg  ({st.sales_return_bag:>3} bags)")
    print(f"   -------------------------------------------------")
    print(f"   ===> NET BALANCE: {st.balance_quantity:>10.3f} Kg  ({st.balance_bag:>3} bags)")


# ==============================================================================
# 8. VERIFY & PRINT FINANCIAL PARTY LEDGER STATEMENTS
# ==============================================================================
print("\n================================================================================")
print("           FINANCIAL PARTY LEDGER STATEMENTS (tl_voucher / tl_voucher_line)     ")
print("================================================================================")

# Supplier / Trader Statement
trader_stmt = CurrencyLedgerService.get_party_ledger_statement(company.id, trader.id)
print(f"\n[PARTY LEDGER] Supplier: {trader_stmt['party']['name']} ({trader_stmt['party']['code']})")
print(f"  Opening Balance: INR {trader_stmt['opening_balance']} ({trader_stmt['opening_balance_type']})")
print(f"  Total Debit (Payments): INR {trader_stmt['total_debit']} | Total Credit (Bills): INR {trader_stmt['total_credit']}")
print(f"  ===> CLOSING BALANCE:   INR {trader_stmt['closing_balance']} ({trader_stmt['closing_balance_type']})")
print("  Transactions:")
for tx in trader_stmt['transactions']:
    print(f"    - {tx['voucher_date']} | {tx['voucher_type']:<8} | {tx['voucher_number']} | Agst: {tx['transaction_against']:<26} | Dr: {tx['debit']:>10} | Cr: {tx['credit']:>10} | Bal: {tx['running_balance']:>10}")

# Customer Statement
cust_stmt = CurrencyLedgerService.get_party_ledger_statement(company.id, customer.id)
print(f"\n[PARTY LEDGER] Customer: {cust_stmt['party']['name']} ({cust_stmt['party']['code']})")
print(f"  Opening Balance: INR {cust_stmt['opening_balance']} ({cust_stmt['opening_balance_type']})")
print(f"  Total Debit (Invoices): INR {cust_stmt['total_debit']} | Total Credit (Receipts & Returns): INR {cust_stmt['total_credit']}")
print(f"  ===> CLOSING BALANCE:   INR {cust_stmt['closing_balance']} ({cust_stmt['closing_balance_type']})")
print("  Transactions:")
for tx in cust_stmt['transactions']:
    print(f"    - {tx['voucher_date']} | {tx['voucher_type']:<8} | {tx['voucher_number']} | Agst: {tx['transaction_against']:<30} | Dr: {tx['debit']:>10} | Cr: {tx['credit']:>10} | Bal: {tx['running_balance']:>10}")

print("\n================================================================================")
print("   SUCCESS: Dual Ledgers (Physical Stock + Financial Party) seeded successfully!")
print("================================================================================")
