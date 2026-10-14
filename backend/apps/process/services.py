from decimal import Decimal
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from core.base_services import BaseService
from core.exceptions import ValidationError, ResourceNotFound, ConflictError
from core.constants import ProcessProgramStatus
from core.formats import FormatService
from apps.process.models import (
    parent_process_stage_table,
    parent_process_program_table,
    child_process_program_input_table,
    child_process_program_recipe_table,
    JobWorkMaster,
    JobWorkPartyConfiguration,
)


def _normalize_fk(data: dict, fk_fields: list):
    for field in fk_fields:
        if field in data and f"{field}_id" not in data:
            val = data.pop(field)
            if hasattr(val, "id"):
                data[f"{field}_id"] = val.id
            elif isinstance(val, (int, str)) and str(val).isdigit():
                data[f"{field}_id"] = int(val)


class ProcessStageService(BaseService):
    """
    Manages process stage definitions (Knitting, Dyeing, Cutting, etc.).
    """

    DEFAULT_STAGES = [
        {
            "name": "Knitting",
            "code": "KNITTING",
            "sequence_order": 10,
            "input_from_stage": "YARN",
            "input_item_category": "GREY_YARN",
            "input_unit_type": "BAG_WT_KG",
            "output_to_stage": "GREY_FABRIC",
            "output_item_category": "GREY_FABRIC",
            "output_unit_type": "ROLL_WT_KG",
            "standard_loss_percent": Decimal("2.00"),
            "standard_rate": Decimal("18.00"),
            "has_recipe": False,
            "has_shrinkage": False,
            "has_sizes": False,
            "description": "Transforms Yarn into Grey Knitted Fabric rolls.",
        },
        {
            "name": "Dyeing & Processing",
            "code": "DYEING",
            "sequence_order": 20,
            "input_from_stage": "GREY_FABRIC",
            "input_item_category": "GREY_FABRIC",
            "input_unit_type": "ROLL_WT_KG",
            "output_to_stage": "DYED_FABRIC",
            "output_item_category": "DYED_FABRIC",
            "output_unit_type": "ROLL_WT_KG",
            "standard_loss_percent": Decimal("5.00"),
            "standard_rate": Decimal("35.00"),
            "has_recipe": True,
            "has_shrinkage": True,
            "has_sizes": False,
            "description": "Bleaches, dyes, and finishes Grey Fabric into colored Dyed Fabric rolls.",
        },
        {
            "name": "Compacting",
            "code": "COMPACTING",
            "sequence_order": 25,
            "input_from_stage": "DYED_FABRIC",
            "input_item_category": "DYED_FABRIC",
            "input_unit_type": "ROLL_WT_KG",
            "output_to_stage": "DYED_FABRIC",
            "output_item_category": "DYED_FABRIC",
            "output_unit_type": "ROLL_WT_KG",
            "standard_loss_percent": Decimal("1.00"),
            "standard_rate": Decimal("8.00"),
            "has_recipe": False,
            "has_shrinkage": True,
            "has_sizes": False,
            "description": "Controls length/width shrinkage and compacts fabric for stability.",
        },
        {
            "name": "Cutting",
            "code": "CUTTING",
            "sequence_order": 30,
            "input_from_stage": "DYED_FABRIC",
            "input_item_category": "DYED_FABRIC",
            "input_unit_type": "ROLL_WT_KG",
            "output_to_stage": "CUT_PANELS",
            "output_item_category": "CUT_PANELS",
            "output_unit_type": "PIECES",
            "standard_loss_percent": Decimal("3.00"),
            "standard_rate": Decimal("4.50"),
            "has_recipe": False,
            "has_shrinkage": False,
            "has_sizes": True,
            "description": "Spreads dyed fabric and cuts garment body panels, sleeves, and collars.",
        },
        {
            "name": "Printing",
            "code": "PRINTING",
            "sequence_order": 40,
            "input_from_stage": "CUT_PANELS",
            "input_item_category": "CUT_PANELS",
            "input_unit_type": "PIECES",
            "output_to_stage": "PRINTED_PANELS",
            "output_item_category": "PRINTED_PANELS",
            "output_unit_type": "PIECES",
            "standard_loss_percent": Decimal("1.00"),
            "standard_rate": Decimal("3.50"),
            "has_recipe": True,
            "has_shrinkage": False,
            "has_sizes": True,
            "description": "Screen, rotary, or chest printing on cut garment panels.",
        },
        {
            "name": "Stitching",
            "code": "STITCHING",
            "sequence_order": 50,
            "input_from_stage": "CUT_PANELS",
            "input_item_category": "CUT_PANELS",
            "input_unit_type": "PIECES",
            "output_to_stage": "GARMENTS",
            "output_item_category": "GARMENTS",
            "output_unit_type": "PIECES",
            "standard_loss_percent": Decimal("1.50"),
            "standard_rate": Decimal("12.50"),
            "has_recipe": False,
            "has_shrinkage": False,
            "has_sizes": True,
            "description": "Assembles cut panels into completed garments.",
        },
    ]

    @classmethod
    @transaction.atomic
    def seed_default_stages(cls, company_id: int, user=None) -> List[parent_process_stage_table]:
        created_stages = []
        for stage_def in cls.DEFAULT_STAGES:
            stage, created = parent_process_stage_table.objects.get_or_create(
                company_id=company_id,
                code=stage_def["code"],
                defaults={
                    **stage_def,
                    "company_id": company_id,
                    "created_by": user,
                    "updated_by": user,
                }
            )
            created_stages.append(stage)
        return created_stages


class ProcessProgramService(BaseService):
    """
    Business workflow engine for all production process programs (job cards).
    Enforces automatic serial generation, loss % calculation, authorization,
    and live reconciliation with Inward receipts.
    """

    CODE_MAP = {
        "KNITTING": "KNIT",
        "DYEING": "DYE",
        "COMPACTING": "COMP",
        "CUTTING": "CUT",
        "PRINTING": "PRNT",
        "STITCHING": "STCH",
        "FINISHING": "FIN",
        "PACKING": "PACK",
    }

    @classmethod
    def _generate_program_number(cls, company_id: int, stage_code: str = "PRG") -> str:
        date_str = timezone.now().strftime("%Y%m")
        clean_code = cls.CODE_MAP.get(stage_code.upper(), stage_code[:4].upper())
        prefix = f"PRG-{clean_code}-{date_str}-"
        last = (
            parent_process_program_table.objects
            .filter(company_id=company_id, program_number__startswith=prefix)
            .order_by("-program_number")
            .first()
        )
        if last:
            try:
                seq = int(last.program_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def create_program(cls, company_id: int, fy_id: int, data: Dict[str, Any], user) -> parent_process_program_table:
        input_lines_data = data.pop("input_lines", [])
        recipe_lines_data = data.pop("recipe_lines", [])

        _normalize_fk(data, ["process_stage", "job_worker", "source_warehouse", "dest_warehouse"])

        # Fetch stage to auto-derive code and defaults if missing
        stage_id = data.get("process_stage_id")
        stage = parent_process_stage_table.objects.filter(id=stage_id, company_id=company_id).first()
        stage_code = stage.code if stage else "PRG"

        if not data.get("program_number"):
            data["program_number"] = cls._generate_program_number(company_id, stage_code)

        if "program_date" in data and data["program_date"]:
            data["program_date"] = FormatService.parse_date(data["program_date"])

        data["company_id"] = company_id
        data["cfyear_id"] = fy_id
        data["created_by"] = user
        data["updated_by"] = user
        data["status"] = ProcessProgramStatus.DRAFT

        # Default routing strings from stage if not supplied
        if stage:
            if not data.get("input_from"):
                data["input_from"] = stage.input_from_stage
            if not data.get("output_to"):
                data["output_to"] = stage.output_to_stage
            if not data.get("input_type"):
                data["input_type"] = stage.input_unit_type
            if not data.get("output_type"):
                data["output_type"] = stage.output_unit_type
            if not data.get("planned_loss_percent"):
                data["planned_loss_percent"] = stage.standard_loss_percent
            if not data.get("rate") and stage.standard_rate > 0:
                data["rate"] = stage.standard_rate

        program = parent_process_program_table(**data)
        program.clean()
        program.save()

        # Save child input breakdown lines
        for l_data in input_lines_data:
            child_process_program_input_table.objects.create(
                tm_program=program,
                source_lot_or_roll_no=l_data.get("source_lot_or_roll_no", ""),
                item_code=l_data.get("item_code", ""),
                item_name=l_data.get("item_name", "Raw Material Line"),
                blend_ratio_percent=Decimal(str(l_data.get("blend_ratio_percent", "100.00"))),
                units=int(l_data.get("units", 0)),
                quantity=Decimal(str(l_data.get("quantity", "0.000"))),
                remarks=l_data.get("remarks", ""),
            )

        # Save child recipe lines (if dyeing/washing/printing)
        for r_data in recipe_lines_data:
            child_process_program_recipe_table.objects.create(
                tm_program=program,
                item_type=r_data.get("item_type", "DYESTUFF"),
                item_name=r_data.get("item_name", "Chemical"),
                dosage_unit=r_data.get("dosage_unit", "PERCENTAGE"),
                dosage_value=Decimal(str(r_data.get("dosage_value", "0.0000"))),
                process_step=r_data.get("process_step", ""),
                remarks=r_data.get("remarks", ""),
            )

        return program

    @classmethod
    @transaction.atomic
    def authorize_program(cls, program_id: int, company_id: int, user) -> parent_process_program_table:
        program = (
            parent_process_program_table.objects
            .select_for_update()
            .filter(id=program_id, company_id=company_id)
            .exclude(status=ProcessProgramStatus.CANCELLED)
            .first()
        )
        if not program:
            raise ResourceNotFound(f"Process Program {program_id} not found.")

        if program.status == ProcessProgramStatus.AUTHORIZED:
            raise ConflictError("Process Program is already authorized.")

        program.status = ProcessProgramStatus.AUTHORIZED
        program.is_authorized = 1
        program.updated_by = user
        program.save(update_fields=["status", "is_authorized", "updated_by", "updated_on"])
        return program

    @classmethod
    @transaction.atomic
    def unauthorize_program(cls, program_id: int, company_id: int, user) -> parent_process_program_table:
        program = (
            parent_process_program_table.objects
            .select_for_update()
            .filter(id=program_id, company_id=company_id)
            .first()
        )
        if not program:
            raise ResourceNotFound(f"Process Program {program_id} not found.")

        if program.status != ProcessProgramStatus.AUTHORIZED:
            raise ValidationError("Only Authorized programs that have not started production can be re-opened to Draft.")

        program.status = ProcessProgramStatus.DRAFT
        program.is_authorized = 0
        program.updated_by = user
        program.save(update_fields=["status", "is_authorized", "updated_by", "updated_on"])
        return program

    @classmethod
    @transaction.atomic
    def cancel_program(cls, program_id: int, company_id: int, user) -> parent_process_program_table:
        program = (
            parent_process_program_table.objects
            .select_for_update()
            .filter(id=program_id, company_id=company_id)
            .first()
        )
        if not program:
            raise ResourceNotFound(f"Process Program {program_id} not found.")

        if program.received_output_qty > 0:
            raise ValidationError(
                f"Cannot cancel Process Program {program.program_number}: "
                f"Production inward has already commenced ({program.received_output_qty} received)."
            )

        program.soft_delete(user)
        return program

    @classmethod
    def get_program_summary(cls, program_id: int, company_id: int) -> Dict[str, Any]:
        program = (
            parent_process_program_table.objects
            .select_related("process_stage", "job_worker", "source_warehouse", "dest_warehouse")
            .prefetch_related("input_lines", "recipe_lines")
            .filter(id=program_id, company_id=company_id)
            .first()
        )
        if not program:
            raise ResourceNotFound(f"Process Program {program_id} not found.")

        pending_qty = max(Decimal("0.000"), program.expected_output_qty - program.received_output_qty)
        completion_pct = (
            (program.received_output_qty / program.expected_output_qty * Decimal("100.00")).quantize(Decimal("0.01"))
            if program.expected_output_qty > 0
            else Decimal("0.00")
        )

        return {
            "id": program.id,
            "program_number": program.program_number,
            "program_date": program.program_date.strftime("%d/%m/%Y"),
            "process": program.process_stage.name,
            "process_code": program.process_stage.code,
            "job_worker": program.job_worker.name,
            "source_warehouse": program.source_warehouse.name,
            "dest_warehouse": program.dest_warehouse.name,
            "input_from": program.input_from,
            "input_item": program.input_item,
            "input_quantity": str(program.input_quantity),
            "input_units": program.input_units,
            "output_to": program.output_to,
            "output_item": program.output_item,
            "expected_output_qty": str(program.expected_output_qty),
            "received_output_qty": str(program.received_output_qty),
            "pending_output_qty": str(pending_qty),
            "completion_percentage": str(completion_pct),
            "planned_loss_percent": str(program.planned_loss_percent),
            "rate": str(program.rate),
            "grand_total": str(program.grand_total),
            "status": program.get_status_display(),
            "input_lines_count": program.input_lines.count(),
            "recipe_lines_count": program.recipe_lines.count(),
        }


class JobWorkService(BaseService):
    """
    Business Domain Service for Job Work Master and Planning Configuration:
    - Master CRUD with sequential lead-time summation
    - Job Worker Specific Capacity, MOQ & Rate Agreements
    - Order Validation Engine (MOQ checks, capacity ceilings, small lot surcharges)
    - Milestone Delivery Schedule Calculator (Sequential & Fast-Track)
    - Default Masters & Contracts Seeder
    """

    @staticmethod
    @transaction.atomic
    def create_job_work(data: dict, company_id: int, user_id: Optional[int] = None) -> JobWorkMaster:
        from apps.process.repositories import JobWorkRepository
        from apps.process.models import parent_process_stage_table
        from apps.masters.models import UnitOfMeasurement

        code = str(data.get("job_work_code", "")).strip().upper()
        if not code:
            raise ValidationError("Job Work Code is mandatory.")

        if JobWorkRepository.get_by_code(code, company_id):
            raise ConflictError(f"Job Work Code '{code}' already exists for this company.")

        stage_id = data.get("process_stage_id")
        if not stage_id or not parent_process_stage_table.objects.filter(id=stage_id, company_id=company_id).exists():
            raise ValidationError("Valid process_stage_id is required.")

        uom_id = data.get("uom_id")
        if not uom_id or not UnitOfMeasurement.objects.filter(id=uom_id, company_id=company_id).exists():
            raise ValidationError("Valid uom_id is required.")

        min_qty = Decimal(str(data.get("min_order_qty", "100.000")))
        if min_qty <= Decimal("0.000"):
            raise ValidationError("Minimum Order Quantity (MOQ) must be greater than zero.")

        max_qty = data.get("max_order_qty")
        if max_qty is not None and Decimal(str(max_qty)) < min_qty:
            raise ValidationError("Maximum Order Quantity cannot be less than Minimum Order Quantity (MOQ).")

        data["company_id"] = company_id
        data["job_work_code"] = code
        data["created_by"] = user_id
        data["updated_by"] = user_id

        return JobWorkRepository.create(data)

    @staticmethod
    @transaction.atomic
    def update_job_work(job_work_id: int, data: dict, company_id: int, user_id: Optional[int] = None) -> JobWorkMaster:
        from apps.process.repositories import JobWorkRepository

        job_work = JobWorkRepository.get_by_id(job_work_id, company_id)
        if not job_work:
            raise ResourceNotFound(f"Job Work Master #{job_work_id} not found.")

        if "min_order_qty" in data and Decimal(str(data["min_order_qty"])) <= Decimal("0.000"):
            raise ValidationError("Minimum Order Quantity (MOQ) must be greater than zero.")

        min_q = Decimal(str(data.get("min_order_qty", job_work.min_order_qty)))
        max_q = data.get("max_order_qty", job_work.max_order_qty)
        if max_q is not None and Decimal(str(max_q)) < min_q:
            raise ValidationError("Maximum Order Quantity cannot be less than Minimum Order Quantity (MOQ).")

        if user_id:
            data["updated_by"] = user_id

        return JobWorkRepository.update(job_work, data)

    @staticmethod
    @transaction.atomic
    def delete_job_work(job_work_id: int, company_id: int, user_id: Optional[int] = None) -> None:
        from apps.process.repositories import JobWorkRepository
        from apps.process.models import JobWorkPartyConfiguration

        job_work = JobWorkRepository.get_by_id(job_work_id, company_id)
        if not job_work:
            raise ResourceNotFound(f"Job Work Master #{job_work_id} not found.")

        job_work.soft_delete(user_id)
        JobWorkPartyConfiguration.objects.filter(job_work_id=job_work_id, company_id=company_id).update(
            record_status="D",
            updated_by=user_id,
            updated_at=timezone.now()
        )

    @staticmethod
    @transaction.atomic
    def create_party_config(data: dict, company_id: int, user_id: Optional[int] = None) -> JobWorkPartyConfiguration:
        from apps.process.repositories import JobWorkRepository, JobWorkPartyConfigRepository
        from apps.masters.models import PartyMaster, UnitOfMeasurement

        jw_id = data.get("job_work_id")
        party_id = data.get("party_id")
        if not jw_id or not JobWorkRepository.get_by_id(jw_id, company_id):
            raise ValidationError("Valid job_work_id is required.")

        if not party_id or not PartyMaster.objects.filter(id=party_id, company_id=company_id).exists():
            raise ValidationError("Valid party_id is required.")

        uom_id = data.get("uom_id")
        if not uom_id or not UnitOfMeasurement.objects.filter(id=uom_id, company_id=company_id).exists():
            raise ValidationError("Valid uom_id is required.")

        min_qty = Decimal(str(data.get("min_order_qty", "100.000")))
        if min_qty <= Decimal("0.000"):
            raise ValidationError("Minimum Order Quantity (MOQ) must be greater than zero.")

        max_qty = data.get("max_order_qty")
        if max_qty is not None and Decimal(str(max_qty)) < min_qty:
            raise ValidationError("Maximum Order Quantity cannot be less than Minimum Order Quantity (MOQ).")

        eff_from = data.get("effective_from")
        eff_to = data.get("effective_to")
        if eff_from and eff_to and eff_from > eff_to:
            raise ValidationError("effective_from date cannot be after effective_to date.")

        data["company_id"] = company_id
        data["created_by"] = user_id
        data["updated_by"] = user_id

        return JobWorkPartyConfigRepository.create(data)

    @staticmethod
    @transaction.atomic
    def update_party_config(config_id: int, data: dict, company_id: int, user_id: Optional[int] = None) -> JobWorkPartyConfiguration:
        from apps.process.repositories import JobWorkPartyConfigRepository

        config = JobWorkPartyConfigRepository.get_by_id(config_id, company_id)
        if not config:
            raise ResourceNotFound(f"Job Work Party Configuration #{config_id} not found.")

        if "min_order_qty" in data and Decimal(str(data["min_order_qty"])) <= Decimal("0.000"):
            raise ValidationError("Minimum Order Quantity (MOQ) must be greater than zero.")

        if user_id:
            data["updated_by"] = user_id

        return JobWorkPartyConfigRepository.update(config, data)

    @staticmethod
    def validate_job_work_order(
        company_id: int,
        job_work_id: int,
        quantity: Decimal,
        party_id: Optional[int] = None,
        uom_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validates a proposed job work program order against operational thresholds:
        - Rejects zero or negative order quantities.
        - Verifies UOM consistency.
        - Evaluates vendor MOQ and applies small lot surcharge if below threshold.
        - Evaluates maximum batch capacity and warns/blocks overload.
        """
        from apps.process.repositories import JobWorkRepository, JobWorkPartyConfigRepository
        from apps.masters.models import PartyMaster, UnitOfMeasurement

        qty = Decimal(str(quantity))
        if qty <= Decimal("0.000"):
            raise ValidationError("Order quantity must be positive.")

        job_work = JobWorkRepository.get_by_id(job_work_id, company_id)
        if not job_work:
            raise ResourceNotFound(f"Job Work Master #{job_work_id} not found.")

        # UOM validation
        if uom_id and uom_id != job_work.uom_id:
            req_uom = UnitOfMeasurement.objects.filter(id=uom_id).first()
            exp_uom = UnitOfMeasurement.objects.filter(id=job_work.uom_id).first()
            raise ValidationError(
                f"UOM mismatch: Job Work {job_work.job_work_code} requires '{exp_uom.code if exp_uom else job_work.uom_id}', but order requested '{req_uom.code if req_uom else uom_id}'."
            )

        # Retrieve applicable configuration (Party Specific or General Base)
        party_config = None
        party_name = None
        if party_id:
            party = PartyMaster.objects.filter(id=party_id, company_id=company_id).first()
            party_name = party.name if party else f"Party #{party_id}"
            party_config = JobWorkPartyConfigRepository.get_active_config(
                job_work_id=job_work_id,
                party_id=party_id,
                company_id=company_id,
                target_date=timezone.now().date()
            )

        if party_config:
            min_moq = party_config.min_order_qty
            max_cap = party_config.max_order_qty
            base_rate = party_config.agreed_rate
            small_lot_sc = party_config.small_lot_surcharge
            lead_time = party_config.total_estimated_lead_time
            source = "PARTY_SPECIFIC_CONTRACT"
        else:
            min_moq = job_work.min_order_qty
            max_cap = job_work.max_order_qty
            base_rate = job_work.standard_rate
            small_lot_sc = Decimal("0.0000")
            lead_time = job_work.total_estimated_lead_time
            source = "GENERAL_JOB_WORK_MASTER"

        is_below_moq = (qty < min_moq)
        is_capacity_exceeded = (max_cap is not None and qty > max_cap)

        applied_sc = small_lot_sc if is_below_moq else Decimal("0.0000")
        effective_rate = (base_rate + applied_sc).quantize(Decimal("0.0001"))
        est_total = (qty * effective_rate).quantize(Decimal("0.0001"))

        warning_message = None
        if is_below_moq:
            warning_message = f"Order quantity {qty} is below MOQ {min_moq}. "
            if applied_sc > Decimal("0.0000"):
                warning_message += f"Small lot surcharge of Rs.{applied_sc}/unit applied."
            else:
                warning_message += "Please increase order quantity to meet vendor MOQ."

        if is_capacity_exceeded:
            capacity_msg = f"Order quantity {qty} exceeds maximum batch capacity of {max_cap}. Order splitting or managerial authorization required."
            warning_message = f"{warning_message} | {capacity_msg}" if warning_message else capacity_msg

        return {
            "is_valid": not is_capacity_exceeded,
            "job_work_id": job_work.id,
            "job_work_code": job_work.job_work_code,
            "job_work_name": job_work.job_work_name,
            "party_id": party_id,
            "vendor_name": party_name,
            "pricing_source": source,
            "order_quantity": str(qty),
            "min_order_qty": str(min_moq),
            "max_order_qty": str(max_cap) if max_cap is not None else None,
            "is_below_moq": is_below_moq,
            "is_capacity_exceeded": is_capacity_exceeded,
            "agreed_rate": str(base_rate),
            "small_lot_surcharge": str(applied_sc),
            "effective_unit_rate": str(effective_rate),
            "estimated_total_charges": str(est_total),
            "total_lead_time_days": lead_time,
            "warning_message": warning_message
        }

    @staticmethod
    def calculate_schedule(
        company_id: int,
        job_work_id: int,
        order_date,
        quantity: Optional[Decimal] = None,
        party_id: Optional[int] = None,
        is_fast_track: bool = False
    ) -> Dict[str, Any]:
        """
        Calculates sequential or fast-track milestone schedules:
        - Procurement Dispatch Date
        - Processing Completion Date
        - Quality Sign-off Date
        - Target Delivery Date
        """
        import datetime
        from apps.process.repositories import JobWorkRepository, JobWorkPartyConfigRepository

        if isinstance(order_date, str):
            order_date = datetime.date.fromisoformat(order_date)

        job_work = JobWorkRepository.get_by_id(job_work_id, company_id)
        if not job_work:
            raise ResourceNotFound(f"Job Work Master #{job_work_id} not found.")

        party_config = None
        if party_id:
            party_config = JobWorkPartyConfigRepository.get_active_config(
                job_work_id=job_work_id,
                party_id=party_id,
                company_id=company_id,
                target_date=order_date
            )

        if party_config:
            proc_d = party_config.procurement_days
            proc_time = party_config.processing_days
            qc_d = party_config.quality_inspection_days
            trans_d = party_config.transportation_days
        else:
            proc_d = job_work.procurement_days
            proc_time = job_work.processing_days
            qc_d = job_work.quality_inspection_days
            trans_d = job_work.transportation_days

        if is_fast_track:
            # Overlap inspection with final processing stage
            qc_effective = max(0, qc_d - 1)
            total_days = proc_d + proc_time + qc_effective + trans_d
        else:
            total_days = proc_d + proc_time + qc_d + trans_d

        d_proc = order_date + datetime.timedelta(days=proc_d)
        d_complete = d_proc + datetime.timedelta(days=proc_time)
        d_qc = d_complete + datetime.timedelta(days=qc_d)
        d_delivery = order_date + datetime.timedelta(days=total_days)

        return {
            "job_work_id": job_work.id,
            "job_work_code": job_work.job_work_code,
            "party_id": party_id,
            "order_date": order_date.strftime("%Y-%m-%d"),
            "procurement_days": proc_d,
            "processing_days": proc_time,
            "quality_inspection_days": qc_d,
            "transportation_days": trans_d,
            "total_lead_time_days": total_days,
            "is_fast_track": is_fast_track,
            "schedule_milestones": {
                "procurement_dispatch_date": d_proc.strftime("%Y-%m-%d"),
                "processing_completion_date": d_complete.strftime("%Y-%m-%d"),
                "quality_signoff_date": d_qc.strftime("%Y-%m-%d"),
                "target_delivery_date": d_delivery.strftime("%Y-%m-%d")
            }
        }

    @staticmethod
    @transaction.atomic
    def seed_default_job_works(company_id: int, user_id: Optional[int] = None) -> List[JobWorkMaster]:
        """
        Seeds standard Tirupur job work masters and links them to configured vendors:
        - Knitting: Single Jersey 24GG, 1x1 Rib 24GG
        - Dyeing: Reactive Dark, Reactive Light
        - Printing: 4-Color Chest Screen Print
        - Cutting: Crew Neck Tee Lay Cutting
        - Stitching: Polo Shirt CMT Assembly
        """
        import datetime
        from apps.process.models import parent_process_stage_table
        from apps.masters.models import PartyMaster, UnitOfMeasurement
        from apps.process.repositories import JobWorkRepository, JobWorkPartyConfigRepository
        from core.constants import PartyTypes

        uom_kg = UnitOfMeasurement.objects.filter(company_id=company_id, code__iexact="KGS").first() or UnitOfMeasurement.objects.filter(company_id=company_id).first()
        uom_pcs = UnitOfMeasurement.objects.filter(company_id=company_id, code__iexact="PCS").first() or uom_kg

        stage_knit = parent_process_stage_table.objects.filter(company_id=company_id, code__icontains="KNIT").first()
        stage_dye = parent_process_stage_table.objects.filter(company_id=company_id, code__icontains="DYE").first()
        stage_prnt = parent_process_stage_table.objects.filter(company_id=company_id, code__icontains="PRNT").first() or parent_process_stage_table.objects.filter(company_id=company_id, code__icontains="PRINT").first()
        stage_cut = parent_process_stage_table.objects.filter(company_id=company_id, code__icontains="CUT").first()
        stage_stch = parent_process_stage_table.objects.filter(company_id=company_id, code__icontains="STCH").first() or parent_process_stage_table.objects.filter(company_id=company_id, code__icontains="STITCH").first()

        knitter = PartyMaster.objects.filter(company_id=company_id, party_type=PartyTypes.KNITTING_UNIT).first() or PartyMaster.objects.filter(company_id=company_id, code__icontains="KNIT").first()
        dyer = PartyMaster.objects.filter(company_id=company_id, party_type=PartyTypes.DYEING_UNIT).first() or PartyMaster.objects.filter(company_id=company_id, code__icontains="DYE").first()
        printer = PartyMaster.objects.filter(company_id=company_id, code__icontains="PRNT").first() or PartyMaster.objects.filter(company_id=company_id, name__icontains="Printer").first()
        cutter = PartyMaster.objects.filter(company_id=company_id, code__icontains="CUT").first() or PartyMaster.objects.filter(company_id=company_id, name__icontains="Cutting").first()
        stitcher = PartyMaster.objects.filter(company_id=company_id, code__icontains="STCH").first() or PartyMaster.objects.filter(company_id=company_id, name__icontains="Stitching").first()

        start_date = datetime.date(2026, 4, 1)
        end_date = datetime.date(2027, 3, 31)

        created_masters = []

        # 1. Single Jersey Knitting
        if stage_knit:
            jw_knit_sj = JobWorkRepository.get_by_code("JW-KNIT-SJ-24", company_id)
            if not jw_knit_sj:
                jw_knit_sj = JobWorkRepository.create({
                    "company_id": company_id,
                    "job_work_code": "JW-KNIT-SJ-24",
                    "job_work_name": "Single Jersey 24GG Knitting Conversion",
                    "process_stage_id": stage_knit.id,
                    "job_work_category": "KNITTING",
                    "material_type": "YARN",
                    "uom_id": uom_kg.id if uom_kg else 1,
                    "min_order_qty": Decimal("100.000"),
                    "max_order_qty": Decimal("5000.000"),
                    "standard_batch_qty": Decimal("300.000"),
                    "procurement_days": 2,
                    "processing_days": 3,
                    "quality_inspection_days": 1,
                    "transportation_days": 1,
                    "standard_delivery_days": 7,
                    "standard_rate": Decimal("18.0000"),
                    "rate_valid_from": start_date,
                    "rate_valid_to": end_date,
                    "description": "Standard circular knitting conversion for cotton single jersey fabric.",
                    "created_by": user_id,
                    "updated_by": user_id,
                })
            created_masters.append(jw_knit_sj)

            if knitter:
                cfg_knit = JobWorkPartyConfigRepository.get_active_config(jw_knit_sj.id, knitter.id, company_id)
                if not cfg_knit:
                    JobWorkPartyConfigRepository.create({
                        "company_id": company_id,
                        "job_work_id": jw_knit_sj.id,
                        "party_id": knitter.id,
                        "uom_id": uom_kg.id if uom_kg else 1,
                        "min_order_qty": Decimal("300.000"),
                        "max_order_qty": Decimal("3000.000"),
                        "daily_capacity_qty": Decimal("1000.000"),
                        "procurement_days": 2,
                        "processing_days": 3,
                        "quality_inspection_days": 1,
                        "transportation_days": 1,
                        "agreed_rate": Decimal("16.0000"),
                        "small_lot_surcharge": Decimal("2.0000"),
                        "allowed_loss_percent": Decimal("2.00"),
                        "effective_from": start_date,
                        "effective_to": end_date,
                        "created_by": user_id,
                        "updated_by": user_id,
                    })

        # 2. Reactive Dark Dyeing
        if stage_dye:
            jw_dye_dk = JobWorkRepository.get_by_code("JW-DYE-REACT-DK", company_id)
            if not jw_dye_dk:
                jw_dye_dk = JobWorkRepository.create({
                    "company_id": company_id,
                    "job_work_code": "JW-DYE-REACT-DK",
                    "job_work_name": "Reactive Soft-Flow Dyeing - Dark Shade",
                    "process_stage_id": stage_dye.id,
                    "job_work_category": "DYEING",
                    "material_type": "GREY_FABRIC",
                    "uom_id": uom_kg.id if uom_kg else 1,
                    "min_order_qty": Decimal("100.000"),
                    "max_order_qty": Decimal("2500.000"),
                    "standard_batch_qty": Decimal("250.000"),
                    "procurement_days": 2,
                    "processing_days": 4,
                    "quality_inspection_days": 1,
                    "transportation_days": 1,
                    "standard_delivery_days": 8,
                    "standard_rate": Decimal("65.0000"),
                    "rate_valid_from": start_date,
                    "rate_valid_to": end_date,
                    "description": "Soft-flow dark shade reactive dyeing and compacting.",
                    "created_by": user_id,
                    "updated_by": user_id,
                })
            created_masters.append(jw_dye_dk)

            if dyer:
                cfg_dye = JobWorkPartyConfigRepository.get_active_config(jw_dye_dk.id, dyer.id, company_id)
                if not cfg_dye:
                    JobWorkPartyConfigRepository.create({
                        "company_id": company_id,
                        "job_work_id": jw_dye_dk.id,
                        "party_id": dyer.id,
                        "uom_id": uom_kg.id if uom_kg else 1,
                        "min_order_qty": Decimal("250.000"),
                        "max_order_qty": Decimal("2000.000"),
                        "daily_capacity_qty": Decimal("800.000"),
                        "procurement_days": 2,
                        "processing_days": 4,
                        "quality_inspection_days": 1,
                        "transportation_days": 1,
                        "agreed_rate": Decimal("62.0000"),
                        "small_lot_surcharge": Decimal("5.0000"),
                        "allowed_loss_percent": Decimal("4.50"),
                        "effective_from": start_date,
                        "effective_to": end_date,
                        "created_by": user_id,
                        "updated_by": user_id,
                    })

        # 3. Chest Screen Printing
        if stage_prnt:
            jw_prnt = JobWorkRepository.get_by_code("JW-PRNT-CHEST-4C", company_id)
            if not jw_prnt:
                jw_prnt = JobWorkRepository.create({
                    "company_id": company_id,
                    "job_work_code": "JW-PRNT-CHEST-4C",
                    "job_work_name": "4-Color Chest Screen Print",
                    "process_stage_id": stage_prnt.id,
                    "job_work_category": "PRINTING",
                    "material_type": "CUT_PANEL",
                    "uom_id": uom_pcs.id if uom_pcs else 1,
                    "min_order_qty": Decimal("100.000"),
                    "max_order_qty": Decimal("10000.000"),
                    "standard_batch_qty": Decimal("1000.000"),
                    "procurement_days": 2,
                    "processing_days": 4,
                    "quality_inspection_days": 1,
                    "transportation_days": 1,
                    "standard_delivery_days": 8,
                    "standard_rate": Decimal("4.5000"),
                    "rate_valid_from": start_date,
                    "rate_valid_to": end_date,
                    "description": "Chest table/carousel screen printing with plastisol/reactive pigment.",
                    "created_by": user_id,
                    "updated_by": user_id,
                })
            created_masters.append(jw_prnt)

            if printer:
                cfg_prnt = JobWorkPartyConfigRepository.get_active_config(jw_prnt.id, printer.id, company_id)
                if not cfg_prnt:
                    JobWorkPartyConfigRepository.create({
                        "company_id": company_id,
                        "job_work_id": jw_prnt.id,
                        "party_id": printer.id,
                        "uom_id": uom_pcs.id if uom_pcs else 1,
                        "min_order_qty": Decimal("500.000"),
                        "max_order_qty": Decimal("5000.000"),
                        "daily_capacity_qty": Decimal("2500.000"),
                        "procurement_days": 2,
                        "processing_days": 3,
                        "quality_inspection_days": 1,
                        "transportation_days": 1,
                        "agreed_rate": Decimal("4.0000"),
                        "small_lot_surcharge": Decimal("0.8000"),
                        "allowed_loss_percent": Decimal("1.50"),
                        "effective_from": start_date,
                        "effective_to": end_date,
                        "created_by": user_id,
                        "updated_by": user_id,
                    })

        # 4. Lay Cutting Tee
        if stage_cut:
            jw_cut = JobWorkRepository.get_by_code("JW-CUT-TEE-01", company_id)
            if not jw_cut:
                jw_cut = JobWorkRepository.create({
                    "company_id": company_id,
                    "job_work_code": "JW-CUT-TEE-01",
                    "job_work_name": "Crew Neck Tee Lay Cutting & Bundling",
                    "process_stage_id": stage_cut.id,
                    "job_work_category": "CUTTING",
                    "material_type": "DYED_FABRIC",
                    "uom_id": uom_pcs.id if uom_pcs else 1,
                    "min_order_qty": Decimal("500.000"),
                    "max_order_qty": Decimal("20000.000"),
                    "standard_batch_qty": Decimal("2000.000"),
                    "procurement_days": 1,
                    "processing_days": 2,
                    "quality_inspection_days": 1,
                    "transportation_days": 1,
                    "standard_delivery_days": 5,
                    "standard_rate": Decimal("3.8000"),
                    "rate_valid_from": start_date,
                    "rate_valid_to": end_date,
                    "description": "Fabric spreading, relaxation, master pattern cutting and bundle ticketing.",
                    "created_by": user_id,
                    "updated_by": user_id,
                })
            created_masters.append(jw_cut)

            if cutter:
                cfg_cut = JobWorkPartyConfigRepository.get_active_config(jw_cut.id, cutter.id, company_id)
                if not cfg_cut:
                    JobWorkPartyConfigRepository.create({
                        "company_id": company_id,
                        "job_work_id": jw_cut.id,
                        "party_id": cutter.id,
                        "uom_id": uom_pcs.id if uom_pcs else 1,
                        "min_order_qty": Decimal("1000.000"),
                        "max_order_qty": Decimal("15000.000"),
                        "daily_capacity_qty": Decimal("5000.000"),
                        "procurement_days": 1,
                        "processing_days": 2,
                        "quality_inspection_days": 1,
                        "transportation_days": 1,
                        "agreed_rate": Decimal("3.5000"),
                        "small_lot_surcharge": Decimal("0.5000"),
                        "allowed_loss_percent": Decimal("2.50"),
                        "effective_from": start_date,
                        "effective_to": end_date,
                        "created_by": user_id,
                        "updated_by": user_id,
                    })

        # 5. CMT Stitching Polo
        if stage_stch:
            jw_stch = JobWorkRepository.get_by_code("JW-CMT-POLO", company_id)
            if not jw_stch:
                jw_stch = JobWorkRepository.create({
                    "company_id": company_id,
                    "job_work_code": "JW-CMT-POLO",
                    "job_work_name": "Polo Shirt Assembly CMT",
                    "process_stage_id": stage_stch.id,
                    "job_work_category": "STITCHING",
                    "material_type": "CUT_PANEL",
                    "uom_id": uom_pcs.id if uom_pcs else 1,
                    "min_order_qty": Decimal("200.000"),
                    "max_order_qty": Decimal("5000.000"),
                    "standard_batch_qty": Decimal("500.000"),
                    "procurement_days": 3,
                    "processing_days": 7,
                    "quality_inspection_days": 1,
                    "transportation_days": 1,
                    "standard_delivery_days": 12,
                    "standard_rate": Decimal("17.5000"),
                    "rate_valid_from": start_date,
                    "rate_valid_to": end_date,
                    "description": "Placket making, collar attaching, overlock assembly, sleeve setting.",
                    "created_by": user_id,
                    "updated_by": user_id,
                })
            created_masters.append(jw_stch)

            if stitcher:
                cfg_stch = JobWorkPartyConfigRepository.get_active_config(jw_stch.id, stitcher.id, company_id)
                if not cfg_stch:
                    JobWorkPartyConfigRepository.create({
                        "company_id": company_id,
                        "job_work_id": jw_stch.id,
                        "party_id": stitcher.id,
                        "uom_id": uom_pcs.id if uom_pcs else 1,
                        "min_order_qty": Decimal("500.000"),
                        "max_order_qty": Decimal("4000.000"),
                        "daily_capacity_qty": Decimal("600.000"),
                        "procurement_days": 3,
                        "processing_days": 7,
                        "quality_inspection_days": 1,
                        "transportation_days": 1,
                        "agreed_rate": Decimal("16.5000"),
                        "small_lot_surcharge": Decimal("2.5000"),
                        "allowed_loss_percent": Decimal("1.50"),
                        "effective_from": start_date,
                        "effective_to": end_date,
                        "created_by": user_id,
                        "updated_by": user_id,
                    })

        return [m for m in created_masters if m]

