import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.authentication.models import Company
from apps.process.models import (
    parent_process_stage_table,
    JobWorkMaster,
    JobWorkPartyConfiguration,
)
from apps.masters.models import PartyMaster, UnitOfMeasurement
from core.constants import PartyTypes


class Command(BaseCommand):
    help = "Seeds comprehensive, realistic Tirupur Job Work Masters and Party Configurations for Garments ERP."

    def handle(self, *args, **options):
        self.stdout.write("Seeding Job Work Masters and Vendor Configurations...")

        companies = Company.objects.all()
        if not companies.exists():
            self.stdout.write(self.style.ERROR("No companies found in database."))
            return

        for company in companies:
            self._seed_company_job_works(company)

        self.stdout.write(self.style.SUCCESS("Successfully seeded Job Work data."))

    def _seed_company_job_works(self, company):
        company_id = company.id
        self.stdout.write(f"\n--- Seeding for Company: {company.name} ({company.code}) ---")

        # Resolve UOMs
        uom_kgs = UnitOfMeasurement.objects.filter(company_id=company_id, code__iexact="KGS").first() or UnitOfMeasurement.objects.filter(company_id=company_id).first()
        uom_pcs = UnitOfMeasurement.objects.filter(company_id=company_id, code__iexact="PCS").first() or uom_kgs
        uom_mtr = UnitOfMeasurement.objects.filter(company_id=company_id, code__iexact="MTR").first() or uom_kgs

        # Resolve Stages
        stage_knit = parent_process_stage_table.objects.filter(company_id=company_id, code="KNITTING").first()
        stage_dye = parent_process_stage_table.objects.filter(company_id=company_id, code="DYEING").first()
        stage_comp = parent_process_stage_table.objects.filter(company_id=company_id, code="COMPACTING").first()
        stage_cut = parent_process_stage_table.objects.filter(company_id=company_id, code="CUTTING").first()
        stage_prnt = parent_process_stage_table.objects.filter(company_id=company_id, code="PRINTING").first()
        stage_stch = parent_process_stage_table.objects.filter(company_id=company_id, code="STITCHING").first()

        # Resolve Parties
        knitter = PartyMaster.objects.filter(company_id=company_id, party_type=PartyTypes.KNITTING_UNIT).first()
        dyer = PartyMaster.objects.filter(company_id=company_id, party_type=PartyTypes.DYEING_UNIT).first()
        printer = PartyMaster.objects.filter(company_id=company_id, name__icontains="Printer").first() or PartyMaster.objects.filter(company_id=company_id, code__icontains="PRNT").first()
        cutter = PartyMaster.objects.filter(company_id=company_id, name__icontains="Cutting").first() or PartyMaster.objects.filter(company_id=company_id, code__icontains="CUT").first()
        stitcher = PartyMaster.objects.filter(company_id=company_id, name__icontains="Stitching").first() or PartyMaster.objects.filter(company_id=company_id, code__icontains="STCH").first()

        start_date = datetime.date(2026, 4, 1)
        end_date = datetime.date(2027, 3, 31)

        # -------------------------------------------------------------------------
        # 1. JOB WORK MASTER CATALOG
        # -------------------------------------------------------------------------
        master_definitions = [
            # KNITTING
            {
                "code": "JW-KNIT-SJ-24",
                "name": "Single Jersey 24GG Knitting Conversion",
                "stage": stage_knit,
                "category": "KNITTING",
                "material": "YARN",
                "uom": uom_kgs,
                "moq": Decimal("100.000"),
                "max": Decimal("5000.000"),
                "batch": Decimal("300.000"),
                "proc": 2,
                "process": 3,
                "qc": 1,
                "trans": 1,
                "sla": 7,
                "rate": Decimal("18.0000"),
                "desc": "Circular knitting conversion of 100% combed cotton yarn into single jersey grey fabric rolls.",
            },
            {
                "code": "JW-KNIT-RIB-24",
                "name": "1x1 Rib 24GG Knitting Conversion",
                "stage": stage_knit,
                "category": "KNITTING",
                "material": "YARN",
                "uom": uom_kgs,
                "moq": Decimal("100.000"),
                "max": Decimal("3000.000"),
                "batch": Decimal("250.000"),
                "proc": 2,
                "process": 3,
                "qc": 1,
                "trans": 1,
                "sla": 7,
                "rate": Decimal("22.0000"),
                "desc": "Circular knitting conversion for collars, cuffs, and body rib fabric.",
            },
            {
                "code": "JW-KNIT-INT-28",
                "name": "Interlock 28GG Fine Gauge Conversion",
                "stage": stage_knit,
                "category": "KNITTING",
                "material": "YARN",
                "uom": uom_kgs,
                "moq": Decimal("150.000"),
                "max": Decimal("3000.000"),
                "batch": Decimal("250.000"),
                "proc": 2,
                "process": 4,
                "qc": 1,
                "trans": 1,
                "sla": 8,
                "rate": Decimal("25.0000"),
                "desc": "Heavy premium double-knit interlock conversion for polo & activewear.",
            },
            {
                "code": "JW-KNIT-FLC-20",
                "name": "3-Thread Fleece 20GG Winterwear Conversion",
                "stage": stage_knit,
                "category": "KNITTING",
                "material": "YARN",
                "uom": uom_kgs,
                "moq": Decimal("200.000"),
                "max": Decimal("4000.000"),
                "batch": Decimal("350.000"),
                "proc": 2,
                "process": 4,
                "qc": 1,
                "trans": 1,
                "sla": 8,
                "rate": Decimal("28.0000"),
                "desc": "3-end invisible fleece knitting for hoodies and winter sweatshirts.",
            },

            # DYEING
            {
                "code": "JW-DYE-REACT-DK",
                "name": "Reactive Soft-Flow Dyeing - Dark Shade",
                "stage": stage_dye,
                "category": "DYEING",
                "material": "GREY_FABRIC",
                "uom": uom_kgs,
                "moq": Decimal("100.000"),
                "max": Decimal("2500.000"),
                "batch": Decimal("250.000"),
                "proc": 2,
                "process": 4,
                "qc": 1,
                "trans": 1,
                "sla": 8,
                "rate": Decimal("55.0000"),
                "desc": "Exhaust reactive dyeing in soft-flow vessel for Black, Navy, Maroon shades with bio-polish.",
            },
            {
                "code": "JW-DYE-REACT-MED",
                "name": "Reactive Soft-Flow Dyeing - Medium Shade",
                "stage": stage_dye,
                "category": "DYEING",
                "material": "GREY_FABRIC",
                "uom": uom_kgs,
                "moq": Decimal("100.000"),
                "max": Decimal("2500.000"),
                "batch": Decimal("250.000"),
                "proc": 2,
                "process": 3,
                "qc": 1,
                "trans": 1,
                "sla": 7,
                "rate": Decimal("48.0000"),
                "desc": "Standard reactive dyeing for Red, Royal Blue, Olive Green, Gold shades.",
            },
            {
                "code": "JW-DYE-REACT-LT",
                "name": "Reactive Soft-Flow Dyeing - Light Shade & White",
                "stage": stage_dye,
                "category": "DYEING",
                "material": "GREY_FABRIC",
                "uom": uom_kgs,
                "moq": Decimal("100.000"),
                "max": Decimal("2500.000"),
                "batch": Decimal("250.000"),
                "proc": 2,
                "process": 3,
                "qc": 1,
                "trans": 1,
                "sla": 7,
                "rate": Decimal("38.0000"),
                "desc": "Bleaching and optical brightening / pastel shade reactive dyeing.",
            },

            # COMPACTING
            {
                "code": "JW-COMP-TUB",
                "name": "Tubular Felt Compacting & Heat Setting",
                "stage": stage_comp,
                "category": "COMPACTING",
                "material": "DYED_FABRIC",
                "uom": uom_kgs,
                "moq": Decimal("100.000"),
                "max": Decimal("5000.000"),
                "batch": Decimal("500.000"),
                "proc": 1,
                "process": 2,
                "qc": 1,
                "trans": 1,
                "sla": 5,
                "rate": Decimal("8.5000"),
                "desc": "Controls residual length/width shrinkage within 4% and improves fabric feel.",
            },

            # CUTTING
            {
                "code": "JW-CUT-CREW-TEE",
                "name": "Crew Neck T-Shirt Automated Lay Cutting",
                "stage": stage_cut,
                "category": "CUTTING",
                "material": "DYED_FABRIC",
                "uom": uom_pcs,
                "moq": Decimal("300.000"),
                "max": Decimal("10000.000"),
                "batch": Decimal("1000.000"),
                "proc": 1,
                "process": 2,
                "qc": 1,
                "trans": 1,
                "sla": 5,
                "rate": Decimal("4.5000"),
                "desc": "Precision knife lay cutting for body, sleeve, neck-rib panels across sizes S to XXL.",
            },
            {
                "code": "JW-CUT-POLO",
                "name": "Polo Shirt Lay Cutting with Placket & Collar",
                "stage": stage_cut,
                "category": "CUTTING",
                "material": "DYED_FABRIC",
                "uom": uom_pcs,
                "moq": Decimal("250.000"),
                "max": Decimal("8000.000"),
                "batch": Decimal("800.000"),
                "proc": 1,
                "process": 3,
                "qc": 1,
                "trans": 1,
                "sla": 6,
                "rate": Decimal("6.0000"),
                "desc": "Cut parts including body, placket facing, woven collar fusing, and sleeve bands.",
            },

            # PRINTING
            {
                "code": "JW-PRNT-SCR-4C",
                "name": "4-Color Chest Screen Printing",
                "stage": stage_prnt,
                "category": "PRINTING",
                "material": "CUT_PANEL",
                "uom": uom_pcs,
                "moq": Decimal("200.000"),
                "max": Decimal("5000.000"),
                "batch": Decimal("500.000"),
                "proc": 2,
                "process": 4,
                "qc": 1,
                "trans": 1,
                "sla": 8,
                "rate": Decimal("7.5000"),
                "desc": "Plastisol/Waterbase multi-color placement screen print with curing wash fastness.",
            },
            {
                "code": "JW-PRNT-ROT-AOP",
                "name": "Rotary All-Over Fabric Reactive Print",
                "stage": stage_prnt,
                "category": "PRINTING",
                "material": "GREY_FABRIC",
                "uom": uom_kgs,
                "moq": Decimal("200.000"),
                "max": Decimal("3000.000"),
                "batch": Decimal("300.000"),
                "proc": 2,
                "process": 5,
                "qc": 1,
                "trans": 1,
                "sla": 9,
                "rate": Decimal("32.0000"),
                "desc": "Continuous rotary screen all-over printing with loop ager steaming and washing.",
            },

            # STITCHING
            {
                "code": "JW-STCH-CREW-TEE",
                "name": "Basic Crew Neck T-Shirt CMT Assembly",
                "stage": stage_stch,
                "category": "STITCHING",
                "material": "CUT_PANEL",
                "uom": uom_pcs,
                "moq": Decimal("200.000"),
                "max": Decimal("5000.000"),
                "batch": Decimal("500.000"),
                "proc": 2,
                "process": 5,
                "qc": 1,
                "trans": 1,
                "sla": 9,
                "rate": Decimal("14.0000"),
                "desc": "Overlock + flatlock seaming, rib attachment, tape binding, and size label tacking.",
            },
            {
                "code": "JW-STCH-POLO",
                "name": "Pique Polo Shirt CMT Assembly with Rib Collar",
                "stage": stage_stch,
                "category": "STITCHING",
                "material": "CUT_PANEL",
                "uom": uom_pcs,
                "moq": Decimal("200.000"),
                "max": Decimal("4000.000"),
                "batch": Decimal("400.000"),
                "proc": 2,
                "process": 6,
                "qc": 1,
                "trans": 1,
                "sla": 10,
                "rate": Decimal("24.0000"),
                "desc": "Button placket construction, jacquard knit collar assembly, side slit binding.",
            },
        ]

        created_jw_map = {}

        for m_data in master_definitions:
            if not m_data["stage"]:
                continue

            jw, created = JobWorkMaster.objects.get_or_create(
                company_id=company_id,
                job_work_code=m_data["code"],
                defaults={
                    "company_id": company_id,
                    "job_work_code": m_data["code"],
                    "job_work_name": m_data["name"],
                    "process_stage_id": m_data["stage"].id,
                    "job_work_category": m_data["category"],
                    "material_type": m_data["material"],
                    "uom_id": m_data["uom"].id,
                    "min_order_qty": m_data["moq"],
                    "max_order_qty": m_data["max"],
                    "standard_batch_qty": m_data["batch"],
                    "procurement_days": m_data["proc"],
                    "processing_days": m_data["process"],
                    "quality_inspection_days": m_data["qc"],
                    "transportation_days": m_data["trans"],
                    "standard_delivery_days": m_data["sla"],
                    "standard_rate": m_data["rate"],
                    "rate_valid_from": start_date,
                    "rate_valid_to": end_date,
                    "description": m_data["desc"],
                    "is_active": True,
                    "record_status": "A",
                }
            )
            created_jw_map[m_data["code"]] = jw
            action_str = "Created" if created else "Found"
            self.stdout.write(f"  {action_str} Master: [{jw.job_work_code}] {jw.job_work_name} ({jw.total_estimated_lead_time}d lead time)")

        # -------------------------------------------------------------------------
        # 2. JOB WORK PARTY-SPECIFIC CONFIGURATIONS (CONTRACTS)
        # -------------------------------------------------------------------------
        party_configs = []

        # Annai Knitting Works (knitter)
        if knitter:
            if "JW-KNIT-SJ-24" in created_jw_map:
                party_configs.append({
                    "jw": created_jw_map["JW-KNIT-SJ-24"],
                    "party": knitter,
                    "uom": uom_kgs,
                    "moq": Decimal("300.000"),
                    "max": Decimal("4000.000"),
                    "daily": Decimal("1000.000"),
                    "proc": 2, "process": 3, "qc": 1, "trans": 1,
                    "rate": Decimal("16.0000"),
                    "surcharge": Decimal("2.0000"),
                    "loss": Decimal("2.00"),
                    "remarks": "Annai Knitting: Special volume discount agreement",
                })
            if "JW-KNIT-RIB-24" in created_jw_map:
                party_configs.append({
                    "jw": created_jw_map["JW-KNIT-RIB-24"],
                    "party": knitter,
                    "uom": uom_kgs,
                    "moq": Decimal("250.000"),
                    "max": Decimal("2500.000"),
                    "daily": Decimal("600.000"),
                    "proc": 2, "process": 3, "qc": 1, "trans": 1,
                    "rate": Decimal("20.0000"),
                    "surcharge": Decimal("2.5000"),
                    "loss": Decimal("2.50"),
                    "remarks": "Annai Knitting: Rib dial machine priority scheduling",
                })
            if "JW-KNIT-INT-28" in created_jw_map:
                party_configs.append({
                    "jw": created_jw_map["JW-KNIT-INT-28"],
                    "party": knitter,
                    "uom": uom_kgs,
                    "moq": Decimal("300.000"),
                    "max": Decimal("2500.000"),
                    "daily": Decimal("500.000"),
                    "proc": 2, "process": 4, "qc": 1, "trans": 1,
                    "rate": Decimal("23.0000"),
                    "surcharge": Decimal("3.0000"),
                    "loss": Decimal("2.50"),
                    "remarks": "Annai Knitting: 28GG Interlock contract",
                })

        # Rainbow Dyeing & Processing Mills (dyer)
        if dyer:
            if "JW-DYE-REACT-DK" in created_jw_map:
                party_configs.append({
                    "jw": created_jw_map["JW-DYE-REACT-DK"],
                    "party": dyer,
                    "uom": uom_kgs,
                    "moq": Decimal("250.000"),
                    "max": Decimal("2000.000"),
                    "daily": Decimal("800.000"),
                    "proc": 2, "process": 4, "qc": 1, "trans": 1,
                    "rate": Decimal("52.0000"),
                    "surcharge": Decimal("5.0000"),
                    "loss": Decimal("5.00"),
                    "remarks": "Rainbow Dyeing: Zero discharge soft-flow vessel reservation",
                })
            if "JW-DYE-REACT-MED" in created_jw_map:
                party_configs.append({
                    "jw": created_jw_map["JW-DYE-REACT-MED"],
                    "party": dyer,
                    "uom": uom_kgs,
                    "moq": Decimal("200.000"),
                    "max": Decimal("2000.000"),
                    "daily": Decimal("1000.000"),
                    "proc": 2, "process": 3, "qc": 1, "trans": 1,
                    "rate": Decimal("45.0000"),
                    "surcharge": Decimal("4.0000"),
                    "loss": Decimal("4.50"),
                    "remarks": "Rainbow Dyeing: Reactive medium shade terms",
                })
            if "JW-DYE-REACT-LT" in created_jw_map:
                party_configs.append({
                    "jw": created_jw_map["JW-DYE-REACT-LT"],
                    "party": dyer,
                    "uom": uom_kgs,
                    "moq": Decimal("150.000"),
                    "max": Decimal("2500.000"),
                    "daily": Decimal("1200.000"),
                    "proc": 2, "process": 3, "qc": 1, "trans": 1,
                    "rate": Decimal("35.0000"),
                    "surcharge": Decimal("3.5000"),
                    "loss": Decimal("4.00"),
                    "remarks": "Rainbow Dyeing: Bleaching & white shade contract",
                })

        # Supreme Garment Cutting Floor (cutter)
        if cutter:
            if "JW-CUT-CREW-TEE" in created_jw_map:
                party_configs.append({
                    "jw": created_jw_map["JW-CUT-CREW-TEE"],
                    "party": cutter,
                    "uom": uom_pcs,
                    "moq": Decimal("500.000"),
                    "max": Decimal("12000.000"),
                    "daily": Decimal("4000.000"),
                    "proc": 1, "process": 2, "qc": 1, "trans": 1,
                    "rate": Decimal("4.0000"),
                    "surcharge": Decimal("0.7500"),
                    "loss": Decimal("1.50"),
                    "remarks": "Supreme Cutting: CNC Gerber automated cutting spread",
                })
            if "JW-CUT-POLO" in created_jw_map:
                party_configs.append({
                    "jw": created_jw_map["JW-CUT-POLO"],
                    "party": cutter,
                    "uom": uom_pcs,
                    "moq": Decimal("400.000"),
                    "max": Decimal("8000.000"),
                    "daily": Decimal("2500.000"),
                    "proc": 1, "process": 3, "qc": 1, "trans": 1,
                    "rate": Decimal("5.2500"),
                    "surcharge": Decimal("1.0000"),
                    "loss": Decimal("2.00"),
                    "remarks": "Supreme Cutting: Polo pattern alignment terms",
                })

        # Star Screen & Rotary Printers (printer)
        if printer:
            if "JW-PRNT-SCR-4C" in created_jw_map:
                party_configs.append({
                    "jw": created_jw_map["JW-PRNT-SCR-4C"],
                    "party": printer,
                    "uom": uom_pcs,
                    "moq": Decimal("300.000"),
                    "max": Decimal("5000.000"),
                    "daily": Decimal("1500.000"),
                    "proc": 2, "process": 4, "qc": 1, "trans": 1,
                    "rate": Decimal("6.8000"),
                    "surcharge": Decimal("1.2000"),
                    "loss": Decimal("1.00"),
                    "remarks": "Star Printers: Automatic carousel screen print agreement",
                })

        # Classic Garment Stitching Unit (stitcher)
        if stitcher:
            if "JW-STCH-CREW-TEE" in created_jw_map:
                party_configs.append({
                    "jw": created_jw_map["JW-STCH-CREW-TEE"],
                    "party": stitcher,
                    "uom": uom_pcs,
                    "moq": Decimal("300.000"),
                    "max": Decimal("6000.000"),
                    "daily": Decimal("1200.000"),
                    "proc": 2, "process": 5, "qc": 1, "trans": 1,
                    "rate": Decimal("12.5000"),
                    "surcharge": Decimal("2.0000"),
                    "loss": Decimal("1.00"),
                    "remarks": "Classic Stitching: 40-machine line dedicated allocation",
                })
            if "JW-STCH-POLO" in created_jw_map:
                party_configs.append({
                    "jw": created_jw_map["JW-STCH-POLO"],
                    "party": stitcher,
                    "uom": uom_pcs,
                    "moq": Decimal("250.000"),
                    "max": Decimal("4000.000"),
                    "daily": Decimal("800.000"),
                    "proc": 2, "process": 6, "qc": 1, "trans": 1,
                    "rate": Decimal("22.0000"),
                    "surcharge": Decimal("3.0000"),
                    "loss": Decimal("1.50"),
                    "remarks": "Classic Stitching: Premium polo assembly contract",
                })

        for cfg_data in party_configs:
            cfg, created = JobWorkPartyConfiguration.objects.get_or_create(
                company_id=company_id,
                job_work_id=cfg_data["jw"].id,
                party_id=cfg_data["party"].id,
                defaults={
                    "company_id": company_id,
                    "job_work_id": cfg_data["jw"].id,
                    "party_id": cfg_data["party"].id,
                    "uom_id": cfg_data["uom"].id,
                    "min_order_qty": cfg_data["moq"],
                    "max_order_qty": cfg_data["max"],
                    "daily_capacity_qty": cfg_data["daily"],
                    "procurement_days": cfg_data["proc"],
                    "processing_days": cfg_data["process"],
                    "quality_inspection_days": cfg_data["qc"],
                    "transportation_days": cfg_data["trans"],
                    "agreed_rate": cfg_data["rate"],
                    "small_lot_surcharge": cfg_data["surcharge"],
                    "allowed_loss_percent": cfg_data["loss"],
                    "effective_from": start_date,
                    "effective_to": end_date,
                    "is_active": True,
                    "remarks": cfg_data["remarks"],
                    "record_status": "A",
                }
            )
            action_str = "Created" if created else "Found"
            self.stdout.write(f"    {action_str} Party Config: [{cfg_data['party'].name}] -> {cfg_data['jw'].job_work_code} @ Rs.{cfg.agreed_rate} ({cfg.total_estimated_lead_time}d)")
