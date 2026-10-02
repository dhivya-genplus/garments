import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.utils import timezone
from apps.authentication.models import Company, FinancialYear, User
from apps.masters.models import (
    PartyMaster, YarnCountMaster, YarnTypeMaster, ColorShadeMaster,
    WarehouseMaster, quality_program_table, sub_quality_program_table
)
from apps.purchase.services import YarnPOService
from apps.purchase.models import parent_po_table
from apps.inventory.services import YarnInwardService, YarnOutwardService
from apps.inventory.models import yarn_stock_table
from apps.sales.services import YarnSalesService, YarnSalesReturnService
from core.constants import YarnCategory, YarnOutwardTypes

company = Company.objects.first()
fy = FinancialYear.objects.filter(company=company).first()
admin_user = User.objects.filter(is_superuser=True).first()

mill = PartyMaster.objects.get(name='Lakshmi Spinning Mills Ltd')
trader = PartyMaster.objects.filter(party_type='TRADER').first() or PartyMaster.objects.get(name='Sri Yarn Traders')
knitter = PartyMaster.objects.get(name='Annai Knitting Works')
dyer = PartyMaster.objects.get(name='Rainbow Dyeing & Processing Mills')
customer = PartyMaster.objects.get(name='Classic Polo Retail Brands')

count_30s = YarnCountMaster.objects.get(count='30s')
count_34s = YarnCountMaster.objects.get(count='34s')
shade_navy = ColorShadeMaster.objects.get(shade_code='NVY-002')
shade_white = ColorShadeMaster.objects.get(shade_code='WHT-001')
wh_yarn = WarehouseMaster.objects.get(warehouse_code='WH-YARN-01')

print("--- 1. Populating Masters: Quality Programs ---")
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

print("\n--- 2. Populating Yarn Purchase Orders (Grey & Dyed) ---")
from apps.inventory.models import parent_yarn_inward_table, parent_yarn_outward_table
from apps.sales.models import parent_yarn_sales_table, parent_yarn_sales_return_table
parent_yarn_sales_return_table.objects.all().delete()
parent_yarn_sales_table.objects.all().delete()
parent_yarn_outward_table.objects.all().delete()
parent_yarn_inward_table.objects.all().delete()
yarn_stock_table.objects.all().delete()
parent_po_table.objects.filter(po_number__startswith='YPO-').delete()

# PO 1: Grey Yarn PO
po_grey_num = 'YPO-202610-0001'
po1 = YarnPOService.create_yarn_po(
    company_id=company.id,
    data={
        'po_number': po_grey_num,
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
        'remarks': 'Grey Yarn for Summer Collection Knitting'
    },
    deliveries_data=[
        {'party_id': knitter.id, 'delivery_date': timezone.now().date(), 'bag': 50, 'bag_wt': Decimal('45.360')},
        {'party_id': wh_yarn.id, 'delivery_date': timezone.now().date(), 'bag': 50, 'bag_wt': Decimal('45.360')},
    ],
    user=admin_user
)
YarnPOService.authorize_yarn_po(po1.id, company.id, admin_user)
print(f"PO 1: {po1.po_number} | {po1.get_yarn_type_display()} | Qty: {po1.quantity} Kg | Net Rate: Rs.{po1.net_rate} | Total: Rs.{po1.amount}")

# PO 2: Dyed Yarn PO
po_dyed_num = 'YPO-202610-0002'
parent_po_table.objects.filter(po_number=po_dyed_num).delete()
po2 = YarnPOService.create_yarn_po(
    company_id=company.id,
    data={
        'po_number': po_dyed_num,
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
        'remarks': 'Navy Blue Dyed Yarn for Collar Knitting'
    },
    deliveries_data=[
        {'party_id': wh_yarn.id, 'delivery_date': timezone.now().date(), 'bag': 50, 'bag_wt': Decimal('50.000')}
    ],
    user=admin_user
)
YarnPOService.authorize_yarn_po(po2.id, company.id, admin_user)
print(f"PO 2: {po2.po_number} | {po2.get_yarn_type_display()} ({po2.color_shade.color_name}) | Qty: {po2.quantity} Kg | Net Rate: Rs.{po2.net_rate} | Total: Rs.{po2.amount}")

print("\n--- 3. Populating Yarn Inward (GRN from POs) ---")
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
        'remarks': 'Full delivery inwarded from Mill'
    },
    user=admin_user
)
print(f"Inward 1: {inw1.inward_number} | Received: {inw1.net_wt} Kg against PO #{po1.po_number}")

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
        'remarks': 'Dyed Navy Yarn inwarded from Mill'
    },
    user=admin_user
)
print(f"Inward 2: {inw2.inward_number} | Received: {inw2.net_wt} Kg against PO #{po2.po_number}")

print("\n--- 4. Populating Yarn Outward (Knitting & Dyeing) ---")
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
        'remarks': 'Dispatched for Knitting Job Work'
    },
    user=admin_user
)
print(f"Outward 1: {out1.outward_number} | {out1.get_outward_type_display()} | Qty: {out1.quantity} Kg -> {out1.destination_party.name}")

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
        'remarks': 'Dispatched Grey Yarn for Dyeing Process'
    },
    user=admin_user
)
print(f"Outward 2: {out2.outward_number} | {out2.get_outward_type_display()} | Qty: {out2.quantity} Kg -> {out2.destination_party.name}")

print("\n--- 5. Populating Yarn Sales & Sales Returns ---")
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
        'remarks': 'Direct Grey Yarn Sale'
    },
    user=admin_user
)
print(f"Sales 1: {sal1.invoice_number} | {sal1.get_yarn_type_display()} | Qty: {sal1.quantity} Kg | Total: Rs.{sal1.total_amount}")

sal2 = YarnSalesService.create_sales(
    company_id=company.id,
    data={
        'invoice_number': 'YSAL-202610-0002',
        'invoice_date': timezone.now().date(),
        'yarn_type': YarnCategory.DYED,
        'warehouse_id': wh_yarn.id,
        'customer_id': customer.id,
        'yarn_count_id': count_34s.id,
        'mill_id': mill.id,
        'color_shade_id': shade_navy.id,
        'lot_no': 'LOT-34D-01',
        'bag': 10,
        'per_bag': Decimal('50.000'),
        'quantity': Decimal('500.000'),
        'rate': Decimal('380.00'),
        'payment_terms': 'Net 30 days',
        'remarks': 'Dyed Navy Yarn Sale'
    },
    user=admin_user
)
print(f"Sales 2: {sal2.invoice_number} | {sal2.get_yarn_type_display()} | Qty: {sal2.quantity} Kg | Total: Rs.{sal2.total_amount}")

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
        'return_reason': 'Excess Yarn Returned from Knitting Batch'
    },
    user=admin_user
)
print(f"Sales Return 1: {ret1.return_number} | Re-credited: {ret1.quantity} Kg ({ret1.bag} bags)")

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
        'return_reason': 'Minor shade variation on 1 box'
    },
    user=admin_user
)
print(f"Sales Return 2: {ret2.return_number} | Re-credited: {ret2.quantity} Kg ({ret2.bag} bags)")

print("\n================ LIVE YARN STOCK LEDGER ================")
for st in yarn_stock_table.objects.all():
    shade = st.color_shade.color_name if st.color_shade else "RAW GREY"
    print(f"[{st.get_yarn_type_display()}] Count: {st.yarn_count.count} | Shade: {shade} | Lot: {st.lot_no}")
    print(f"  + Inward: {st.inward_quantity} Kg ({st.inward_bag} bags)")
    print(f"  - Outward: {st.outward_quantity} Kg ({st.outward_bag} bags)")
    print(f"  - Sales: {st.sales_quantity} Kg ({st.sales_bag} bags)")
    print(f"  + Sales Return: {st.sales_return_quantity} Kg ({st.sales_return_bag} bags)")
    print(f"  ===> LIVE BALANCE: {st.balance_quantity} Kg ({st.balance_bag} bags)\n")
