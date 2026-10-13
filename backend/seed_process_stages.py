import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.utils import timezone
from apps.authentication.models import Company, FinancialYear, User
from apps.masters.models import PartyMaster, WarehouseMaster, FabricMaster, FabricTypeMaster
from apps.process.models import (
    parent_process_stage_table,
    parent_process_program_table,
    child_process_program_input_table,
    child_process_program_recipe_table,
)
from apps.process.services import ProcessStageService, ProcessProgramService
from core.constants import PartyTypes, WarehouseTypes

print("================ SEEDING PROCESS STAGES & SAMPLE PROGRAMS ================")

company = Company.objects.first()
fy = FinancialYear.objects.filter(company=company).first()
admin_user = User.objects.filter(is_superuser=True).first()

if not company or not fy:
    print("Error: Company or Financial Year not found.")
    exit(1)

# 1. Seed standard process stages (Knitting, Dyeing, Compacting, Cutting, Printing, Stitching)
stages = ProcessStageService.seed_default_stages(company.id, admin_user)
print(f"Verified/Seeded {len(stages)} Process Stages for Company: {company.name}")
for st in parent_process_stage_table.objects.filter(company=company):
    print(f"  - [{st.code}] {st.name}: Input={st.input_from_stage} ({st.input_unit_type}) -> Output={st.output_to_stage} ({st.output_unit_type}) | Loss={st.standard_loss_percent}% | Rate=INR {st.standard_rate}")

# 2. Get/create reference parties & warehouses
knitter = PartyMaster.objects.filter(company=company, party_type=PartyTypes.KNITTING_UNIT).first()
dyer = PartyMaster.objects.filter(company=company, party_type=PartyTypes.DYEING_UNIT).first()

cutter, _ = PartyMaster.objects.get_or_create(
    company=company,
    code="CUT-001",
    defaults={
        "party_type": PartyTypes.JOB_WORKER,
        "name": "Supreme Garment Cutting Floor",
        "contact_person": "R. Murugan",
        "phone": "0421-2890123",
        "city": "Tirupur",
        "state": "Tamil Nadu",
    }
)

printer, _ = PartyMaster.objects.get_or_create(
    company=company,
    code="PRNT-001",
    defaults={
        "party_type": PartyTypes.JOB_WORKER,
        "name": "Star Screen & Rotary Printers",
        "contact_person": "S. Prakash",
        "phone": "0421-2890456",
        "city": "Tirupur",
        "state": "Tamil Nadu",
    }
)

stitcher, _ = PartyMaster.objects.get_or_create(
    company=company,
    code="STCH-001",
    defaults={
        "party_type": PartyTypes.JOB_WORKER,
        "name": "Classic Garment Stitching Unit",
        "contact_person": "K. Velusamy",
        "phone": "0421-2890789",
        "city": "Tirupur",
        "state": "Tamil Nadu",
    }
)

wh_yarn = WarehouseMaster.objects.filter(company=company, warehouse_type=WarehouseTypes.YARN_GODOWN).first()
wh_grey = WarehouseMaster.objects.filter(company=company, warehouse_type=WarehouseTypes.GREY_FABRIC_GODOWN).first()
wh_dyed = WarehouseMaster.objects.filter(company=company, warehouse_type=WarehouseTypes.DYED_FABRIC_GODOWN).first()

wh_fg, _ = WarehouseMaster.objects.get_or_create(
    company=company,
    warehouse_type=WarehouseTypes.FINISHED_GOODS_GODOWN,
    defaults={
        "warehouse_code": "WH-FG-01",
        "name": "Main Finished Goods Warehouse",
        "address": "Tirupur, Tamil Nadu",
        "contact_person": "Store Keeper",
        "phone": "0421-2890999",
    }
)

# Fetch stages
stage_knit = parent_process_stage_table.objects.get(company=company, code="KNITTING")
stage_dye = parent_process_stage_table.objects.get(company=company, code="DYEING")
stage_comp = parent_process_stage_table.objects.get(company=company, code="COMPACTING")
stage_cut = parent_process_stage_table.objects.get(company=company, code="CUTTING")
stage_prnt = parent_process_stage_table.objects.get(company=company, code="PRINTING")
stage_stch = parent_process_stage_table.objects.get(company=company, code="STITCHING")

# 3. Clean up prior sample process programs
parent_process_program_table.objects.filter(company=company, program_number__startswith="PRG-").delete()

print("\n--- Creating > 2 entries for each process stage ---")

# =====================================================================
# STAGE 1: KNITTING (3 entries)
# =====================================================================
knit_programs_data = [
    {
        "program_number": "PRG-KNIT-202610-0001",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_knit.id,
        "job_worker_id": knitter.id if knitter else cutter.id,
        "source_warehouse_id": wh_yarn.id if wh_yarn else wh_grey.id,
        "dest_warehouse_id": wh_grey.id,
        "input_from": "YARN",
        "input_item": "30s Combed Cotton Grey Yarn",
        "input_type": "BAG_WT_KG",
        "input_units": 24,
        "input_quantity": Decimal("1200.000"),
        "output_to": "GREY_FABRIC",
        "output_item": "30s Cotton Single Jersey Grey Fabric",
        "output_type": "ROLL_WT_KG",
        "planned_loss_percent": Decimal("2.00"),
        "dia": "24",
        "gsm": 160,
        "gauge": "24GG",
        "loop_length": "2.70",
        "rate": Decimal("18.00"),
        "remarks": "Autumn T-Shirt production lot 01",
        "input_lines": [
            {"item_name": "30s Combed Cotton 100%", "blend_ratio_percent": "100.00", "units": 24, "quantity": "1200.000"}
        ]
    },
    {
        "program_number": "PRG-KNIT-202610-0002",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_knit.id,
        "job_worker_id": knitter.id if knitter else cutter.id,
        "source_warehouse_id": wh_yarn.id if wh_yarn else wh_grey.id,
        "dest_warehouse_id": wh_grey.id,
        "input_from": "YARN",
        "input_item": "40s Combed Cotton Grey Yarn",
        "input_type": "BAG_WT_KG",
        "input_units": 18,
        "input_quantity": Decimal("900.000"),
        "output_to": "GREY_FABRIC",
        "output_item": "40s Cotton Interlock Grey Fabric",
        "output_type": "ROLL_WT_KG",
        "planned_loss_percent": Decimal("2.00"),
        "dia": "30",
        "gsm": 190,
        "gauge": "28GG",
        "loop_length": "2.85",
        "rate": Decimal("22.00"),
        "remarks": "Premium Polo shirt interlock run",
        "input_lines": [
            {"item_name": "40s Combed Cotton Compact", "blend_ratio_percent": "100.00", "units": 18, "quantity": "900.000"}
        ]
    },
    {
        "program_number": "PRG-KNIT-202610-0003",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_knit.id,
        "job_worker_id": knitter.id if knitter else cutter.id,
        "source_warehouse_id": wh_yarn.id if wh_yarn else wh_grey.id,
        "dest_warehouse_id": wh_grey.id,
        "input_from": "YARN",
        "input_item": "2/20s PC Blend Yarn (65/35)",
        "input_type": "BAG_WT_KG",
        "input_units": 12,
        "input_quantity": Decimal("600.000"),
        "output_to": "GREY_FABRIC",
        "output_item": "1x1 Rib Collar & Cuff Fabric",
        "output_type": "ROLL_WT_KG",
        "planned_loss_percent": Decimal("2.50"),
        "dia": "34",
        "gsm": 220,
        "gauge": "18GG",
        "loop_length": "2.60",
        "rate": Decimal("20.00"),
        "remarks": "Matching ribbed trims production",
        "input_lines": [
            {"item_name": "2/20s Polyester Cotton 65/35", "blend_ratio_percent": "100.00", "units": 12, "quantity": "600.000"}
        ]
    },
]

for d in knit_programs_data:
    p = ProcessProgramService.create_program(company.id, fy.id, d, admin_user)
    ProcessProgramService.authorize_program(p.id, company.id, admin_user)
    print(f"  [KNITTING] {p.program_number}: {p.input_quantity} Kg Yarn -> {p.expected_output_qty} Kg Grey Fabric [AUTHORIZED]")

# =====================================================================
# STAGE 2: DYEING & PROCESSING (3 entries)
# =====================================================================
dye_programs_data = [
    {
        "program_number": "PRG-DYE-202610-0001",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_dye.id,
        "job_worker_id": dyer.id if dyer else cutter.id,
        "source_warehouse_id": wh_grey.id,
        "dest_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "input_from": "GREY_FABRIC",
        "input_item": "30s Cotton Single Jersey Grey Fabric",
        "input_type": "ROLL_WT_KG",
        "input_units": 35,
        "input_quantity": Decimal("700.000"),
        "output_to": "DYED_FABRIC",
        "output_item": "Navy Blue Dyed Single Jersey",
        "output_type": "ROLL_WT_KG",
        "planned_loss_percent": Decimal("5.00"),
        "length_shrinkage_percent": Decimal("4.00"),
        "width_shrinkage_percent": Decimal("4.00"),
        "spirality_tolerance_percent": Decimal("3.00"),
        "lab_dip_no": "LD-2026-088",
        "light_source": "D65",
        "dye_class": "REACTIVE",
        "rate": Decimal("35.00"),
        "remarks": "Navy Blue shade 19-4024 TCX Reactive Dyeing run",
        "input_lines": [
            {"source_lot_or_roll_no": "LOT-SJ-KNT01", "item_name": "Single Jersey 24 Dia 160 GSM", "units": 35, "quantity": "700.000"}
        ],
        "recipe_lines": [
            {"item_type": "DYESTUFF", "item_name": "Reactive Navy Blue RGB", "dosage_unit": "PERCENTAGE", "dosage_value": "2.8500", "process_step": "DYEING"},
            {"item_type": "CHEMICAL", "item_name": "Glauber Salt", "dosage_unit": "GPL", "dosage_value": "50.0000", "process_step": "DYEING"},
            {"item_type": "CHEMICAL", "item_name": "Soda Ash", "dosage_unit": "GPL", "dosage_value": "20.0000", "process_step": "FIXATION"}
        ]
    },
    {
        "program_number": "PRG-DYE-202610-0002",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_dye.id,
        "job_worker_id": dyer.id if dyer else cutter.id,
        "source_warehouse_id": wh_grey.id,
        "dest_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "input_from": "GREY_FABRIC",
        "input_item": "30s Cotton Single Jersey Grey Fabric",
        "input_type": "ROLL_WT_KG",
        "input_units": 32,
        "input_quantity": Decimal("650.000"),
        "output_to": "DYED_FABRIC",
        "output_item": "Crimson Red Dyed Single Jersey",
        "output_type": "ROLL_WT_KG",
        "planned_loss_percent": Decimal("5.00"),
        "length_shrinkage_percent": Decimal("3.50"),
        "width_shrinkage_percent": Decimal("3.50"),
        "spirality_tolerance_percent": Decimal("2.50"),
        "lab_dip_no": "LD-2026-104",
        "light_source": "TL84",
        "dye_class": "REACTIVE",
        "rate": Decimal("38.00"),
        "remarks": "Crimson Red shade 19-1763 TCX High-fastness run",
        "input_lines": [
            {"source_lot_or_roll_no": "LOT-SJ-KNT02", "item_name": "Single Jersey 24 Dia 160 GSM", "units": 32, "quantity": "650.000"}
        ],
        "recipe_lines": [
            {"item_type": "DYESTUFF", "item_name": "Reactive Red ME4B", "dosage_unit": "PERCENTAGE", "dosage_value": "3.1000", "process_step": "DYEING"},
            {"item_type": "CHEMICAL", "item_name": "Glauber Salt", "dosage_unit": "GPL", "dosage_value": "45.0000", "process_step": "DYEING"},
            {"item_type": "CHEMICAL", "item_name": "Soda Ash", "dosage_unit": "GPL", "dosage_value": "18.0000", "process_step": "FIXATION"}
        ]
    },
    {
        "program_number": "PRG-DYE-202610-0003",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_dye.id,
        "job_worker_id": dyer.id if dyer else cutter.id,
        "source_warehouse_id": wh_grey.id,
        "dest_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "input_from": "GREY_FABRIC",
        "input_item": "40s Cotton Interlock Grey Fabric",
        "input_type": "ROLL_WT_KG",
        "input_units": 40,
        "input_quantity": Decimal("800.000"),
        "output_to": "DYED_FABRIC",
        "output_item": "Olive Green Dyed Interlock Fabric",
        "output_type": "ROLL_WT_KG",
        "planned_loss_percent": Decimal("5.00"),
        "length_shrinkage_percent": Decimal("3.00"),
        "width_shrinkage_percent": Decimal("3.00"),
        "spirality_tolerance_percent": Decimal("2.00"),
        "lab_dip_no": "LD-2026-112",
        "light_source": "D65",
        "dye_class": "REACTIVE",
        "rate": Decimal("36.00"),
        "remarks": "Olive Green shade 18-0527 TCX Reactive Dyeing run",
        "input_lines": [
            {"source_lot_or_roll_no": "LOT-INT-KNT01", "item_name": "Interlock 30 Dia 190 GSM", "units": 40, "quantity": "800.000"}
        ],
        "recipe_lines": [
            {"item_type": "DYESTUFF", "item_name": "Reactive Yellow 3RS", "dosage_unit": "PERCENTAGE", "dosage_value": "1.4500", "process_step": "DYEING"},
            {"item_type": "DYESTUFF", "item_name": "Reactive Blue 21", "dosage_unit": "PERCENTAGE", "dosage_value": "1.8000", "process_step": "DYEING"},
            {"item_type": "CHEMICAL", "item_name": "Glauber Salt", "dosage_unit": "GPL", "dosage_value": "55.0000", "process_step": "DYEING"},
            {"item_type": "CHEMICAL", "item_name": "Soda Ash", "dosage_unit": "GPL", "dosage_value": "22.0000", "process_step": "FIXATION"}
        ]
    },
]

for d in dye_programs_data:
    p = ProcessProgramService.create_program(company.id, fy.id, d, admin_user)
    ProcessProgramService.authorize_program(p.id, company.id, admin_user)
    print(f"  [DYEING] {p.program_number}: {p.input_quantity} Kg Grey -> {p.expected_output_qty} Kg Dyed | {p.recipe_lines.count()} chemicals [AUTHORIZED]")

# =====================================================================
# STAGE 3: COMPACTING (3 entries)
# =====================================================================
comp_programs_data = [
    {
        "program_number": "PRG-COMP-202610-0001",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_comp.id,
        "job_worker_id": dyer.id if dyer else cutter.id,
        "source_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "dest_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "input_from": "DYED_FABRIC",
        "input_item": "Navy Blue Dyed Single Jersey",
        "input_type": "ROLL_WT_KG",
        "input_units": 33,
        "input_quantity": Decimal("665.000"),
        "output_to": "DYED_FABRIC",
        "output_item": "Compacted Navy Blue Single Jersey",
        "output_type": "ROLL_WT_KG",
        "planned_loss_percent": Decimal("1.00"),
        "length_shrinkage_percent": Decimal("2.80"),
        "width_shrinkage_percent": Decimal("2.50"),
        "spirality_tolerance_percent": Decimal("2.00"),
        "rate": Decimal("8.00"),
        "remarks": "Tubular felt compacting for zero torquing",
        "input_lines": [
            {"source_lot_or_roll_no": "DYE-NAVY-01", "item_name": "Dyed Single Jersey Rolls", "units": 33, "quantity": "665.000"}
        ]
    },
    {
        "program_number": "PRG-COMP-202610-0002",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_comp.id,
        "job_worker_id": dyer.id if dyer else cutter.id,
        "source_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "dest_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "input_from": "DYED_FABRIC",
        "input_item": "Crimson Red Dyed Single Jersey",
        "input_type": "ROLL_WT_KG",
        "input_units": 30,
        "input_quantity": Decimal("615.000"),
        "output_to": "DYED_FABRIC",
        "output_item": "Compacted Crimson Red Single Jersey",
        "output_type": "ROLL_WT_KG",
        "planned_loss_percent": Decimal("1.00"),
        "length_shrinkage_percent": Decimal("3.00"),
        "width_shrinkage_percent": Decimal("2.70"),
        "spirality_tolerance_percent": Decimal("1.80"),
        "rate": Decimal("8.00"),
        "remarks": "Open width compacting for high-stability fabric",
        "input_lines": [
            {"source_lot_or_roll_no": "DYE-RED-01", "item_name": "Dyed Single Jersey Rolls", "units": 30, "quantity": "615.000"}
        ]
    },
    {
        "program_number": "PRG-COMP-202610-0003",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_comp.id,
        "job_worker_id": dyer.id if dyer else cutter.id,
        "source_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "dest_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "input_from": "DYED_FABRIC",
        "input_item": "Olive Green Dyed Interlock Fabric",
        "input_type": "ROLL_WT_KG",
        "input_units": 38,
        "input_quantity": Decimal("760.000"),
        "output_to": "DYED_FABRIC",
        "output_item": "Compacted Olive Green Interlock Fabric",
        "output_type": "ROLL_WT_KG",
        "planned_loss_percent": Decimal("1.00"),
        "length_shrinkage_percent": Decimal("2.00"),
        "width_shrinkage_percent": Decimal("2.00"),
        "spirality_tolerance_percent": Decimal("1.50"),
        "rate": Decimal("9.50"),
        "remarks": "Interlock dimensional stabilization",
        "input_lines": [
            {"source_lot_or_roll_no": "DYE-OLV-01", "item_name": "Dyed Interlock Rolls", "units": 38, "quantity": "760.000"}
        ]
    },
]

for d in comp_programs_data:
    p = ProcessProgramService.create_program(company.id, fy.id, d, admin_user)
    ProcessProgramService.authorize_program(p.id, company.id, admin_user)
    print(f"  [COMPACTING] {p.program_number}: {p.input_quantity} Kg Dyed -> {p.expected_output_qty} Kg Compacted [AUTHORIZED]")

# =====================================================================
# STAGE 4: CUTTING (3 entries)
# =====================================================================
cut_programs_data = [
    {
        "program_number": "PRG-CUT-202610-0001",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_cut.id,
        "job_worker_id": cutter.id,
        "source_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "dest_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "input_from": "DYED_FABRIC",
        "input_item": "Compacted Navy Blue Single Jersey",
        "input_type": "ROLL_WT_KG",
        "input_units": 10,
        "input_quantity": Decimal("200.000"),
        "output_to": "CUT_PANELS",
        "output_item": "Round Neck T-Shirt Cut Body & Sleeve Panels",
        "output_type": "PIECES",
        "planned_loss_percent": Decimal("3.00"),
        "rate": Decimal("4.50"),
        "remarks": "Size ratios: S:1, M:2, L:2, XL:1",
        "input_lines": [
            {"source_lot_or_roll_no": "COMP-NAVY-01", "item_name": "Navy Compacted Fabric Plies", "units": 10, "quantity": "200.000"}
        ]
    },
    {
        "program_number": "PRG-CUT-202610-0002",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_cut.id,
        "job_worker_id": cutter.id,
        "source_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "dest_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "input_from": "DYED_FABRIC",
        "input_item": "Compacted Crimson Red Single Jersey",
        "input_type": "ROLL_WT_KG",
        "input_units": 12,
        "input_quantity": Decimal("250.000"),
        "output_to": "CUT_PANELS",
        "output_item": "Polo Shirt Body, Sleeve & Collar Panels",
        "output_type": "PIECES",
        "planned_loss_percent": Decimal("3.00"),
        "rate": Decimal("5.50"),
        "remarks": "Size ratios: M:2, L:2, XL:2, XXL:1",
        "input_lines": [
            {"source_lot_or_roll_no": "COMP-RED-01", "item_name": "Red Compacted Fabric Plies", "units": 12, "quantity": "250.000"}
        ]
    },
    {
        "program_number": "PRG-CUT-202610-0003",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_cut.id,
        "job_worker_id": cutter.id,
        "source_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "dest_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "input_from": "DYED_FABRIC",
        "input_item": "Compacted Olive Green Interlock Fabric",
        "input_type": "ROLL_WT_KG",
        "input_units": 9,
        "input_quantity": Decimal("180.000"),
        "output_to": "CUT_PANELS",
        "output_item": "Henley Shirt Cut Panels & Front Plackets",
        "output_type": "PIECES",
        "planned_loss_percent": Decimal("3.00"),
        "rate": Decimal("5.00"),
        "remarks": "Size ratios: S:1, M:2, L:2",
        "input_lines": [
            {"source_lot_or_roll_no": "COMP-OLV-01", "item_name": "Olive Compacted Fabric Plies", "units": 9, "quantity": "180.000"}
        ]
    },
]

for d in cut_programs_data:
    p = ProcessProgramService.create_program(company.id, fy.id, d, admin_user)
    ProcessProgramService.authorize_program(p.id, company.id, admin_user)
    print(f"  [CUTTING] {p.program_number}: {p.input_quantity} Kg Dyed Fabric -> {p.expected_output_qty} Pcs Panels [AUTHORIZED]")

# =====================================================================
# STAGE 5: PRINTING (3 entries)
# =====================================================================
prnt_programs_data = [
    {
        "program_number": "PRG-PRNT-202610-0001",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_prnt.id,
        "job_worker_id": printer.id,
        "source_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "dest_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "input_from": "CUT_PANELS",
        "input_item": "Navy Blue T-Shirt Front Chest Panels",
        "input_type": "PIECES",
        "input_units": 11,
        "input_quantity": Decimal("1100.000"),
        "output_to": "PRINTED_PANELS",
        "output_item": "Graphic Screen Printed Navy Chest Panels",
        "output_type": "PIECES",
        "planned_loss_percent": Decimal("1.00"),
        "rate": Decimal("3.50"),
        "remarks": "Discharge print: Vintage Nautical Artwork",
        "input_lines": [
            {"source_lot_or_roll_no": "CUT-NAVY-B01", "item_name": "Chest Cut Panels", "units": 11, "quantity": "1100.000"}
        ],
        "recipe_lines": [
            {"item_type": "DYESTUFF", "item_name": "Discharge White Ink Base", "dosage_unit": "PERCENTAGE", "dosage_value": "15.0000", "process_step": "PRINTING"},
            {"item_type": "CHEMICAL", "item_name": "Discharge Activator Salt", "dosage_unit": "PERCENTAGE", "dosage_value": "5.0000", "process_step": "CURING"}
        ]
    },
    {
        "program_number": "PRG-PRNT-202610-0002",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_prnt.id,
        "job_worker_id": printer.id,
        "source_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "dest_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "input_from": "CUT_PANELS",
        "input_item": "Crimson Red Polo Sleeve Panels",
        "input_type": "PIECES",
        "input_units": 14,
        "input_quantity": Decimal("1350.000"),
        "output_to": "PRINTED_PANELS",
        "output_item": "High-Density Printed Red Sleeve Panels",
        "output_type": "PIECES",
        "planned_loss_percent": Decimal("1.00"),
        "rate": Decimal("3.00"),
        "remarks": "High-Density Plastisol Brand Logo print",
        "input_lines": [
            {"source_lot_or_roll_no": "CUT-RED-S01", "item_name": "Sleeve Cut Panels", "units": 14, "quantity": "1350.000"}
        ],
        "recipe_lines": [
            {"item_type": "DYESTUFF", "item_name": "Plastisol White Ink", "dosage_unit": "PERCENTAGE", "dosage_value": "12.0000", "process_step": "PRINTING"}
        ]
    },
    {
        "program_number": "PRG-PRNT-202610-0003",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_prnt.id,
        "job_worker_id": printer.id,
        "source_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "dest_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "input_from": "CUT_PANELS",
        "input_item": "Olive Green Henley Back Panels",
        "input_type": "PIECES",
        "input_units": 10,
        "input_quantity": Decimal("980.000"),
        "output_to": "PRINTED_PANELS",
        "output_item": "Soft-Hand Waterbase Printed Back Panels",
        "output_type": "PIECES",
        "planned_loss_percent": Decimal("1.00"),
        "rate": Decimal("4.00"),
        "remarks": "Eco-friendly Waterbase Botanical Motif",
        "input_lines": [
            {"source_lot_or_roll_no": "CUT-OLV-B01", "item_name": "Back Cut Panels", "units": 10, "quantity": "980.000"}
        ],
        "recipe_lines": [
            {"item_type": "DYESTUFF", "item_name": "Waterbase Matsui Eco Green", "dosage_unit": "PERCENTAGE", "dosage_value": "10.0000", "process_step": "PRINTING"}
        ]
    },
]

for d in prnt_programs_data:
    p = ProcessProgramService.create_program(company.id, fy.id, d, admin_user)
    ProcessProgramService.authorize_program(p.id, company.id, admin_user)
    print(f"  [PRINTING] {p.program_number}: {p.input_quantity} Pcs Cut Panels -> {p.expected_output_qty} Pcs Printed [AUTHORIZED]")

# =====================================================================
# STAGE 6: STITCHING (3 entries)
# =====================================================================
stch_programs_data = [
    {
        "program_number": "PRG-STCH-202610-0001",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_stch.id,
        "job_worker_id": stitcher.id,
        "source_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "dest_warehouse_id": wh_fg.id,
        "input_from": "CUT_PANELS",
        "input_item": "Printed Navy Blue T-Shirt Body & Trim Panels",
        "input_type": "PIECES",
        "input_units": 11,
        "input_quantity": Decimal("1089.000"),
        "output_to": "GARMENTS",
        "output_item": "Completed Navy Blue Round Neck T-Shirts",
        "output_type": "PIECES",
        "planned_loss_percent": Decimal("1.50"),
        "rate": Decimal("12.50"),
        "remarks": "4-thread overlock assembly with ribbed neck rib",
        "input_lines": [
            {"source_lot_or_roll_no": "PRNT-NAVY-01", "item_name": "Printed Panels Bundle", "units": 11, "quantity": "1089.000"}
        ]
    },
    {
        "program_number": "PRG-STCH-202610-0002",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_stch.id,
        "job_worker_id": stitcher.id,
        "source_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "dest_warehouse_id": wh_fg.id,
        "input_from": "CUT_PANELS",
        "input_item": "Crimson Red Polo Body, Sleeve & Collar Kits",
        "input_type": "PIECES",
        "input_units": 14,
        "input_quantity": Decimal("1336.000"),
        "output_to": "GARMENTS",
        "output_item": "Completed Crimson Red Polo Shirts with Placket",
        "output_type": "PIECES",
        "planned_loss_percent": Decimal("1.50"),
        "rate": Decimal("16.00"),
        "remarks": "Polo assembly with fusing collar & button stitching",
        "input_lines": [
            {"source_lot_or_roll_no": "PRNT-RED-01", "item_name": "Polo Component Bundles", "units": 14, "quantity": "1336.000"}
        ]
    },
    {
        "program_number": "PRG-STCH-202610-0003",
        "program_date": timezone.now().date(),
        "process_stage_id": stage_stch.id,
        "job_worker_id": stitcher.id,
        "source_warehouse_id": wh_dyed.id if wh_dyed else wh_grey.id,
        "dest_warehouse_id": wh_fg.id,
        "input_from": "CUT_PANELS",
        "input_item": "Olive Green Henley Body Panels & Plackets",
        "input_type": "PIECES",
        "input_units": 10,
        "input_quantity": Decimal("970.000"),
        "output_to": "GARMENTS",
        "output_item": "Completed Olive Green Henley Shirts",
        "output_type": "PIECES",
        "planned_loss_percent": Decimal("1.50"),
        "rate": Decimal("14.50"),
        "remarks": "Henley assembly with wooden 3-button placket",
        "input_lines": [
            {"source_lot_or_roll_no": "PRNT-OLV-01", "item_name": "Henley Cut Bundles", "units": 10, "quantity": "970.000"}
        ]
    },
]

for d in stch_programs_data:
    p = ProcessProgramService.create_program(company.id, fy.id, d, admin_user)
    ProcessProgramService.authorize_program(p.id, company.id, admin_user)
    print(f"  [STITCHING] {p.program_number}: {p.input_quantity} Pcs Panels -> {p.expected_output_qty} Pcs Garments [AUTHORIZED]")

print("\n================ PROCESS SEEDING COMPLETED SUCCESSFULLY ================")
