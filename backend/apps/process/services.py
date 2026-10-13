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
