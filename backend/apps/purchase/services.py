from __future__ import annotations
from decimal import Decimal
from typing import Dict, Any, List, Optional
from django.db import transaction
from django.utils import timezone
from core.base_services import BaseService
from core.exceptions import ValidationError, ResourceNotFound, ConflictError, PermissionDeniedError
from core.constants import (
    YarnCategory, YarnDefectReasons, StockMovementTypes, VoucherTypes,
    UserRoles, ModulePermissions
)
from core.formats import FormatService
from apps.authentication.models import Company, FinancialYear
from apps.masters.models import PartyMaster, YarnCountMaster, WarehouseMaster
from apps.inventory.models import parent_yarn_inward_table, yarn_stock_table
from apps.purchase.models import (
    company_yarn_type_table,
    parent_po_table,
    child_po_table,
    yarn_po_delivery_table,
    parent_yarn_po_return_table,
    child_yarn_po_return_table,
)
from apps.purchase.repositories import YarnPORepository


class YarnPOService(BaseService):
    """
    Business logic and workflow orchestration for Yarn Purchase Orders.
    Enforces authorization locks, delivery allocation constraints,
    Grey vs. Dyed yarn rules, and atomic multi-line/delivery creation.
    """

    STANDARD_YARN_TYPES = [
        {
            "yarn_type": YarnCategory.GREY,
            "display_name": "Grey Yarn (Natural / Ecru)",
            "is_active": True,
            "requires_color_shade": False,
            "requires_blend_ratio": False,
            "requires_ply_twists": False,
            "requires_slub_pattern": False,
            "requires_core_denier": False,
        },
        {
            "yarn_type": YarnCategory.DYED,
            "display_name": "Dyed Yarn (Cone / Cheese Dyed)",
            "is_active": True,
            "requires_color_shade": True,
            "requires_blend_ratio": False,
            "requires_ply_twists": False,
            "requires_slub_pattern": False,
            "requires_core_denier": False,
        },
        {
            "yarn_type": YarnCategory.MELANGE,
            "display_name": "Melange Yarn (Fiber / Top Dyed)",
            "is_active": False,
            "requires_color_shade": True,
            "requires_blend_ratio": True,
            "requires_ply_twists": False,
            "requires_slub_pattern": False,
            "requires_core_denier": False,
        },
        {
            "yarn_type": YarnCategory.BLENDED,
            "display_name": "Blended Yarn (PC, PV, Cotton-Modal)",
            "is_active": False,
            "requires_color_shade": False,
            "requires_blend_ratio": True,
            "requires_ply_twists": False,
            "requires_slub_pattern": False,
            "requires_core_denier": False,
        },
        {
            "yarn_type": YarnCategory.WOUND,
            "display_name": "Wound / Doubled & Twisted Yarn (TFO)",
            "is_active": False,
            "requires_color_shade": False,
            "requires_blend_ratio": False,
            "requires_ply_twists": True,
            "requires_slub_pattern": False,
            "requires_core_denier": False,
        },
        {
            "yarn_type": YarnCategory.SLUB,
            "display_name": "Slub / Fancy Yarn (Injected / Structured)",
            "is_active": False,
            "requires_color_shade": False,
            "requires_blend_ratio": False,
            "requires_ply_twists": False,
            "requires_slub_pattern": True,
            "requires_core_denier": False,
        },
        {
            "yarn_type": YarnCategory.CORE_SPUN,
            "display_name": "Lycra / Core-Spun Stretch Yarn",
            "is_active": False,
            "requires_color_shade": False,
            "requires_blend_ratio": False,
            "requires_ply_twists": False,
            "requires_slub_pattern": False,
            "requires_core_denier": True,
        },
        {
            "yarn_type": YarnCategory.RECYCLED,
            "display_name": "Recycled / Sustainable Yarn (GRS / GOTS)",
            "is_active": False,
            "requires_color_shade": False,
            "requires_blend_ratio": True,
            "requires_ply_twists": False,
            "requires_slub_pattern": False,
            "requires_core_denier": False,
        },
    ]

    @classmethod
    @transaction.atomic
    def seed_company_yarn_types(cls, company_id: int, user=None) -> List[company_yarn_type_table]:
        """Initialize company yarn process configurations if not present."""
        configs = []
        for defn in cls.STANDARD_YARN_TYPES:
            cfg, _ = company_yarn_type_table.objects.get_or_create(
                company_id=company_id,
                yarn_type=defn["yarn_type"],
                defaults={
                    **defn,
                    "company_id": company_id,
                    "created_by": user,
                    "updated_by": user,
                }
            )
            configs.append(cfg)
        return configs

    @classmethod
    def get_active_yarn_types(cls, company_id: int) -> List[company_yarn_type_table]:
        """Fetch active yarn process types configured for the company."""
        if not company_yarn_type_table.objects.filter(company_id=company_id).exists():
            cls.seed_company_yarn_types(company_id)
        return list(company_yarn_type_table.objects.filter(company_id=company_id, is_active=True))

    @staticmethod
    def generate_po_number(company_id: int) -> str:
        """Generate formatted PO number: YPO-YYYYMM-XXXX"""
        now = timezone.now()
        prefix = f"YPO-{now.strftime('%Y%m')}-"
        last_po = (
            parent_po_table.objects
            .filter(company_id=company_id, po_number__startswith=prefix)
            .order_by("-po_number")
            .first()
        )
        if last_po:
            try:
                seq = int(last_po.po_number.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def create_yarn_po(
        cls,
        company_id: int,
        data: Dict[str, Any],
        line_items_data: Optional[List[Dict[str, Any]]] = None,
        deliveries_data: Optional[List[Dict[str, Any]]] = None,
        user=None
    ) -> parent_po_table:
        # 1. Validate Yarn Type & Company Enablement
        yarn_type = data.get("yarn_type", YarnCategory.GREY)
        valid_yarn_types = [c[0] for c in YarnCategory.CHOICES]
        if yarn_type not in valid_yarn_types:
            raise ValidationError(f"Invalid yarn type '{yarn_type}'. Must be one of: {', '.join(valid_yarn_types)}.")

        # Ensure company yarn types are seeded
        if not company_yarn_type_table.objects.filter(company_id=company_id).exists():
            cls.seed_company_yarn_types(company_id, user)

        active_yarn_types = set(
            company_yarn_type_table.objects
            .filter(company_id=company_id, is_active=True)
            .values_list("yarn_type", flat=True)
        )
        if yarn_type not in active_yarn_types:
            raise ValidationError(
                f"Yarn process type '{yarn_type}' is not enabled for this company. "
                f"Enabled types: {', '.join(sorted(active_yarn_types))}."
            )

        # 2. Dynamic Conditional Validation per Yarn Type
        color_shade_id = data.get("color_shade_id") or data.get("color_shade")
        blend_ratio = data.get("blend_ratio")
        ply_count = int(data.get("ply_count", 1) or 1)

        if yarn_type == YarnCategory.DYED and not color_shade_id:
            raise ValidationError("Color shade is required for Dyed Yarn Purchase Orders.")

        if yarn_type == YarnCategory.MELANGE:
            if not color_shade_id:
                raise ValidationError("Color shade is required for Melange Yarn Purchase Orders.")
            if not blend_ratio:
                raise ValidationError("Melange shade ratio / fiber blend percentage (e.g. 85/15) is required for Melange Yarn.")

        if yarn_type in [YarnCategory.BLENDED, YarnCategory.RECYCLED] and not blend_ratio:
            raise ValidationError(f"Fiber blend ratio (e.g. 65/35 PC) is required for {yarn_type} Yarn Purchase Orders.")

        if yarn_type == YarnCategory.WOUND and ply_count < 1:
            raise ValidationError("Ply count must be at least 1 for Wound / Twisted Yarn.")

        # 3. Standard bag weight defaults
        per_bag = Decimal(str(data.get("per_bag", "45.360")))
        if per_bag <= 0:
            raise ValidationError("Per bag weight must be positive (typically 45.360 or 50.000 Kg/bag).")

        # 4. Generate PO Number if not provided
        po_number = data.get("po_number") or cls.generate_po_number(company_id)
        if parent_po_table.objects.filter(company_id=company_id, po_number=po_number, status=1).exists():
            raise ConflictError(f"Purchase Order #{po_number} already exists.")

        # 5. Compute quantities and values
        bag = int(data.get("bag", 0))
        rate = Decimal(str(data.get("rate", "0.00")))
        discount = Decimal(str(data.get("discount", "0.00")))
        net_rate = rate - discount
        quantity = Decimal(str(bag)) * per_bag
        amount = quantity * net_rate

        # 6. Delivery Allocation Constraint
        if deliveries_data:
            total_delivery_bags = sum(int(d.get("bag", 0)) for d in deliveries_data)
            if total_delivery_bags > bag:
                raise ValidationError(
                    f"Total scheduled delivery bags ({total_delivery_bags}) cannot exceed total PO bags ({bag})."
                )

        # 7. Create Parent PO Header
        cfyear_id = data.get("cfyear_id") or data.get("cfyear")
        if not cfyear_id:
            comp_obj = Company.objects.filter(id=company_id).first()
            cf = comp_obj.current_financial_year if comp_obj else None
            cfyear_id = cf.id if cf else (FinancialYear.objects.filter(company_id=company_id).first().id if FinancialYear.objects.filter(company_id=company_id).exists() else None)
        if not cfyear_id:
            raise ValidationError("A valid Financial Year is required for the Purchase Order.")

        po_data = {
            "po_number": po_number,
            "po_date": data.get("po_date") or timezone.now().date(),
            "yarn_type": yarn_type,
            "color_shade_id": color_shade_id if yarn_type in [YarnCategory.DYED, YarnCategory.MELANGE] else None,
            "blend_ratio": blend_ratio,
            "ply_count": ply_count,
            "twists_per_inch": data.get("twists_per_inch"),
            "slub_pattern": data.get("slub_pattern"),
            "core_denier": data.get("core_denier"),
            "name": data.get("name"),
            "company_id": company_id,
            "cfyear_id": cfyear_id,
            "party_id": data.get("party_id") or data.get("party"),
            "mill_id": data.get("mill_id") or data.get("mill"),
            "yarn_count_id": data.get("yarn_count_id") or data.get("yarn_count"),
            "bag": bag,
            "per_bag": per_bag,
            "quantity": quantity,
            "gross_quantity": data.get("gross_quantity") or quantity,
            "rate": rate,
            "discount": discount,
            "net_rate": net_rate,
            "amount": amount,
            "remarks": data.get("remarks"),
            "is_delivery": 1 if deliveries_data else data.get("is_delivery", 0),
            "is_complete": 0,
            "is_authorized": 0,
            "is_active": 1,
            "status": 1,
            "created_by": user,
            "updated_by": user,
        }
        po = parent_po_table.objects.create(**po_data)

        # 8. Create Line Items (Child PO)
        if line_items_data:
            line_objs = []
            for item in line_items_data:
                item_yarn_type = item.get("yarn_type", yarn_type)
                item_shade = item.get("color_shade_id") or item.get("color_shade")
                if item_yarn_type in [YarnCategory.DYED, YarnCategory.MELANGE] and not item_shade:
                    item_shade = color_shade_id

                item_bag = int(item.get("bag", 0))
                item_per_bag = Decimal(str(item.get("per_bag", per_bag)))
                item_qty = Decimal(str(item_bag)) * item_per_bag
                act_rate = Decimal(str(item.get("actual_rate", rate)))
                disc = Decimal(str(item.get("discount", "0.00")))
                eff_rate = act_rate - disc
                line_amt = item_qty * eff_rate

                line_objs.append(
                    child_po_table(
                        tm_po=po,
                        yarn_type=item_yarn_type,
                        yarn_count_id=item.get("yarn_count_id") or item.get("yarn_count") or po.yarn_count_id,
                        color_shade_id=item_shade,
                        blend_ratio=item.get("blend_ratio") or po.blend_ratio,
                        ply_count=int(item.get("ply_count", po.ply_count) or 1),
                        twists_per_inch=item.get("twists_per_inch") or po.twists_per_inch,
                        slub_pattern=item.get("slub_pattern") or po.slub_pattern,
                        core_denier=item.get("core_denier") or po.core_denier,
                        bag=item_bag,
                        per_bag=item_per_bag,
                        quantity=item_qty,
                        gross_wt=item.get("gross_wt") or item_qty,
                        actual_rate=act_rate,
                        discount=disc,
                        rate=eff_rate,
                        amount=line_amt,
                        remaining_bag=item_bag,
                        remaining_quantity=item_qty,
                        remaining_amount=line_amt,
                        is_active=1,
                        status=1,
                    )
                )
            child_po_table.objects.bulk_create(line_objs)
        elif po.yarn_count_id and po.bag:
            # Auto-create line item from header for single-count orders
            child_po_table.objects.create(
                tm_po=po,
                yarn_type=po.yarn_type,
                yarn_count_id=po.yarn_count_id,
                color_shade_id=po.color_shade_id,
                blend_ratio=po.blend_ratio,
                ply_count=po.ply_count,
                twists_per_inch=po.twists_per_inch,
                slub_pattern=po.slub_pattern,
                core_denier=po.core_denier,
                bag=po.bag,
                per_bag=po.per_bag,
                quantity=po.quantity,
                gross_wt=po.gross_quantity or po.quantity,
                actual_rate=po.rate,
                discount=po.discount,
                rate=po.net_rate,
                amount=po.amount,
                remaining_bag=po.bag,
                remaining_quantity=po.quantity,
                remaining_amount=po.amount,
                is_active=1,
                status=1,
            )

        # 8. Create Split Delivery Schedules
        if deliveries_data:
            delivery_objs = []
            for d in deliveries_data:
                d_bag = int(d.get("bag", 0))
                d_bag_wt = Decimal(str(d.get("bag_wt", per_bag)))
                d_qty = Decimal(str(d_bag)) * d_bag_wt

                delivery_objs.append(
                    yarn_po_delivery_table(
                        tm_po=po,
                        yarn_count_id=d.get("yarn_count_id") or d.get("yarn_count") or po.yarn_count_id,
                        party_id=d.get("party_id") or d.get("party"),
                        delivery_date=d.get("delivery_date"),
                        bag=d_bag,
                        bag_wt=d_bag_wt,
                        quantity=d_qty,
                        company_id=company_id,
                        cfyear_id=po.cfyear_id,
                        is_active=1,
                        status=1,
                    )
                )
            yarn_po_delivery_table.objects.bulk_create(delivery_objs)

        return po

    @classmethod
    @transaction.atomic
    def update_yarn_po(
        cls,
        po_id: int,
        company_id: int,
        data: Dict[str, Any],
        line_items_data: Optional[List[Dict[str, Any]]] = None,
        deliveries_data: Optional[List[Dict[str, Any]]] = None,
        user=None
    ) -> parent_po_table:
        po = YarnPORepository.get_by_id(po_id)
        if not po or po.company_id != company_id:
            raise ResourceNotFound(f"Purchase Order with ID {po_id} not found.")

        # Authorization Lock Rule
        if po.is_authorized == 1:
            raise ValidationError(
                f"Purchase Order #{po.po_number} is Authorized and locked. It must be un-authorized before editing."
            )

        # Update Yarn Type and Color Shade
        yarn_type = data.get("yarn_type", po.yarn_type)
        if yarn_type not in [YarnCategory.GREY, YarnCategory.DYED]:
            raise ValidationError("Invalid yarn type. Must be GREY or DYED.")
        po.yarn_type = yarn_type

        color_shade_id = data.get("color_shade_id") or (po.color_shade_id if yarn_type == YarnCategory.DYED else None)
        if yarn_type == YarnCategory.DYED and not color_shade_id:
            raise ValidationError("Color shade is required for Dyed Yarn Purchase Orders.")
        po.color_shade_id = color_shade_id

        # Update standard fields
        for field in ["po_date", "name", "remarks", "party_id", "mill_id", "yarn_count_id", "cfyear_id"]:
            if field in data and data[field] is not None:
                setattr(po, field, data[field])

        if "bag" in data:
            po.bag = int(data["bag"])
        if "per_bag" in data:
            po.per_bag = Decimal(str(data["per_bag"]))
        if "rate" in data:
            po.rate = Decimal(str(data["rate"]))
        if "discount" in data:
            po.discount = Decimal(str(data["discount"]))

        po.clean()
        po.updated_by = user
        po.save()

        # Update line items if provided
        if line_items_data is not None:
            child_po_table.objects.filter(tm_po=po).delete()
            line_objs = [
                child_po_table(
                    tm_po=po,
                    yarn_type=item.get("yarn_type", po.yarn_type),
                    yarn_count_id=item.get("yarn_count_id") or po.yarn_count_id,
                    color_shade_id=item.get("color_shade_id") or po.color_shade_id,
                    bag=int(item.get("bag", 0)),
                    per_bag=Decimal(str(item.get("per_bag", po.per_bag))),
                    actual_rate=Decimal(str(item.get("actual_rate", po.rate))),
                    discount=Decimal(str(item.get("discount", "0.00"))),
                    is_active=1,
                    status=1,
                )
                for item in line_items_data
            ]
            child_po_table.objects.bulk_create(line_objs)

        # Update deliveries if provided
        if deliveries_data is not None:
            total_delivery_bags = sum(int(d.get("bag", 0)) for d in deliveries_data)
            if total_delivery_bags > po.bag:
                raise ValidationError(
                    f"Total scheduled delivery bags ({total_delivery_bags}) exceeds PO bags ({po.bag})."
                )

            yarn_po_delivery_table.objects.filter(tm_po=po).delete()
            delivery_objs = [
                yarn_po_delivery_table(
                    tm_po=po,
                    yarn_count_id=d.get("yarn_count_id") or po.yarn_count_id,
                    party_id=d.get("party_id") or d.get("party"),
                    delivery_date=d.get("delivery_date"),
                    bag=int(d.get("bag", 0)),
                    bag_wt=Decimal(str(d.get("bag_wt", po.per_bag))),
                    company_id=company_id,
                    cfyear_id=po.cfyear_id,
                    is_active=1,
                    status=1,
                )
                for d in deliveries_data
            ]
            yarn_po_delivery_table.objects.bulk_create(delivery_objs)
            po.is_delivery = 1 if delivery_objs else 0
            po.save(update_fields=["is_delivery"])

        return po

    @classmethod
    @transaction.atomic
    def authorize_yarn_po(cls, po_id: int, company_id: int, user) -> parent_po_table:
        """Lock and authorize the Purchase Order."""
        po = YarnPORepository.get_by_id(po_id)
        if not po or po.company_id != company_id:
            raise ResourceNotFound(f"Purchase Order with ID {po_id} not found.")

        if po.is_authorized == 1:
            raise ValidationError(f"Purchase Order #{po.po_number} is already authorized.")

        po.is_authorized = 1
        po.authorized_by = user
        po.authorized_on = timezone.now()
        po.updated_by = user
        po.save(update_fields=["is_authorized", "authorized_by", "authorized_on", "updated_by", "updated_on"])
        return po

    @classmethod
    @transaction.atomic
    def unauthorize_yarn_po(cls, po_id: int, company_id: int, user) -> parent_po_table:
        """Unlock/Re-open the Purchase Order for edits."""
        po = YarnPORepository.get_by_id(po_id)
        if not po or po.company_id != company_id:
            raise ResourceNotFound(f"Purchase Order with ID {po_id} not found.")

        if po.is_complete == 1:
            raise ValidationError("Completed/Fulfilled purchase orders cannot be un-authorized.")

        po.is_authorized = 0
        po.authorized_by = None
        po.authorized_on = None
        po.updated_by = user
        po.save(update_fields=["is_authorized", "authorized_by", "authorized_on", "updated_by", "updated_on"])
        return po

    @classmethod
    def check_and_update_completion(cls, po_id: int, tolerance_threshold: Decimal = Decimal("10.000")) -> bool:
        """
        Auto-completion check:
        Transitions is_complete = 1 when total received inward weight >= PO Quantity - tolerance.
        """
        po = parent_po_table.objects.get(id=po_id)
        # Check total inward received weight from child line items remaining quantity
        total_remaining = sum(item.remaining_quantity for item in po.line_items.filter(status=1))
        if total_remaining <= tolerance_threshold:
            po.is_complete = 1
            po.save(update_fields=["is_complete", "updated_on"])
            return True
        return False

    @classmethod
    @transaction.atomic
    def delete_yarn_po(cls, po_id: int, company_id: int, user=None) -> parent_po_table:
        """Safely soft-delete an un-authorized PO if no inward receipts exist."""
        po = YarnPORepository.get_by_id(po_id)
        if not po or po.company_id != company_id:
            raise ResourceNotFound(f"Purchase Order with ID {po_id} not found.")

        if po.is_authorized == 1:
            raise ValidationError("Authorized purchase orders cannot be deleted. Unauthorize first.")

        if hasattr(po, 'inwards') and po.inwards.filter(status=1).exists():
            raise ValidationError("Cannot delete purchase order because Goods Receipt (Inward) entries exist against it.")

        po.soft_delete(user=user)
        return po


class YarnPoReturnService(BaseService):
    """
    Dedicated Service for Yarn PO Returns (Vendor Rejections & Debit Notes).
    Outward rejection of substandard yarn back to spinning mill / vendor.
    Atomically:
      1. Deducts physical and ledger stock from Godown (YarnStockService).
      2. Records physical stock movement (StockLedgerService).
      3. Generates balanced double-entry accounting voucher (Debit Note) reducing Mill Accounts Payable.
    """

    @classmethod
    def generate_return_number(cls, company_id: int) -> str:
        from django.utils import timezone
        prefix = f"YPR-{timezone.now().strftime('%Y%m')}-"
        last = (
            parent_yarn_po_return_table.objects
            .filter(company_id=company_id, return_number__startswith=prefix)
            .order_by("-return_number")
            .first()
        )
        if last:
            try:
                seq = int(last.return_number.split("-")[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    def generate_debit_note_number(cls, company_id: int) -> str:
        from django.utils import timezone
        prefix = f"DN-{timezone.now().strftime('%Y%m')}-"
        last = (
            parent_yarn_po_return_table.objects
            .filter(company_id=company_id, debit_note_number__startswith=prefix)
            .order_by("-debit_note_number")
            .first()
        )
        if last and last.debit_note_number:
            try:
                seq = int(last.debit_note_number.split("-")[-1]) + 1
            except ValueError:
                seq = 1
        else:
            seq = 1
        return f"{prefix}{seq:04d}"

    @classmethod
    @transaction.atomic
    def create_po_return(cls, data: Dict[str, Any], company_id: int, user=None) -> parent_yarn_po_return_table:
        """
        Creates an authorized Yarn PO Return and Debit Note enforcing 6 strict enterprise safeguards:
          1. Stock & Inventory Safeguards (Zero Negative Stock): Live balance check, atomic lot matching.
          2. Upstream Source Document Binding: Mandatory links to authorized Yarn PO & authorized Inward GRN with matching mill party and unconsumed balance check.
          3. Role-Based Access Control (RBAC): Gated to authorized personnel with can_create and can_approve privileges.
          4. Mandatory Quality Defect Codification: Strict industry defect codes and lab test findings.
          5. Multi-Tenant & Fiscal Period Constraints: Strict company isolation and active/open Financial Year lockdown.
          6. Double-Entry Accounting Immutability: Automated balanced Debit Note voucher (tl_voucher) reversing Mill AP, Purchase, and Input GST.
        """
        from django.db.models import Sum
        from apps.inventory.services import YarnStockService
        from apps.masters.models import PartyMaster, YarnCountMaster, WarehouseMaster

        # -------------------------------------------------------------
        # RESTRICTION 5: Multi-Tenant Isolation
        # -------------------------------------------------------------
        if not company_id:
            raise ValidationError("Company context is required for multi-tenant isolation.")
        company = Company.objects.filter(id=company_id, is_deleted=False).first()
        if not company:
            raise ResourceNotFound(f"Active Company #{company_id} not found.")

        # -------------------------------------------------------------
        # RESTRICTION 3: Role-Based Access Control (RBAC) & Privileges
        # -------------------------------------------------------------
        if user and getattr(user, "is_authenticated", True):
            is_superadmin = (
                getattr(user, "is_superadmin", False) or
                getattr(user, "role", "") == UserRoles.SUPER_ADMIN or
                getattr(user, "is_superuser", False)
            )
            is_admin = (
                getattr(user, "is_company_admin", False) or
                getattr(user, "role", "") == UserRoles.ADMIN_USER
            )
            if not (is_superadmin or is_admin):
                role = getattr(user, "custom_role", None)
                if not role:
                    raise PermissionDeniedError("Forbidden: User is not assigned an authorized role with purchase return privileges.")
                privilege = role.privileges.filter(
                    module=ModulePermissions.PURCHASE_YARN_PO_RETURN,
                    is_deleted=False
                ).first()
                if not privilege or not privilege.can_create:
                    raise PermissionDeniedError("Forbidden: User lacks 'purchase_return.can_create' privilege required to draft Yarn PO Returns.")
                if not privilege.can_approve:
                    raise PermissionDeniedError("Forbidden: User lacks 'purchase_return.can_approve' privilege required for outward dispatch and ledger posting.")

        # -------------------------------------------------------------
        # RESTRICTION 4: Mandatory Quality Defect Codification
        # -------------------------------------------------------------
        defect_reason = data.get("defect_reason")
        valid_defect_codes = [c[0] for c in YarnDefectReasons.CHOICES]
        if not defect_reason or defect_reason not in valid_defect_codes:
            raise ValidationError(
                f"Invalid defect code '{defect_reason}'. Return must be explicitly tagged to a standard industry defect code: "
                f"{', '.join(valid_defect_codes)}."
            )

        defect_notes = (data.get("defect_notes") or "").strip()
        if not defect_notes or len(defect_notes) < 5:
            raise ValidationError("Mandatory Defect Findings: QC inspection findings / lab test metrics (at least 5 characters) are required for defective yarn returns.")

        # -------------------------------------------------------------
        # RESTRICTION 2: Upstream Source Document Binding
        # -------------------------------------------------------------
        # Mandatory Yarn PO Link
        po_id = data.get("po_id") or data.get("po")
        if hasattr(po_id, "id"):
            po_id = po_id.id
        elif po_id is not None:
            try:
                po_id = int(po_id)
            except (ValueError, TypeError):
                pass
        if not po_id:
            raise ValidationError("Upstream Binding Required: Yarn PO Return must be referenced to an authorized Yarn Purchase Order (po_id). Standalone returns are prohibited.")

        po = parent_po_table.objects.filter(id=po_id, company_id=company_id, status=1).first()
        if not po:
            raise ValidationError(f"Purchase Order #{po_id} does not exist or does not belong to active company #{company_id}.")
        if not po.is_authorized:
            raise ValidationError(f"Purchase Order #{po.po_number} is in draft status. Only authorized POs can be referenced for returns.")

        # Mandatory Inward GRN Link
        inward_id = data.get("inward_id") or data.get("inward")
        if hasattr(inward_id, "id"):
            inward_id = inward_id.id
        elif inward_id is not None:
            try:
                inward_id = int(inward_id)
            except (ValueError, TypeError):
                pass
        if not inward_id:
            raise ValidationError("Upstream Binding Required: Yarn PO Return must be referenced to an authorized Inward GRN (inward_id). Standalone returns are prohibited.")

        inward = parent_yarn_inward_table.objects.filter(id=inward_id, company_id=company_id, status=1).first()
        if not inward:
            raise ValidationError(f"Inward GRN #{inward_id} does not exist or does not belong to active company #{company_id}.")
        if not inward.is_authorized:
            raise ValidationError(f"Inward GRN #{inward.inward_number} is in draft status. Only authorized GRNs can be referenced for returns.")

        if inward.po_id and inward.po_id != po.id:
            raise ValidationError(
                f"Source Document Discrepancy: Inward GRN #{inward.inward_number} is bound to PO #{inward.po.po_number}, "
                f"which does not match selected PO #{po.po_number}."
            )

        # Party / Mill Vendor Restriction
        party_id = data.get("party_id") or data.get("party")
        if hasattr(party_id, "id"):
            party_id = party_id.id
        elif party_id is not None:
            try:
                party_id = int(party_id)
            except (ValueError, TypeError):
                pass
        if not party_id:
            raise ValidationError("Spinning Mill / Supplier (party_id) is required.")

        if po.party_id != party_id:
            raise ValidationError(
                f"Party Mismatch: Selected spinning mill (ID {party_id}) does not match source PO mill '{po.party.name}' (ID {po.party_id})."
            )
        inward_party_id = inward.party_id or getattr(inward, "mill_id", None)
        if inward_party_id and inward_party_id != party_id:
            raise ValidationError(
                f"Party Mismatch: Selected spinning mill (ID {party_id}) does not match source Inward GRN mill (ID {inward_party_id})."
            )

        # Master Entities Resolution
        party = PartyMaster.objects.filter(id=party_id, company_id=company_id, is_deleted=False).first()
        if not party:
            raise ResourceNotFound(f"Spinning Mill #{party_id} not found in company #{company_id}.")

        warehouse_id = data.get("warehouse_id") or data.get("warehouse") or inward.warehouse_id
        if hasattr(warehouse_id, "id"):
            warehouse_id = warehouse_id.id
        elif warehouse_id is not None:
            try:
                warehouse_id = int(warehouse_id)
            except (ValueError, TypeError):
                pass
        warehouse = WarehouseMaster.objects.filter(id=warehouse_id, company_id=company_id, is_deleted=False).first()
        if not warehouse:
            raise ResourceNotFound(f"Godown #{warehouse_id} not found in company #{company_id}.")

        # Yarn Type, Count, and Lot No Match against Inward GRN
        yarn_type = data.get("yarn_type") or inward.yarn_type
        if yarn_type != inward.yarn_type:
            raise ValidationError(
                f"Yarn Type Mismatch: Return yarn type '{yarn_type}' does not match Inward GRN yarn type '{inward.yarn_type}'."
            )

        yarn_count_id = data.get("yarn_count_id") or data.get("yarn_count") or inward.yarn_count_id
        if hasattr(yarn_count_id, "id"):
            yarn_count_id = yarn_count_id.id
        elif yarn_count_id is not None:
            try:
                yarn_count_id = int(yarn_count_id)
            except (ValueError, TypeError):
                pass
        if yarn_count_id != inward.yarn_count_id:
            raise ValidationError(
                f"Yarn Count Mismatch: Return count (ID {yarn_count_id}) does not match Inward GRN count (ID {inward.yarn_count_id})."
            )
        yarn_count = YarnCountMaster.objects.filter(id=yarn_count_id, company_id=company_id, is_deleted=False).first()
        if not yarn_count:
            raise ResourceNotFound(f"Yarn Count #{yarn_count_id} not found in company #{company_id}.")

        lot_no = (data.get("lot_no") or inward.lot_no or "").strip()
        if not lot_no:
            raise ValidationError("Lot No is required for atomic lot matching.")
        if lot_no != inward.lot_no:
            raise ValidationError(
                f"Lot Mismatch: Return Lot '{lot_no}' does not match Inward GRN Lot '{inward.lot_no}'."
            )

        color_shade_id = data.get("color_shade_id") or data.get("color_shade") or inward.color_shade_id
        if hasattr(color_shade_id, "id"):
            color_shade_id = color_shade_id.id
        elif color_shade_id is not None and str(color_shade_id).strip():
            try:
                color_shade_id = int(color_shade_id)
            except (ValueError, TypeError):
                color_shade_id = None
        else:
            color_shade_id = None

        # -------------------------------------------------------------
        # Quantities and Inward GRN Unconsumed Balance Ceiling
        # -------------------------------------------------------------
        bag = int(data.get("bag", 0) or 0)
        per_bag = Decimal(str(data.get("per_bag", inward.per_bag if inward else "45.360") or "45.360"))
        quantity = Decimal(str(data.get("quantity", "0.000") or "0.000"))

        if quantity <= Decimal("0.000") and bag > 0:
            quantity = (Decimal(str(bag)) * per_bag).quantize(Decimal("0.001"))

        if quantity <= Decimal("0.000"):
            raise ValidationError("Return quantity must be greater than 0.")

        # Inward GRN unconsumed stock balance ceiling: has_available_stock = 1
        prior_returned = (
            parent_yarn_po_return_table.objects
            .filter(company_id=company_id, inward_id=inward.id, status=1)
            .aggregate(total=Sum("quantity"))["total"] or Decimal("0.000")
        )
        available_grn_qty = inward.net_wt - prior_returned
        if available_grn_qty <= Decimal("0.000"):
            raise ValidationError(
                f"Inward GRN #{inward.inward_number} has zero unconsumed stock remaining (has_available_stock = 0). "
                f"All inward stock ({inward.net_wt} Kg) has already been returned or consumed."
            )
        if quantity > available_grn_qty:
            raise ValidationError(
                f"Requested return weight ({quantity} Kg) exceeds unconsumed balance ({available_grn_qty} Kg) "
                f"of Inward GRN #{inward.inward_number} (Total: {inward.net_wt} Kg, Already Returned: {prior_returned} Kg)."
            )

        # -------------------------------------------------------------
        # RESTRICTION 1: Stock & Inventory Safeguards (Zero Negative Stock)
        # -------------------------------------------------------------
        # Live Balance Verification: Requested Return Weight <= Available Godown Stock
        # Atomic Lot Deduction: select_for_update() locks record preventing negative stock
        stock_rec = (
            yarn_stock_table.objects
            .select_for_update()
            .filter(
                company_id=company_id,
                warehouse_id=warehouse_id,
                yarn_type=yarn_type,
                yarn_count_id=yarn_count_id,
                mill_id=party_id,
                color_shade_id=color_shade_id,
                lot_no=lot_no,
            )
            .first()
        )
        if not stock_rec:
            raise ValidationError(
                f"Zero Physical Stock: No stock record found in {warehouse.name} for {yarn_type} Yarn "
                f"({yarn_count.count}, Mill: {party.name}, Lot: {lot_no}). Negative stock is prohibited."
            )
        if stock_rec.balance_quantity < quantity or (bag > 0 and stock_rec.balance_bag < bag):
            raise ValidationError(
                f"Insufficient stock in {warehouse.name} for {yarn_type} Yarn ({yarn_count.count}, Lot: {lot_no}). "
                f"Available: {stock_rec.balance_quantity} Kg ({stock_rec.balance_bag} bags), Requested Return: {quantity} Kg ({bag} bags). "
                f"Requested Return Weight <= Available Godown Stock invariant violated. Negative stock prohibited."
            )

        # Atomically deduct stock from live ledger
        YarnStockService.deduct_outward_stock(
            company_id=company_id,
            warehouse_id=warehouse_id,
            yarn_type=yarn_type,
            yarn_count_id=yarn_count_id,
            mill_id=party_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no,
            bag=bag,
            quantity=quantity,
        )

        # -------------------------------------------------------------
        # RESTRICTION 5 (Continued): Financial Year Lockdown & Dates
        # -------------------------------------------------------------
        cfyear_id = data.get("cfyear_id") or data.get("cfyear")
        if hasattr(cfyear_id, "id"):
            cfyear_id = cfyear_id.id
        elif cfyear_id is not None:
            try:
                cfyear_id = int(cfyear_id)
            except (ValueError, TypeError):
                pass

        if cfyear_id:
            fy = FinancialYear.objects.filter(id=cfyear_id, company_id=company_id, is_deleted=False).first()
        else:
            fy = company.current_financial_year
            if not fy:
                fy = FinancialYear.objects.filter(company_id=company_id, is_deleted=False).first()

        if not fy:
            raise ValidationError("Financial Year Context Required: No active financial year found for company.")

        if fy.is_closed:
            raise ValidationError(
                f"Financial Year Lockdown: Financial Year '{fy.name}' is closed. Outward movement and debit note voucher creation are blocked."
            )

        return_date = FormatService.parse_date(data.get("return_date")) or timezone.now().date()
        if not (fy.start_date <= return_date <= fy.end_date):
            raise ValidationError(
                f"Financial Year Lockdown: Return date {return_date} is outside the active Financial Year period "
                f"({fy.start_date} to {fy.end_date})."
            )

        # -------------------------------------------------------------
        # RESTRICTION 6: Double-Entry Accounting Immutability & GST
        # -------------------------------------------------------------
        rate = Decimal(str(data.get("rate") or inward.rate or "0.00"))
        if rate <= Decimal("0.00"):
            raise ValidationError("Return unit rate (₹/Kg) must be greater than 0.")

        subtotal = (quantity * rate).quantize(Decimal("0.001"))
        tax_percent = Decimal(str(data.get("tax_percent", inward.tax_percent) or "5.00"))
        tax_amount = (subtotal * (tax_percent / Decimal("100.00"))).quantize(Decimal("0.001"))
        total_debit_amount = subtotal + tax_amount

        # Automatic Intrastate (CGST 2.5% + SGST 2.5%) vs Interstate (IGST 5.0%)
        is_interstate = bool(party.state and company.state and party.state.strip().lower() != company.state.strip().lower())

        if is_interstate:
            igst_percent = tax_percent
            igst_amount = tax_amount
            cgst_percent = Decimal("0.00")
            cgst_amount = Decimal("0.000")
            sgst_percent = Decimal("0.00")
            sgst_amount = Decimal("0.000")
        else:
            igst_percent = Decimal("0.00")
            igst_amount = Decimal("0.000")
            cgst_percent = (tax_percent / Decimal("2.00")).quantize(Decimal("0.01"))
            sgst_percent = tax_percent - cgst_percent
            cgst_amount = (tax_amount / Decimal("2.00")).quantize(Decimal("0.001"))
            sgst_amount = tax_amount - cgst_amount

        return_number = data.get("return_number") or cls.generate_return_number(company_id)
        debit_note_number = data.get("debit_note_number") or cls.generate_debit_note_number(company_id)

        po_return = parent_yarn_po_return_table.objects.create(
            return_number=return_number,
            return_date=return_date,
            company_id=company_id,
            cfyear=fy,
            party_id=party_id,
            po=po,
            inward=inward,
            warehouse_id=warehouse_id,
            yarn_type=yarn_type,
            yarn_count_id=yarn_count_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no,
            defect_reason=defect_reason,
            defect_notes=defect_notes,
            bag=bag,
            per_bag=per_bag,
            quantity=quantity,
            rate=rate,
            subtotal=subtotal,
            tax_id=data.get("tax_id") or data.get("tax") or inward.tax_id,
            tax_percent=tax_percent,
            tax_amount=tax_amount,
            cgst_percent=cgst_percent,
            cgst_amount=cgst_amount,
            sgst_percent=sgst_percent,
            sgst_amount=sgst_amount,
            igst_percent=igst_percent,
            igst_amount=igst_amount,
            total_debit_amount=total_debit_amount,
            transporter_name=data.get("transporter_name", ""),
            vehicle_no=data.get("vehicle_no", ""),
            lr_number=data.get("lr_number", ""),
            debit_note_number=debit_note_number,
            is_authorized=1,
            status=1,
            created_by=user,
            updated_by=user,
        )

        # Line item creation
        child_yarn_po_return_table.objects.create(
            tm_return=po_return,
            yarn_count_id=yarn_count_id,
            color_shade_id=color_shade_id,
            lot_no=lot_no,
            bag=bag,
            per_bag=per_bag,
            quantity=quantity,
            rate=rate,
            amount=subtotal,
            status=1,
        )

        # Physical Stock Movement record
        try:
            from apps.ledger.services import StockLedgerService
            StockLedgerService.record_movement(
                company_id=company_id,
                fy_id=fy.id,
                movement_date=return_date,
                stage="YARN",
                warehouse_id=warehouse_id,
                movement_type=StockMovementTypes.SUPPLIER_RETURN,
                doc_type="PURCHASE_RETURN",
                doc_number=return_number,
                item_name=f"{yarn_count.count} {yarn_type} Yarn",
                lot_or_batch_no=lot_no,
                out_units=bag,
                out_qty=quantity,
                unit_rate=rate,
                party_id=party_id,
                remarks=f"Yarn PO Return {return_number} - {defect_reason}: {defect_notes[:100]}",
                check_balance=False,
                user=user,
            )
        except Exception:
            pass

        # Automated Double-Entry Debit Note Posting
        from apps.ledger.services import CurrencyLedgerService
        voucher = CurrencyLedgerService.post_purchase_return_debit_note_voucher(po_return, user=user)
        if not voucher:
            raise ValidationError("Failed to generate balanced Debit Note voucher.")
        po_return.voucher_id = voucher.id
        po_return.save(update_fields=["voucher_id", "updated_on"])

        return po_return

    @classmethod
    @transaction.atomic
    def cancel_po_return(cls, return_id: int, company_id: int, user=None) -> parent_yarn_po_return_table:
        """
        Atomically reverses yarn stock outward, reverses debit note voucher with contra-entries,
        and marks return cancelled. Direct modification is prohibited; only formal cancellation is allowed.
        """
        # RBAC Check
        if user and getattr(user, "is_authenticated", True):
            is_superadmin = (
                getattr(user, "is_superadmin", False) or
                getattr(user, "role", "") == UserRoles.SUPER_ADMIN or
                getattr(user, "is_superuser", False)
            )
            is_admin = (
                getattr(user, "is_company_admin", False) or
                getattr(user, "role", "") == UserRoles.ADMIN_USER
            )
            if not (is_superadmin or is_admin):
                role = getattr(user, "custom_role", None)
                if not role:
                    raise PermissionDeniedError("Forbidden: User is not authorized to cancel Yarn PO Returns.")
                privilege = role.privileges.filter(
                    module=ModulePermissions.PURCHASE_YARN_PO_RETURN,
                    is_deleted=False
                ).first()
                if not privilege or not (privilege.can_approve or privilege.can_delete):
                    raise PermissionDeniedError("Forbidden: User lacks privilege (can_approve or can_delete) to cancel Yarn PO Returns.")

        po_return = (
            parent_yarn_po_return_table.objects
            .select_for_update()
            .filter(id=return_id, company_id=company_id, status=1)
            .first()
        )
        if not po_return:
            raise ResourceNotFound(f"Active Yarn PO Return #{return_id} not found in company #{company_id}.")

        # FY Lockdown check
        if po_return.cfyear and po_return.cfyear.is_closed:
            raise ValidationError(
                f"Financial Year Lockdown: Cannot cancel return #{po_return.return_number} because FY '{po_return.cfyear.name}' is closed."
            )

        # 1. Reverse Stock
        from apps.inventory.services import YarnStockService
        YarnStockService.reverse_outward_stock(
            company_id=company_id,
            warehouse_id=po_return.warehouse_id,
            yarn_type=po_return.yarn_type,
            yarn_count_id=po_return.yarn_count_id,
            mill_id=po_return.party_id,
            color_shade_id=po_return.color_shade_id,
            lot_no=po_return.lot_no,
            bag=po_return.bag,
            quantity=po_return.quantity,
        )

        # 2. Reverse Voucher via formal compensatory contra-voucher
        if po_return.voucher_id:
            from apps.ledger.services import CurrencyLedgerService
            CurrencyLedgerService.reverse_voucher(
                voucher_id=po_return.voucher_id,
                company_id=company_id,
                reversal_date=timezone.now().date(),
                user=user,
            )

        # 3. Soft Delete
        po_return.soft_delete(user=user)
        return po_return



